# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

```bash
# Install with all dependencies
pip install -e ".[dev,fetchers,mcp]"

# Install browser binaries (required for GhostCrawler/ShadowCrawler)
whispercrawler install
```

## Gotchas

- `Response` (used in `Spider.parse` callbacks) is defined in `engines/toolbelt/custom.py`, not `spiders/`; it's re-exported from `whispercrawler.spiders` and `whispercrawler`.

### Adaptive Parsing

whispercrawler supports self-healing element selection:
- `auto_save=True`: Saves element fingerprint to SQLite
- `adaptive=True`: Recovers elements by similarity after site redesigns

## Development Notes

- **Lazy imports**: Main packages use lazy loading via `__getattr__` for faster startup
- **Async-first**: Spider callbacks are `async def`, uses `anyio` for runtime
