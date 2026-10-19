"""Optional SliceSound API. Deploy on a trusted host with FFmpeg installed."""
import os, re, shutil, subprocess, tempfile, zipfile
from pathlib import Path
from urllib.parse import urlparse
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.getenv("ALLOWED_ORIGINS", "*").split(",")}})
MAX_CLIP_SECONDS = int(os.getenv("MAX_CLIP_SECONDS", "3600"))
MAX_DOWNLOAD_BYTES = int(os.getenv("MAX_DOWNLOAD_BYTES", str(150 * 1024 * 1024)))
ALLOWED_FORMATS = {"mp3", "m4a", "wav"}

def valid_youtube_url(raw):
    try:
        u = urlparse(raw)
        host = (u.hostname or "").lower()
        allowed = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be", "www.youtu.be"}
        if u.scheme not in ("http", "https") or host not in allowed:
            return False
        if host.endswith("youtu.be"):
            return bool(re.fullmatch(r"/[\w-]{11}/?", u.path))
        if u.path == "/watch":
            return bool(re.fullmatch(r"[\w-]{11}", (dict(__import__("urllib.parse", fromlist=["parse_qsl"]).parse_qsl(u.query)).get("v") or "")))
        return bool(re.fullmatch(r"/(shorts|embed|live)/[\w-]{11}/?", u.path))
    except Exception:
        return False

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "SliceSound API"})

@app.post("/api/clip")
def clip():
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", ""))
    fmt = str(data.get("format", "mp3")).lower()
    try:
        start, end = float(data["start"]), float(data["end"])
    except (KeyError, TypeError, ValueError):
        return jsonify(error="Start and end timestamps are required."), 400
    if not valid_youtube_url(url):
        return jsonify(error="Only valid YouTube video URLs are accepted."), 400
    if fmt not in ALLOWED_FORMATS:
        return jsonify(error="Unsupported format. Choose MP3, M4A, or WAV."), 400
    if start < 0 or end <= start or end - start > MAX_CLIP_SECONDS:
        return jsonify(error=f"Choose a valid range up to {MAX_CLIP_SECONDS} seconds."), 400
    if not shutil.which("ffmpeg"):
        return jsonify(error="FFmpeg is not installed on the API host."), 503

    temp = tempfile.TemporaryDirectory(prefix="slicesound-")
    root = Path(temp.name)
    source = root / "source.%(ext)s"
    try:
        opts = {
            "format": "bestaudio/best",
            "outtmpl": str(source),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "max_filesize": MAX_DOWNLOAD_BYTES,
            "socket_timeout": 20,
            "retries": 1,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info.get("duration") and end > float(info["duration"]):
                return jsonify(error="End time exceeds the video's duration."), 400
        candidates = list(root.glob("source.*"))
        if not candidates:
            return jsonify(error="Could not retrieve an audio stream for this video."), 502
        inp = candidates[0]
        out = root / f"clip.{fmt}"
        codec = {"mp3": ["-codec:a", "libmp3lame", "-q:a", "3"], "m4a": ["-codec:a", "aac", "-b:a", "192k"], "wav": ["-codec:a", "pcm_s16le"]}[fmt]
        command = ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(start), "-i", str(inp), "-t", str(end-start), *codec, "-y", str(out)]
        result = subprocess.run(command, capture_output=True, timeout=180)
        if result.returncode or not out.exists():
            return jsonify(error="Audio conversion failed. Try another range or video."), 502
        response = send_file(out, as_attachment=True, download_name=f"slicesound-clip.{fmt}", mimetype={"mp3":"audio/mpeg","m4a":"audio/mp4","wav":"audio/wav"}[fmt])
        response.call_on_close(temp.cleanup)
        return response
    except Exception:
        temp.cleanup()
        app.logger.exception("Audio clip processing failed")
        return jsonify(error="Unable to process this video. It may be unavailable, restricted, or unsupported."), 502


@app.post("/api/batch")
def batch():
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", ""))
    fmt = str(data.get("format", "mp3")).lower()
    ranges = data.get("ranges")
    if not valid_youtube_url(url):
        return jsonify(error="Only valid YouTube video URLs are accepted."), 400
    if fmt not in ALLOWED_FORMATS:
        return jsonify(error="Unsupported format. Choose MP3, M4A, or WAV."), 400
    if not isinstance(ranges, list) or not 1 <= len(ranges) <= 10:
        return jsonify(error="Provide between 1 and 10 clip ranges."), 400
    checked = []
    for item in ranges:
        try:
            start, end = float(item["start"]), float(item["end"])
        except (KeyError, TypeError, ValueError):
            return jsonify(error="Each range requires numeric start and end values."), 400
        if start < 0 or end <= start or end - start > MAX_CLIP_SECONDS:
            return jsonify(error=f"Each range must be valid and no longer than {MAX_CLIP_SECONDS} seconds."), 400
        checked.append((start, end))
    if not shutil.which("ffmpeg"):
        return jsonify(error="FFmpeg is not installed on the API host."), 503
    temp = tempfile.TemporaryDirectory(prefix="slicesound-batch-")
    root = Path(temp.name)
    try:
        opts = {"format": "bestaudio/best", "outtmpl": str(root / "source.%(ext)s"),
                "noplaylist": True, "quiet": True, "no_warnings": True,
                "max_filesize": MAX_DOWNLOAD_BYTES, "socket_timeout": 20, "retries": 1}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            duration = float(info.get("duration") or 0)
        if duration and any(end > duration for _, end in checked):
            return jsonify(error="At least one end time exceeds the video's duration."), 400
        candidates = list(root.glob("source.*"))
        if not candidates:
            return jsonify(error="Could not retrieve an audio stream for this video."), 502
        inp = candidates[0]
        codec = {"mp3": ["-codec:a", "libmp3lame", "-q:a", "3"],
                 "m4a": ["-codec:a", "aac", "-b:a", "192k"],
                 "wav": ["-codec:a", "pcm_s16le"]}[fmt]
        clips = []
        for index, (start, end) in enumerate(checked, 1):
            out = root / f"clip-{index:02d}.{fmt}"
            command = ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(start), "-i", str(inp),
                       "-t", str(end-start), *codec, "-y", str(out)]
            result = subprocess.run(command, capture_output=True, timeout=180)
            if result.returncode or not out.exists():
                return jsonify(error=f"Conversion failed for clip {index}."), 502
            clips.append(out)
        archive = root / "slicesound-batch.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for clip in clips:
                zf.write(clip, arcname=clip.name)
        response = send_file(archive, as_attachment=True, download_name="slicesound-batch.zip", mimetype="application/zip")
        response.call_on_close(temp.cleanup)
        return response
    except Exception:
        temp.cleanup()
        app.logger.exception("Batch audio clip processing failed")
        return jsonify(error="Unable to process this video. It may be unavailable, restricted, or unsupported."), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
