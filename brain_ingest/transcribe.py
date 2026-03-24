"""Local transcription using faster-whisper. No data leaves your machine."""

import os
import tempfile
from pathlib import Path


def transcribe_file(audio_path: str, model_size: str = "base") -> str:
    """Transcribe a local audio/video file and return the full transcript text."""
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="auto", compute_type="auto")
    segments, _ = model.transcribe(audio_path, beam_size=5)
    return " ".join(seg.text.strip() for seg in segments)


def download_youtube(url: str) -> tuple[str, str]:
    """Download YouTube audio to a temp file. Returns (temp_path, video_title)."""
    import yt_dlp

    tmp_dir = tempfile.mkdtemp()
    output_template = os.path.join(tmp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }],
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "untitled")

    # Find the downloaded file
    for f in Path(tmp_dir).iterdir():
        if f.suffix == ".mp3":
            return str(f), title

    raise RuntimeError(f"Download failed — no audio file found in {tmp_dir}")
