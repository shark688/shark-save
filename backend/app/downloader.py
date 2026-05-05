from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from .schemas import AnalyzeResponse, FormatOption
from .utils import UserFacingError, map_download_error, sanitize_filename, validate_public_url

try:
    from yt_dlp import YoutubeDL
except ModuleNotFoundError:  # pragma: no cover - exercised when deps are missing locally
    YoutubeDL = None


ProgressHook = Callable[[dict[str, Any]], None]


@dataclass(frozen=True)
class DownloadResult:
    file_path: Path
    display_filename: str


class YtdlpService:
    def __init__(self, ffmpeg_location: str | None = None, ydl_cls: Optional[type] = None) -> None:
        self.ffmpeg_location = ffmpeg_location
        self.ffmpeg_available = bool(ffmpeg_location)
        self._ydl_cls = ydl_cls

    @property
    def ydl_cls(self) -> type:
        cls = self._ydl_cls or YoutubeDL
        if cls is None:
            raise UserFacingError("后端尚未安装 yt-dlp，请先安装依赖。")
        return cls

    def analyze(self, url: str) -> AnalyzeResponse:
        clean_url = validate_public_url(url)
        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
        }
        try:
            with self.ydl_cls(options) as ydl:
                info = ydl.extract_info(clean_url, download=False)
        except UserFacingError:
            raise
        except Exception as exc:  # noqa: BLE001 - yt-dlp raises broad extractor errors
            raise UserFacingError(map_download_error(exc)) from exc

        formats = self._build_formats(info or {})
        warning = None
        if not self.ffmpeg_available and not formats and (info or {}).get("formats"):
            warning = "当前视频只提供音视频分离流，服务端需要安装 ffmpeg 才能合并下载。"
        elif not self.ffmpeg_available:
            warning = "当前服务端未检测到 ffmpeg，已隐藏需要音视频合并的高清格式。"

        return AnalyzeResponse(
            url=clean_url,
            title=(info or {}).get("title") or "未命名视频",
            platform=(info or {}).get("extractor_key") or (info or {}).get("extractor"),
            thumbnail=(info or {}).get("thumbnail"),
            duration=(info or {}).get("duration"),
            formats=formats,
            ffmpeg_available=self.ffmpeg_available,
            warning=warning,
        )

    def download(
        self,
        url: str,
        format_id: str,
        output_dir: Path,
        job_id: str,
        progress_hook: ProgressHook,
    ) -> DownloadResult:
        clean_url = validate_public_url(url)
        output_dir.mkdir(parents=True, exist_ok=True)
        selected_format = format_id
        if not self.ffmpeg_available and selected_format == "bestvideo+bestaudio/best":
            selected_format = "best[acodec!=none][vcodec!=none]/best"

        options = {
            "format": selected_format,
            "outtmpl": str(output_dir / f"{job_id}.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "progress_hooks": [progress_hook],
            "windowsfilenames": True,
        }
        if self.ffmpeg_available:
            options["merge_output_format"] = "mp4"
            options["ffmpeg_location"] = self.ffmpeg_location

        try:
            with self.ydl_cls(options) as ydl:
                info = ydl.extract_info(clean_url, download=True)
        except UserFacingError:
            raise
        except Exception as exc:  # noqa: BLE001 - yt-dlp raises broad extractor errors
            raise UserFacingError(map_download_error(exc)) from exc

        file_path = self._resolve_downloaded_file(output_dir, job_id, info or {})
        title = sanitize_filename((info or {}).get("title") or "video")
        display_filename = f"{title}{file_path.suffix}"
        return DownloadResult(file_path=file_path, display_filename=display_filename)

    def _build_formats(self, info: dict[str, Any]) -> list[FormatOption]:
        raw_formats = info.get("formats") or []
        formats: list[FormatOption] = []
        seen: set[str] = set()

        if self.ffmpeg_available:
            formats.append(
                FormatOption(
                    id="bestvideo+bestaudio/best",
                    label="最佳质量",
                    ext="mp4",
                    resolution="auto",
                    needs_ffmpeg=True,
                )
            )
            seen.add("bestvideo+bestaudio/best")

        for item in raw_formats:
            format_id = str(item.get("format_id") or "")
            if not format_id:
                continue

            vcodec = item.get("vcodec")
            acodec = item.get("acodec")
            has_video = bool(vcodec and vcodec != "none")
            has_audio = bool(acodec and acodec != "none")
            if not has_video:
                continue

            needs_ffmpeg = not has_audio
            if needs_ffmpeg and not self.ffmpeg_available:
                continue

            download_format_id = f"{format_id}+bestaudio/best" if needs_ffmpeg else format_id
            if download_format_id in seen:
                continue

            seen.add(download_format_id)
            formats.append(
                FormatOption(
                    id=download_format_id,
                    label=self._format_label(item, needs_ffmpeg),
                    ext=item.get("ext"),
                    resolution=item.get("resolution") or self._resolution(item),
                    filesize=item.get("filesize") or item.get("filesize_approx"),
                    vcodec=vcodec,
                    acodec=acodec,
                    fps=item.get("fps"),
                    needs_ffmpeg=needs_ffmpeg,
                )
            )

        if not raw_formats:
            fallback_id = "bestvideo+bestaudio/best" if self.ffmpeg_available else "best[acodec!=none][vcodec!=none]/best"
            if fallback_id not in seen:
                formats.insert(
                    0,
                    FormatOption(
                        id=fallback_id,
                        label="最佳质量" if self.ffmpeg_available else "最佳可直接下载",
                        ext=info.get("ext") or "mp4",
                        resolution="auto",
                        needs_ffmpeg=self.ffmpeg_available,
                    ),
                )

        return formats[:12]

    def _format_label(self, item: dict[str, Any], needs_ffmpeg: bool) -> str:
        resolution = item.get("resolution") or self._resolution(item) or "视频"
        ext = (item.get("ext") or "").upper()
        fps = f" {item.get('fps')}fps" if item.get("fps") else ""
        merge = " 需合并" if needs_ffmpeg else ""
        return f"{resolution} {ext}{fps}{merge}".strip()

    @staticmethod
    def _resolution(item: dict[str, Any]) -> Optional[str]:
        height = item.get("height")
        width = item.get("width")
        if height:
            return f"{height}p"
        if width:
            return f"{width}w"
        return None

    @staticmethod
    def _resolve_downloaded_file(output_dir: Path, job_id: str, info: dict[str, Any]) -> Path:
        requested = info.get("requested_downloads") or []
        for item in requested:
            candidate = item.get("filepath") or item.get("filename")
            if candidate and Path(candidate).exists():
                return Path(candidate)

        for item in sorted(output_dir.glob(f"{job_id}.*")):
            if item.suffix not in {".part", ".ytdl"} and item.is_file():
                return item

        raise UserFacingError("下载任务已结束，但没有找到生成的视频文件。")
