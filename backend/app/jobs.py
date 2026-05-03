from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from .downloader import YtdlpService
from .schemas import AnalyzeResponse, JobResponse, JobState
from .utils import UserFacingError, ensure_within_directory


@dataclass
class JobRecord:
    id: str
    url: str
    format_id: str
    quality_label: str | None
    status: JobState = JobState.queued
    progress: float = 0
    downloaded_bytes: int | None = None
    total_bytes: int | None = None
    speed: float | None = None
    eta: float | None = None
    file_path: Path | None = None
    filename: str | None = None
    error: str | None = None

    def response(self) -> JobResponse:
        download_url = f"/api/jobs/{self.id}/file" if self.status == JobState.completed else None
        return JobResponse(
            id=self.id,
            status=self.status,
            progress=self.progress,
            downloaded_bytes=self.downloaded_bytes,
            total_bytes=self.total_bytes,
            speed=self.speed,
            eta=self.eta,
            filename=self.filename,
            quality_label=self.quality_label,
            error=self.error,
            download_url=download_url,
        )


class JobManager:
    def __init__(self, downloader: YtdlpService, download_root: Path, max_workers: int = 2) -> None:
        self.downloader = downloader
        self.download_root = download_root
        self.download_root.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, JobRecord] = {}
        self._lock = Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def analyze(self, url: str) -> AnalyzeResponse:
        return self.downloader.analyze(url)

    def create_job(self, url: str, format_id: str, quality_label: str | None = None) -> JobResponse:
        job = JobRecord(id=uuid4().hex, url=url, format_id=format_id, quality_label=quality_label)
        with self._lock:
            self._jobs[job.id] = job
        self._executor.submit(self._run_job, job.id)
        return job.response()

    def get_job(self, job_id: str) -> JobResponse:
        return self._get_record(job_id).response()

    def get_file(self, job_id: str) -> tuple[Path, str]:
        job = self._get_record(job_id)
        if job.status != JobState.completed or not job.file_path:
            raise UserFacingError("任务尚未完成，暂时不能下载文件。")
        safe_path = ensure_within_directory(job.file_path, self.download_root)
        if not safe_path.exists():
            raise UserFacingError("下载文件已经不存在，请重新创建任务。")
        return safe_path, job.filename or safe_path.name

    def _get_record(self, job_id: str) -> JobRecord:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise KeyError(job_id)
            return job

    def _run_job(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = JobState.downloading

        def hook(payload: dict) -> None:
            with self._lock:
                current = self._jobs[job_id]
                total = payload.get("total_bytes") or payload.get("total_bytes_estimate")
                downloaded = payload.get("downloaded_bytes")
                current.downloaded_bytes = downloaded
                current.total_bytes = total
                current.speed = payload.get("speed")
                current.eta = payload.get("eta")
                if downloaded and total:
                    current.progress = max(0, min(100, downloaded / total * 100))

        try:
            result = self.downloader.download(
                url=job.url,
                format_id=job.format_id,
                output_dir=self.download_root,
                job_id=job.id,
                progress_hook=hook,
            )
            with self._lock:
                job.file_path = result.file_path
                job.filename = result.display_filename
                job.progress = 100
                job.status = JobState.completed
        except UserFacingError as exc:
            with self._lock:
                job.error = str(exc)
                job.status = JobState.failed
        except Exception:  # noqa: BLE001 - background thread should never crash the server
            with self._lock:
                job.error = "下载任务异常中断，请稍后重试。"
                job.status = JobState.failed
