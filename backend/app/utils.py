from __future__ import annotations

import re
import shutil
from pathlib import Path
from urllib.parse import urlparse


class UserFacingError(Exception):
    """An expected error that can be shown directly to the user."""


def validate_public_url(url: str) -> str:
    cleaned = extract_first_url(url)
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise UserFacingError("请输入有效的 HTTP 或 HTTPS 视频链接。")
    return cleaned


def extract_first_url(value: str) -> str:
    cleaned = (value or "").strip()
    match = re.search(r"https?://[^\s<>'\"]+", cleaned)
    if match:
        cleaned = match.group(0)
    return cleaned.rstrip("。，,；;）)]】")


def sanitize_filename(name: str, fallback: str = "video") -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1F]', " ", name or "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.rstrip(". ")
    if not cleaned:
        cleaned = fallback
    return cleaned[:120]


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def ensure_within_directory(path: Path, parent: Path) -> Path:
    resolved_path = path.resolve()
    resolved_parent = parent.resolve()
    if resolved_parent not in [resolved_path, *resolved_path.parents]:
        raise UserFacingError("文件路径不安全，已拒绝访问。")
    return resolved_path


def map_download_error(error: Exception) -> str:
    message = str(error)
    lowered = message.lower()
    if "unsupported url" in lowered:
        return "这个站点或链接暂时不受支持。"
    if "private" in lowered or "login" in lowered or "sign in" in lowered or "cookies" in lowered:
        return "这个视频可能需要登录或权限，当前 MVP 只支持公开链接。"
    if "requested format is not available" in lowered or "no video formats" in lowered:
        return "所选清晰度暂不可用，请换一个格式重试。"
    if "ffmpeg" in lowered:
        return "服务端缺少 ffmpeg，部分高清合并格式无法下载。"
    if "http error 403" in lowered or "forbidden" in lowered:
        return "平台拒绝了这次下载请求，可能需要权限或稍后重试。"
    if "timed out" in lowered or "timeout" in lowered:
        return "请求超时，请检查链接或稍后重试。"
    return "下载失败，站点规则可能发生变化，请稍后重试或换一个公开链接。"
