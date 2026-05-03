<div align="center">

# SharkSave

**一个精致、移动端优先、基于 `yt-dlp` 的公开视频保存工具。**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue%203-Frontend-42B883?style=for-the-badge&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-Downloader-FF0066?style=for-the-badge)](https://github.com/yt-dlp/yt-dlp)

[English](README.md) | [简体中文](README.zh-CN.md)

[功能亮点](#功能亮点) | [快速开始](#快速开始) | [接口说明](#接口说明) | [路线图](#路线图) | [负责任使用](#负责任使用)

</div>

---

SharkSave 是一个轻量级视频下载 Web 应用，用于把**公开视频链接**解析并保存为本地文件。项目使用 Vue 3 构建具有付费产品质感的前端界面，后端使用 FastAPI 封装 [`yt-dlp`](https://github.com/yt-dlp/yt-dlp)。

当前 MVP 专注一个稳定闭环：

```text
粘贴公开视频链接 -> 解析视频信息 -> 选择格式 -> 创建下载任务 -> 查看进度 -> 下载文件
```

> SharkSave 不绕过 DRM、付费墙、私有内容限制、平台权限或账号登录限制。请只下载你有权保存的内容，并遵守版权、平台规则和当地法律。

## 功能亮点

- 通过 `yt-dlp` 解析公开视频链接
- 支持从 App 分享文案中自动提取第一个链接
- 展示视频标题、平台、时长、缩略图和可用格式
- 后台下载任务与进度轮询
- 通过安全的后端文件接口下载完成文件
- 自动检测 `ffmpeg`，并清晰提示音视频分离流的限制
- 首屏即工具，移动端优先，视觉风格偏高级暗色产品
- 表单错误、状态提示具备基础可访问性
- MVP 阶段无需数据库

## 产品预览

SharkSave 不是一个普通表单页面，而是一个更像产品的下载工作台：

- 首屏大输入框，适合手机和桌面快速粘贴链接
- 明确的“立即解析”主按钮
- 格式选择器和任务进度卡片
- 清晰的版权与权限边界提示
- 为批量下载、字幕翻译、AI 总结和付费队列预留产品入口

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3, Vite, Tailwind CSS, lucide-vue-next |
| 后端 | FastAPI, yt-dlp |
| 任务 | 内存后台任务管理 |
| 存储 | 本地 `storage/downloads` 目录 |
| 数据库 | MVP 阶段不需要 |

## 项目结构

```text
.
|-- backend/
|   |-- app/
|   |   |-- main.py          # FastAPI 应用和 API 路由
|   |   |-- downloader.py    # yt-dlp 封装
|   |   |-- jobs.py          # 内存任务管理
|   |   |-- schemas.py       # API 数据模型
|   |   `-- utils.py         # URL、文件名、ffmpeg 辅助函数
|   |-- tests/
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- App.vue
|   |   |-- api.js
|   |   `-- style.css
|   |-- vite.config.js
|   `-- package.json
|-- pytest.ini
`-- README.md
```

## 环境要求

- Python 3.10+
- Node.js 20+
- 推荐安装 `ffmpeg`

`ffmpeg` 对 B 站等平台尤其重要。这类平台经常返回“视频流”和“音频流”分离的格式。如果没有 `ffmpeg`，SharkSave 仍然可以解析视频信息，但会隐藏需要合并的格式，并提示用户安装 `ffmpeg`。

## 快速开始

### 1. 克隆仓库

```powershell
git clone https://github.com/shark688/shark-save.git
cd shark-save
```

### 2. 启动后端

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --reload --app-dir backend --host 127.0.0.1 --port 8000
```

后端地址：`http://127.0.0.1:8000`

### 3. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

前端地址：`http://127.0.0.1:5173`

Vite 开发服务器会把 `/api` 请求代理到 `http://127.0.0.1:8000`。

## 接口说明

### `GET /api/health`

返回服务状态，以及当前服务端是否检测到 `ffmpeg`。

```json
{
  "ok": true,
  "ffmpeg_available": false
}
```

### `POST /api/analyze`

解析公开视频链接。

```json
{
  "url": "https://www.bilibili.com/video/BV1EW411J7YL/"
}
```

后端也支持传入带有链接的分享文案，会自动提取其中第一个 HTTP/HTTPS 链接。

### `POST /api/jobs`

创建下载任务。

```json
{
  "url": "https://example.com/video.mp4",
  "format_id": "best",
  "quality_label": "Best"
}
```

### `GET /api/jobs/{job_id}`

查询任务状态、下载进度、速度、错误信息，以及完成后的文件下载地址。

### `GET /api/jobs/{job_id}/file`

下载已完成任务生成的本地文件。

## 测试

运行后端测试：

```powershell
python -m pytest
```

构建前端：

```powershell
cd frontend
npm run build
```

当前测试覆盖：

- URL 校验和分享文案链接提取
- 安全文件名和路径处理
- 使用 mock 验证 `yt-dlp` 封装行为
- 未安装 `ffmpeg` 时的音视频分离格式处理
- API 成功和失败响应
- 任务生命周期和文件下载行为

## MVP 已知限制

- 任务保存在内存中，服务重启后会丢失。
- 下载文件保存在本地，目前还没有自动过期清理。
- 暂无用户系统、数据库、支付、套餐和配额。
- 暂不支持 Cookie 导入或需要登录的视频。
- 不支持 DRM、付费墙或权限绕过。
- 各平台规则经常变化，需要持续更新 `yt-dlp`。

## 路线图

- 批量下载队列
- `ffmpeg` 安装指南和服务端能力检测
- 字幕提取与翻译
- 基于字幕或转写的视频 AI 总结
- 用户系统、付费套餐和额度控制
- 下载文件自动清理策略
- 持久化任务存储
- Docker 部署

## 负责任使用

SharkSave 是一个面向合法个人使用场景的 `yt-dlp` Web 封装，例如保存你有权下载的公开视频。请尊重版权、创作者授权、平台条款和当地法律。

## License

当前暂未选择许可证。在接受外部贡献或分发正式版本前，建议先补充合适的开源许可证。
