from pathlib import Path

import pytest

from app.utils import UserFacingError, ensure_within_directory, sanitize_filename, validate_public_url


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
