from pathlib import Path

from fastapi.testclient import TestClient

import app.main as main
from app.downloader import YtdlpService
from app.jobs import JobManager
from app.main import create_app
from app.schemas import AnalyzeResponse, FormatOption, JobResponse, JobState
from app.utils import FfmpegInfo, UserFacingError


class FakeJobManager:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def analyze(self, url: str) -> AnalyzeResponse:
        if url == "https://example.com/error":
            raise UserFacingError("解析失败。")
        return AnalyzeResponse(
            url=url,
            title="Demo Clip",
            platform="Example",
            thumbnail=None,
            duration=10,
            formats=[FormatOption(id="best", label="最佳质量", ext="mp4")],
            ffmpeg_available=True,
        )

    def create_job(self, url: str, format_id: str, quality_label: str | None = None) -> JobResponse:
        return JobResponse(
            id="job123",
            status=JobState.queued,
            quality_label=quality_label,
        )

    def get_job(self, job_id: str) -> JobResponse:
        if job_id != "job123":
            raise KeyError(job_id)
        return JobResponse(
            id="job123",
            status=JobState.completed,
            progress=100,
            filename="Demo Clip.mp4",
            download_url="/api/jobs/job123/file",
        )

    def get_file(self, job_id: str):
        if job_id != "job123":
            raise KeyError(job_id)
        return self.file_path, "Demo Clip.mp4"


class SplitOnlyYDL:
    def __init__(self, options):
        self.options = options

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, url, download=False):
        return {
            "title": "Split Only",
            "extractor_key": "BiliBili",
            "formats": [
                {"format_id": "30280", "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2"},
                {"format_id": "30080", "ext": "mp4", "height": 1080, "vcodec": "avc1", "acodec": "none"},
            ],
        }


def make_client(tmp_path: Path) -> TestClient:
    file_path = tmp_path / "job123.mp4"
    file_path.write_bytes(b"video")
    return TestClient(create_app(FakeJobManager(file_path)))


def test_analyze_success(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post("/api/analyze", json={"url": "https://example.com/video"})

    assert response.status_code == 200
    assert response.json()["title"] == "Demo Clip"
    assert response.json()["formats"][0]["id"] == "best"


def test_health_reports_ffmpeg_source(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(main, "resolve_ffmpeg", lambda: FfmpegInfo(location="C:\\bundled\\ffmpeg.exe", source="bundled"))
    client = make_client(tmp_path)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["ffmpeg_available"] is True
    assert response.json()["ffmpeg_source"] == "bundled"


def test_analyze_returns_split_only_formats_when_ffmpeg_available(tmp_path: Path) -> None:
    manager = JobManager(
        downloader=YtdlpService(ffmpeg_location="C:\\bundled\\ffmpeg.exe", ydl_cls=SplitOnlyYDL),
        download_root=tmp_path,
    )
    client = TestClient(create_app(manager))

    response = client.post("/api/analyze", json={"url": "https://example.com/video"})

    assert response.status_code == 200
    body = response.json()
    assert body["ffmpeg_available"] is True
    assert body["formats"][0]["id"] == "bestvideo+bestaudio/best"
    assert body["formats"][1]["id"] == "30080+bestaudio/best"


def test_analyze_returns_user_facing_error(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post("/api/analyze", json={"url": "https://example.com/error"})

    assert response.status_code == 400
    assert response.json()["detail"] == "解析失败。"


def test_job_lifecycle_and_file_download(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    created = client.post(
        "/api/jobs",
        json={"url": "https://example.com/video", "format_id": "best", "quality_label": "最佳质量"},
    )
    assert created.status_code == 202
    assert created.json()["id"] == "job123"

    status = client.get("/api/jobs/job123")
    assert status.status_code == 200
    assert status.json()["download_url"] == "/api/jobs/job123/file"

    file_response = client.get("/api/jobs/job123/file")
    assert file_response.status_code == 200
    assert file_response.content == b"video"


def test_missing_job_returns_404(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/api/jobs/missing")

    assert response.status_code == 404
