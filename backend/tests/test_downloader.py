from pathlib import Path

from app.downloader import YtdlpService


class FakeYDL:
    last_options = None

    def __init__(self, options):
        self.options = options
        FakeYDL.last_options = options

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, url, download=False):
        if download:
            output = Path(self.options["outtmpl"].replace("%(ext)s", "mp4"))
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"video")
            for hook in self.options["progress_hooks"]:
                hook({"status": "downloading", "downloaded_bytes": 64, "total_bytes": 128, "speed": 16, "eta": 4})
            return {"title": "Demo: Clip", "requested_downloads": [{"filepath": str(output)}]}

        return {
            "title": "Demo Clip",
            "extractor_key": "Example",
            "thumbnail": "https://example.com/thumb.jpg",
            "duration": 61,
            "formats": [
                {
                    "format_id": "18",
                    "ext": "mp4",
                    "height": 360,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                    "filesize": 1024,
                },
                {
                    "format_id": "137",
                    "ext": "mp4",
                    "height": 1080,
                    "vcodec": "avc1",
                    "acodec": "none",
                    "filesize_approx": 2048,
                },
            ],
        }


def test_analyze_hides_merge_only_formats_when_ffmpeg_missing() -> None:
    service = YtdlpService(ffmpeg_available=False, ydl_cls=FakeYDL)

    response = service.analyze("https://example.com/watch?v=1")

    assert response.title == "Demo Clip"
    assert response.warning
    assert [item.id for item in response.formats] == ["18"]


class SplitOnlyYDL(FakeYDL):
    def extract_info(self, url, download=False):
        return {
            "title": "Split Only",
            "extractor_key": "BiliBili",
            "formats": [
                {"format_id": "30280", "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2"},
                {"format_id": "30080", "ext": "mp4", "height": 1080, "vcodec": "avc1", "acodec": "none"},
            ],
        }


def test_analyze_returns_no_downloadable_formats_for_split_only_without_ffmpeg() -> None:
    service = YtdlpService(ffmpeg_available=False, ydl_cls=SplitOnlyYDL)

    response = service.analyze("https://example.com/watch?v=1")

    assert response.platform == "BiliBili"
    assert response.formats == []
    assert "ffmpeg" in response.warning


def test_download_uses_progress_hook_and_returns_safe_display_name(tmp_path: Path) -> None:
    service = YtdlpService(ffmpeg_available=True, ydl_cls=FakeYDL)
    progress_events = []

    result = service.download(
        url="https://example.com/watch?v=1",
        format_id="bestvideo+bestaudio/best",
        output_dir=tmp_path,
        job_id="job123",
        progress_hook=progress_events.append,
    )

    assert result.file_path.exists()
    assert result.display_filename == "Demo Clip.mp4"
    assert progress_events[0]["downloaded_bytes"] == 64
    assert FakeYDL.last_options["merge_output_format"] == "mp4"
