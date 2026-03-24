"""brain-ingest CLI — ingest YouTube, audio/video, or transcripts into the brain vault."""

import os
import sys
import tempfile
import click
from pathlib import Path

VAULT_PATH = str(Path(__file__).parent.parent)
YOUTUBE_PREFIXES = ("https://youtube.com", "https://www.youtube.com", "https://youtu.be")


def _is_youtube(source: str) -> bool:
    return any(source.startswith(p) for p in YOUTUBE_PREFIXES)


def _is_audio_video(path: str) -> bool:
    return Path(path).suffix.lower() in {
        ".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".flac", ".webm", ".mkv", ".mov"
    }


@click.command()
@click.argument("source")
@click.option("--apply", is_flag=True, help="Write the note to the vault inbox (dry-run by default)")
@click.option("--title", default="", help="Override the note title")
@click.option("--transcript", is_flag=True, help="Treat SOURCE as a plain text transcript file")
@click.option("--model", default="base", show_default=True,
              help="Whisper model size: tiny, base, small, medium, large")
@click.option("--vault", default=VAULT_PATH, show_default=True, help="Path to the brain vault")
def main(source, apply, title, transcript, model, vault):
    """
    Ingest a source into the brain vault.

    SOURCE can be:

    \b
      - A YouTube URL
      - A local audio/video file path
      - A plain text transcript file (use --transcript flag)

    Examples:

    \b
      brain-ingest "https://youtube.com/watch?v=..." --apply
      brain-ingest /path/to/recording.mp4 --apply
      brain-ingest /path/to/notes.txt --transcript --title "Team Retro" --apply
    """
    from brain_ingest.extract import extract_knowledge
    from brain_ingest.note import build_note, write_note

    # ── Step 1: Get transcript ──────────────────────────────────────────────
    if transcript:
        click.echo(f"Reading transcript from: {source}")
        raw_transcript = Path(source).read_text(encoding="utf-8")
        note_title = title or Path(source).stem
        source_type = "transcript"

    elif _is_youtube(source):
        click.echo(f"Downloading YouTube audio: {source}")
        from brain_ingest.transcribe import download_youtube, transcribe_file
        tmp_path, yt_title = download_youtube(source)
        note_title = title or yt_title
        click.echo(f"Transcribing with Whisper ({model})...")
        raw_transcript = transcribe_file(tmp_path, model_size=model)
        source_type = "youtube"

    elif _is_audio_video(source):
        click.echo(f"Transcribing audio/video: {source}")
        from brain_ingest.transcribe import transcribe_file
        note_title = title or Path(source).stem
        raw_transcript = transcribe_file(source, model_size=model)
        source_type = "audio"

    else:
        click.echo(f"Error: unrecognised source '{source}'. "
                   "Pass a YouTube URL, audio/video file, or use --transcript.", err=True)
        sys.exit(1)

    click.echo(f"Transcript length: {len(raw_transcript.split())} words")

    # ── Step 2: Extract knowledge ───────────────────────────────────────────
    click.echo("Extracting structured knowledge with Claude...")
    extraction = extract_knowledge(raw_transcript, title=note_title)

    # ── Step 3: Build note ──────────────────────────────────────────────────
    filename, content = build_note(extraction, source=source, source_type=source_type)

    # ── Step 4: Write or preview ────────────────────────────────────────────
    if apply:
        out_path = write_note(filename, content, vault)
        click.echo(f"\nNote written to: {out_path}")
    else:
        click.echo(f"\n{'─'*60}")
        click.echo(f"DRY RUN — would write: inbox/queue-generated/{filename}")
        click.echo(f"{'─'*60}")
        click.echo(content)
        click.echo(f"{'─'*60}")
        click.echo("Re-run with --apply to save.")
