# SliceSound — YouTube Audio Clip Cutter

A tiny, responsive front end for selecting a time range from a YouTube video, previewing it, and exporting the selected segment through an optional Python API.

## Features

- Lightweight, dependency-free front end (plain HTML/CSS/JavaScript)
- YouTube URL validation for watch, Shorts, embed, live, and youtu.be links
- Timestamp inputs in `SS`, `MM:SS`, or `HH:MM:SS` format
- Preview controls, quick clip lengths, and MP3/M4A/WAV export choices
- Mobile-friendly layout and low initial download size

## Important architecture note

GitHub Pages hosts the static interface only. The export feature requires the optional API service in `api.py`, Python dependencies, and FFmpeg on a server. The website deliberately does not claim to export audio until that API is configured.

Only process videos you own or have permission to download, and comply with YouTube's terms and applicable copyright law. Some videos may be unavailable to the processor due to access restrictions or platform changes.

## Run locally

1. Install Python 3.10+ and FFmpeg.
2. Install dependencies: `pip install -r requirements.txt`
3. Start the API: `python api.py`
4. Serve the static page locally (for example, `python -m http.server 8000` from this folder).
5. Open `http://localhost:8000/?api=http://localhost:8080`.

For local development, configure CORS with `ALLOWED_ORIGINS=http://localhost:8000`.

## Deploy

- Publish `index.html` using GitHub Pages (the page is under `/audio-slice/` in this repository).
- Deploy `api.py` on a Python host that permits FFmpeg and outbound requests. Set the start command to `gunicorn --bind 0.0.0.0:$PORT api:app` and install FFmpeg in the service image.
- Set `ALLOWED_ORIGINS` to the exact website origin(s), comma-separated. Example: `https://rocccyborg.github.io`.
- Open the page with the API base URL: `https://rocccyborg.github.io/embed-xplore/audio-slice/?api=https://YOUR-API-HOST`.

For production, also add request rate limiting, a reverse-proxy request-size limit, authentication or abuse controls, and monitoring. Do not expose the API to untrusted traffic without appropriate controls.
