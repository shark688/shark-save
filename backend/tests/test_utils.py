from pathlib import Path

import pytest

import app.utils as utils
from app.utils import UserFacingError, ensure_within_directory, resolve_ffmpeg, sanitize_filename, validate_public_url


def test_validate_public_url_accepts_http_and_https() -> None:
    assert validate_public_url(" https://example.com/watch?v=1 ") == "https://example.com/watch?v=1"
    assert validate_public_url("http://example.com/video") == "http://example.com/video"
    assert (
        validate_public_url("【视频标题】 https://www.bilibili.com/video/BV1EW411J7YL/ 复制分享")
        == "https://www.bilibili.com/video/BV1EW411J7YL/"
    )


@pytest.mark.parametrize("url", ["", "ftp://example.com/file", "javascript:alert(1)", "example.com/video"])
def test_validate_public_url_rejects_non_public_http_urls(url: str) -> None:
    with pytest.raises(UserFacingError):
        validate_public_url(url)


def test_sanitize_filename_removes_windows_unsafe_characters() -> None:
    assert sanitize_filename('demo: clip / 01 * final?.mp4') == "demo clip 01 final .mp4"


def test_ensure_within_directory_rejects_path_traversal(tmp_path: Path) -> None:
    allowed = tmp_path / "downloads"
    allowed.mkdir()
    safe = allowed / "video.mp4"
    safe.write_text("ok", encoding="utf-8")
    assert ensure_within_directory(safe, allowed) == safe.resolve()

    outside = tmp_path / "outside.mp4"
    outside.write_text("no", encoding="utf-8")
    with pytest.raises(UserFacingError):
        ensure_within_directory(outside, allowed)


def test_resolve_ffmpeg_uses_bundled_binary_when_system_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeImageioFfmpeg:
        @staticmethod
        def get_ffmpeg_exe() -> str:
            return "C:\\bundled\\ffmpeg.exe"

    monkeypatch.setattr(utils.shutil, "which", lambda name: None)
    monkeypatch.setattr(utils, "imageio_ffmpeg", FakeImageioFfmpeg)

    result = resolve_ffmpeg()

    assert result.available is True
    assert result.location == "C:\\bundled\\ffmpeg.exe"
    assert result.source == "bundled"


def test_resolve_ffmpeg_reports_missing_when_bundled_lookup_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenImageioFfmpeg:
        @staticmethod
        def get_ffmpeg_exe() -> str:
            raise RuntimeError("missing")

    monkeypatch.setattr(utils.shutil, "which", lambda name: None)
    monkeypatch.setattr(utils, "imageio_ffmpeg", BrokenImageioFfmpeg)

    result = resolve_ffmpeg()

    assert result.available is False
    assert result.location is None
    assert result.source == "missing"
