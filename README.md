# FlowSave

FlowSave is a lightweight video download web app for saving publicly accessible videos to local files. It pairs a premium, mobile-first Vue interface with a small FastAPI backend that wraps [`yt-dlp`](https://github.com/yt-dlp/yt-dlp).

The MVP focuses on one reliable workflow: paste a public video link, inspect available formats, create a download job, watch progress, and download the generated file.

> FlowSave does not bypass DRM, paywalls, private content restrictions, platform permissions, or account-only access. Users are responsible for downloading only content they have the right to save.

## Highlights

- Public video URL analysis through `yt-dlp`
- Format and quality selection when the platform exposes downloadable formats
- Background download jobs with progress polling
- Safe local file delivery from a controlled download directory
- Vue 3 + Vite + Tailwind CSS frontend with a cinematic dark premium style
- FastAPI backend with no database requirement
- Clear handling for split audio/video platforms such as Bilibili when `ffmpeg` is missing
- Support for extracting the first URL from shared text, such as mobile app share messages

## Screens

The current interface is designed as a tool-first landing page:

- Large paste/input area in the first viewport
- Strong primary CTA for analysis
- Format picker and job progress card
- Pro feature previews for batch downloads, subtitles, AI summaries, and paid queues
- Mobile-friendly controls with accessible alerts and status messages

## Tech Stack

| Layer | Stack |
| --- | --- |
| Frontend | Vue 3, Vite, Tailwind CSS, lucide-vue-next |
| Backend | FastAPI, yt-dlp |
| Jobs | In-memory background worker |
| Storage | Local files under `storage/downloads` |
| Database | None for MVP |

## Project Structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- main.py          # FastAPI app and API routes
|   |   |-- downloader.py    # yt-dlp wrapper
|   |   |-- jobs.py          # in-memory job manager
|   |   |-- schemas.py       # API models
|   |   `-- utils.py         # URL, filename, ffmpeg helpers
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

## Requirements

- Python 3.10+
- Node.js 20+
- `ffmpeg` recommended

`ffmpeg` is important for platforms that return separate video-only and audio-only streams. Bilibili commonly behaves this way. Without `ffmpeg`, FlowSave will still analyze the video but will hide formats that require merging.

## Quick Start

### 1. Run the backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --reload --app-dir backend --host 127.0.0.1 --port 8000
```

Backend: `http://127.0.0.1:8000`

### 2. Run the frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend: `http://127.0.0.1:5173`

The Vite dev server proxies `/api` requests to `http://127.0.0.1:8000`.

## API

### `GET /api/health`

Returns service status and whether `ffmpeg` is available.

### `POST /api/analyze`

Analyze a public video URL.

```json
{
  "url": "https://www.bilibili.com/video/BV1EW411J7YL/"
}
```

The backend also accepts shared text that contains a URL and extracts the first HTTP/HTTPS link.

### `POST /api/jobs`

Create a download job.

```json
{
  "url": "https://example.com/video.mp4",
  "format_id": "best",
  "quality_label": "Best"
}
```

### `GET /api/jobs/{job_id}`

Return job status, progress, speed, error details, and a download URL when complete.

### `GET /api/jobs/{job_id}/file`

Download the generated file for a completed job.

## Testing

Run backend tests:

```powershell
python -m pytest
```

Build the frontend:

```powershell
cd frontend
npm run build
```

Current coverage includes:

- URL validation and shared-text URL extraction
- Safe filename/path handling
- yt-dlp wrapper behavior with mocked extractors
- split audio/video handling when `ffmpeg` is unavailable
- API success and error responses
- job lifecycle and file download behavior

## Known MVP Limits

- Jobs are stored in memory and disappear after server restart.
- Downloaded files are stored locally and are not automatically expired yet.
- No user accounts, database, billing, or quota system.
- No cookie import or login-required video support.
- No DRM, paywall, or permission bypass.
- Some sites change extractor behavior frequently; `yt-dlp` should be kept up to date.

## Roadmap

- Batch download queue
- Optional `ffmpeg` installation guide and server capability checks
- Subtitle extraction and translation
- AI video summary from subtitles or transcripts
- User accounts, paid plans, and quota controls
- Download file cleanup policy
- Persistent job storage
- Docker deployment

## Responsible Use

FlowSave is a wrapper around `yt-dlp` for legitimate personal workflows such as saving public videos that the user has the right to download. Respect copyright, platform terms, creator permissions, and local law.
