# Architecture

## Overview

`brain` is a personal knowledge vault with two parts:

1. **Vault** — an Obsidian folder of markdown notes (the data)
2. **`brain_ingest` Python package** — CLI tools that read/write the vault and sync it to Git

Claude Code connects to the vault via an MCP server and persists session learnings automatically on exit.

---

## Components

```
brain/
├── brain_ingest/        # Python package
│   ├── cli.py           # brain-ingest CLI entrypoint
│   ├── extract.py       # Claude Sonnet extraction prompt + API call
│   ├── transcribe.py    # Whisper transcription + yt-dlp download
│   ├── note.py          # Note formatting and vault write
│   └── persist.py       # brain-persist CLI: session → vault → git push
├── setup.sh             # One-shot setup for a new machine
├── pyproject.toml       # Package definition + CLI entrypoints
│
├── 00-home/             # Vault index and active attention
├── atlas/               # Structural indexes
├── inbox/               # Unprocessed drops
│   └── queue-generated/ # brain-ingest output lands here
├── knowledge/
│   ├── graph/           # Curated, promoted notes
│   └── memory/          # Persistent facts across Claude sessions
├── sessions/            # Auto-generated session learning notes
└── voice-notes/         # Transcribed voice memos
```

---

## Data Flow

### Ingest (manual)

```
Source (YouTube URL / audio file / transcript)
  → yt-dlp download          (cli.py + transcribe.py)
  → Whisper transcription     (transcribe.py, runs locally)
  → Claude Sonnet extraction  (extract.py)
  → Markdown note             (note.py)
  → inbox/queue-generated/    (vault)
```

### Session persist (automatic on Claude exit)

```
Claude session ends
  → Stop hook triggers brain-persist
  → Reads ~/.claude/sessions/*.jsonl  (last session transcript)
  → Claude Haiku extracts learnings
  → Writes to sessions/<timestamp>-session-learnings.md
  → git add -A && git commit && git push  (vault synced to origin)
```

### Claude ↔ Vault (during session)

```
Claude Code
  → brain-obsidian MCP server (obsidian-mcp via npx)
  → Read / write / search vault notes directly
```

---

## Setup (`setup.sh`)

Idempotent. Safe to rerun on a new machine.

| Step | What it does |
|------|-------------|
| 1 | Checks Python 3.11+, node, ffmpeg |
| 2 | Verifies Claude Code is installed |
| 3 | Creates `.venv`, installs `brain_ingest` package |
| 4 | Writes `ANTHROPIC_API_KEY` to `.env` |
| 5 | Copies `.mcp.json` and `.claude/settings.local.json` from templates |
| 6 | Saves vault path to `~/.config/brain/vault` |
| 7 | Installs `brain-ingest` / `brain-persist` wrappers to `~/.local/bin` |
| 8 | Registers `brain-obsidian` MCP server with Claude Code (user scope) |
| 9 | Adds `brain-persist` Stop hook to `~/.claude/settings.json` |

The vault path is always the directory where `setup.sh` lives — clone the repo anywhere and it self-configures.

---

## Key Design Decisions

- **Local transcription** — Whisper runs on-device via `faster-whisper`. Audio never leaves the machine.
- **Prose-as-title notes** — Notes named as claims (`memory graphs beat giant memory files.md`) so wikilinks read as prose.
- **Haiku for persist, Sonnet for ingest** — Persist runs on every session exit so uses the cheaper/faster Haiku. Ingest is manual and uses Sonnet for higher quality extraction.
- **Git as sync layer** — No custom sync daemon. The vault is a git repo; `brain-persist` commits and pushes on every session end.
- **MCP scope: user** — `brain-obsidian` is registered at user scope so it's available in every Claude Code project, not just this repo.
