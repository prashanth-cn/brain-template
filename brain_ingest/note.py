"""Generate an Obsidian note from extracted knowledge."""

import re
from datetime import datetime
from pathlib import Path


def _slugify(text: str) -> str:
    """Convert a title to a safe filename."""
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text[:80]


def _extract_claims(raw: str) -> list[str]:
    """Pull claim lines from the extraction output."""
    claims = []
    in_claims = False
    for line in raw.splitlines():
        if line.strip().startswith("## Claims"):
            in_claims = True
            continue
        if line.strip().startswith("## ") and in_claims:
            break
        if in_claims and line.strip().startswith("- "):
            claims.append(line.strip()[2:])
    return claims


def build_note(extraction: dict, source: str, source_type: str) -> tuple[str, str]:
    """
    Build an Obsidian markdown note.
    Returns (filename, note_content).
    """
    title = extraction["title"] or "untitled capture"
    raw = extraction["raw_extraction"]
    now = datetime.now().strftime("%Y-%m-%d")

    # Build wikilinks from claims (prose-as-title convention)
    claims = _extract_claims(raw)
    claim_links = "\n".join(f"- [[{c}]]" for c in claims) if claims else "_none extracted_"

    note = f"""---
source: {source}
type: {source_type}
created: {now}
status: inbox
---

# {title}

> [!abstract]
> Captured {now} from `{source_type}`. Review and promote to `knowledge/graph/`.

## Key Claims
{claim_links}

---

{raw}

## Source
{source}
"""

    filename = f"{now} {_slugify(title)}.md"
    return filename, note


def write_note(filename: str, content: str, vault_path: str) -> str:
    """Write the note to inbox/queue-generated/ and return the full path."""
    inbox = Path(vault_path) / "inbox" / "queue-generated"
    inbox.mkdir(parents=True, exist_ok=True)
    out = inbox / filename
    out.write_text(content, encoding="utf-8")
    return str(out)
