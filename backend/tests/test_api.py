from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas import AnalyzeResponse, FormatOption, JobResponse, JobState
from app.utils import UserFacingError


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
