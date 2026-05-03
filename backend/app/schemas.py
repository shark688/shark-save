from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FormatOption(BaseModel):
    id: str
    label: str
    ext: Optional[str] = None
    resolution: Optional[str] = None
    filesize: Optional[int] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    fps: Optional[float] = None
    needs_ffmpeg: bool = False


class AnalyzeRequest(BaseModel):
    url: str = Field(..., min_length=1)


class AnalyzeResponse(BaseModel):
    url: str
    title: str
    platform: Optional[str] = None
    thumbnail: Optional[str] = None
    duration: Optional[float] = None
    formats: list[FormatOption]
    ffmpeg_available: bool
    warning: Optional[str] = None


class CreateJobRequest(BaseModel):
    url: str = Field(..., min_length=1)
    format_id: str = Field(..., min_length=1)
    quality_label: Optional[str] = None


class JobState(str, Enum):
    queued = "queued"
    downloading = "downloading"
    completed = "completed"
    failed = "failed"


class JobResponse(BaseModel):
    id: str
    status: JobState
    progress: float = 0
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    speed: Optional[float] = None
    eta: Optional[float] = None
    filename: Optional[str] = None
    quality_label: Optional[str] = None
    error: Optional[str] = None
    download_url: Optional[str] = None
