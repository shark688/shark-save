from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .downloader import YtdlpService
from .jobs import JobManager
from .schemas import AnalyzeRequest, AnalyzeResponse, CreateJobRequest, JobResponse
from .utils import UserFacingError, resolve_ffmpeg


def create_app(job_manager: JobManager | None = None) -> FastAPI:
    app = FastAPI(title="SharkSave", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    root = Path(__file__).resolve().parents[2]
    ffmpeg_info = resolve_ffmpeg()
    manager = job_manager or JobManager(
        downloader=YtdlpService(ffmpeg_location=ffmpeg_info.location),
        download_root=root / "storage" / "downloads",
    )
    app.state.job_manager = manager

    @app.get("/api/health")
    def health() -> dict[str, bool | str]:
        current_ffmpeg = resolve_ffmpeg()
        return {"ok": True, "ffmpeg_available": current_ffmpeg.available, "ffmpeg_source": current_ffmpeg.source}

    @app.post("/api/analyze", response_model=AnalyzeResponse)
    def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
        try:
            return app.state.job_manager.analyze(payload.url)
        except UserFacingError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/jobs", response_model=JobResponse, status_code=202)
    def create_job(payload: CreateJobRequest) -> JobResponse:
        try:
            return app.state.job_manager.create_job(payload.url, payload.format_id, payload.quality_label)
        except UserFacingError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/jobs/{job_id}", response_model=JobResponse)
    def get_job(job_id: str) -> JobResponse:
        try:
            return app.state.job_manager.get_job(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="任务不存在。") from exc

    @app.get("/api/jobs/{job_id}/file")
    def get_file(job_id: str) -> FileResponse:
        try:
            file_path, filename = app.state.job_manager.get_file(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="任务不存在。") from exc
        except UserFacingError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return FileResponse(file_path, filename=filename, media_type="application/octet-stream")

    return app


app = create_app()
