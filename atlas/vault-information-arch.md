# Vault Information Architecture

How this vault is structured and why.

## Design Principles

- **Prose-as-title**: Notes are named as claims, not categories. `memory graphs beat giant memory files` not `memory-systems`
- **Wiki-links as prose**: Links read as sentences — `we learned that [[memory graphs beat giant memory files]] when we [[benchmark retrieval like search infrastructure]]`
- **Atomic notes**: One idea per note. Compose complexity through links
- **Progressive disclosure**: Four folder levels so retrieval finds the right depth on first pass

## Folder Purposes

| Folder | Purpose |
|---|---|
| `00-home/` | Maps of content and active attention |
| `atlas/` | Structural overviews and indexes |
| `inbox/` | Unprocessed captures — review and promote |
| `inbox/queue-generated/` | Agent-generated drops (brain-ingest output) |
| `knowledge/graph/` | Curated knowledge graph |
| `knowledge/graph/agent-daily/` | Agent daily observations |
| `knowledge/graph/research/` | Research notes |
| `knowledge/graph/repo-research/` | Codebase-specific knowledge |
| `knowledge/memory/` | Persistent memory for Claude sessions |
| `sessions/` | Raw session transcripts |
| `voice-notes/` | Transcribed voice captures |

## Retrieval Pattern

Claude searches → titles alone indicate relevance → reads body only if relevant → follows wikilinks for depth
