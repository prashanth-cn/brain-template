# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This is a dedicated Obsidian memory vault. Its purpose is to give Claude persistent, queryable knowledge across sessions — a brain that compounds instead of resets.

Every session: **orient → work → persist**. Read `00-home/index.md` to orient. Write new knowledge to the appropriate folder. Update `00-home/top-of-mind.md` with active context.

## Vault Conventions

**Note naming — prose-as-title**: Name notes as claims, not categories.
- `memory graphs beat giant memory files.md` ✓
- `memory-systems.md` ✗

**Wiki-links — links as prose**: Links should read naturally in sentences.
- `we found that [[memory graphs beat giant memory files]] when we [[benchmark retrieval like search infrastructure]]` ✓

**Atomic notes**: One idea per note. Link to compose complexity.

## Folder Guide

| Folder | What goes here |
|---|---|
| `00-home/` | Maps of content, active attention (`top-of-mind.md`) |
| `atlas/` | Structural indexes (projects, research threads, vault architecture) |
| `inbox/` | Anything unprocessed — promote to `knowledge/` after review |
| `inbox/queue-generated/` | Drop zone for brain-ingest and agent output |
| `knowledge/graph/research/` | Curated research notes |
| `knowledge/graph/repo-research/` | Codebase and project-specific knowledge |
| `knowledge/graph/agent-daily/` | Agent daily observations and patterns |
| `knowledge/memory/` | Persistent memory notes across Claude sessions |
| `sessions/` | Raw session transcripts |
| `voice-notes/` | Transcribed voice memos |

## Memory vs Inbox

- `inbox/` is temporary — everything here should be reviewed and either promoted or discarded
- `knowledge/memory/` is permanent — persistent facts, decisions, and patterns worth keeping forever

## brain-ingest CLI

Ingests YouTube videos, audio/video files, or text transcripts into `inbox/queue-generated/`.

```bash
# Activate venv first
source .venv/bin/activate

# YouTube video (downloads + transcribes locally, then extracts with Claude)
brain-ingest "https://youtube.com/watch?v=..." --apply

# Local audio or video
brain-ingest /path/to/recording.mp4 --apply

# Plain text / markdown transcript
brain-ingest /path/to/notes.txt --transcript --title "Team Retro" --apply

# Dry-run (preview without writing)
brain-ingest "https://youtube.com/watch?v=..."
```

Requires `ANTHROPIC_API_KEY` in `.env` at vault root.
Whisper transcription runs fully locally — no audio leaves your machine.
