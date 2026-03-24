"""
brain-persist: called by Claude Code Stop hook.
Reads the last session transcript, extracts learnings, writes to vault.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

VAULT = Path(__file__).parent.parent
SESSIONS_DIR = Path.home() / ".claude" / "sessions"


def get_last_session_transcript() -> str | None:
    """Find and read the most recently modified Claude Code session file."""
    sessions = sorted(SESSIONS_DIR.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not sessions:
        return None

    lines = []
    for raw in sessions[0].read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(raw)
            # Extract text content from assistant/user messages
            msg = entry.get("message", {})
            role = msg.get("role", "")
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                lines.append(f"{role.upper()}: {content.strip()}")
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "").strip()
                        if text:
                            lines.append(f"{role.upper()}: {text}")
        except (json.JSONDecodeError, KeyError):
            continue

    return "\n\n".join(lines) if lines else None


def extract_and_save(transcript: str) -> str:
    """Use Claude to extract key learnings and write to vault."""
    from brain_ingest.extract import _load_env
    import anthropic

    _load_env()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "ANTHROPIC_API_KEY not set — skipping session persist"

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""\
Review this Claude Code session transcript and extract only what's worth persisting long-term in a knowledge vault.

Focus on:
- Decisions made and their rationale
- Patterns or conventions established
- Problems solved in a non-obvious way
- Things that should NOT be done (and why)

If there's nothing worth persisting (routine Q&A, trivial tasks), respond with just: NOTHING_TO_SAVE

Otherwise, write a concise Obsidian note in markdown. Use a prose-as-claim title on the first line (starting with # ).
Include wikilinks [[like this]] for key concepts. Keep it under 300 words.

SESSION TRANSCRIPT (last 8000 chars):
{transcript[-8000:]}
"""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    result = msg.content[0].text.strip()
    if result == "NOTHING_TO_SAVE" or not result:
        return "Nothing worth persisting from this session."

    # Write to sessions/ with timestamp
    now = datetime.now().strftime("%Y-%m-%d-%H%M")
    out = VAULT / "sessions" / f"{now}-session-learnings.md"
    out.write_text(result, encoding="utf-8")
    return f"Saved: {out}"


def git_push_vault() -> str:
    """Stage all vault changes, commit, and push to origin."""
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=VAULT, capture_output=True, text=True
        )
        if not status.stdout.strip():
            return "Git: nothing to commit."

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        subprocess.run(["git", "add", "-A"], cwd=VAULT, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"brain: session persist {now}"],
            cwd=VAULT, check=True
        )
        subprocess.run(["git", "push"], cwd=VAULT, check=True)
        return "Git: pushed vault to origin."
    except subprocess.CalledProcessError as e:
        return f"Git push failed: {e}"


def main():
    transcript = get_last_session_transcript()
    if not transcript:
        print("No session transcript found.")
        sys.exit(0)

    print(f"Processing session ({len(transcript.split())} words)...")
    result = extract_and_save(transcript)
    print(result)
    print(git_push_vault())


if __name__ == "__main__":
    main()
