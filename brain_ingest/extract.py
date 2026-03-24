"""Extract structured knowledge from a transcript using Claude."""

import os
import sys
from pathlib import Path
import anthropic


def _load_env():
    """Load .env file from vault root if present."""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

EXTRACTION_PROMPT = """\
You are a knowledge extraction engine. Given a transcript, extract the highest-signal knowledge into structured categories.

Be ruthlessly selective — only include ideas worth preserving long-term. Skip filler, introductions, and repetition.

Return your response as markdown with exactly these sections:

## Claims
Atomic, falsifiable statements worth preserving. Name each as a prose claim (as if it were a note title).
Format: `- claim text`

## Frameworks
Named mental models, systems, or frameworks introduced. Include a 1-2 sentence explanation.
Format: `- **Framework Name**: explanation`

## Action Items
Concrete, specific techniques or steps someone could apply.
Format: `- action`

## Examples
Memorable concrete examples that anchor the abstract ideas.
Format: `- example with brief context`

## Key Tensions
Tradeoffs, contradictions, or nuanced "it depends" situations highlighted.
Format: `- tension`

---

TRANSCRIPT:
{transcript}
"""


def extract_knowledge(transcript: str, title: str = "") -> dict:
    """Call Claude to extract structured knowledge from a transcript."""
    _load_env()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "Error: ANTHROPIC_API_KEY not set.\n"
            "Add it to /Users/prashanth/Documents/brain/.env as:\n"
            "  ANTHROPIC_API_KEY=sk-ant-...",
            file=sys.stderr,
        )
        sys.exit(1)
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": EXTRACTION_PROMPT.format(transcript=transcript[:50000]),
        }]
    )

    raw = message.content[0].text
    return {"title": title, "raw_extraction": raw}
