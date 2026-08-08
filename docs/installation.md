# Installation

## Requirements
whispercrawler requires **Python 3.10 or higher** and runs on Windows, macOS, and Linux.

## Basic Install
```bash
pip install whispercrawler
```
This installs only the parser engine (`Selector`/`Page`) and its dependencies — no fetchers, no browsers. It also pulls in the CLI and interactive shell dependencies (`click`, `rich`, `ipython`), so `whispercrawler --help` and `whispercrawler shell` work right away. It's enough if you already have HTML on hand and only need to parse/select from it.

## Installing Fetchers
To fetch live websites — via plain HTTP requests, a real browser (`GhostCrawler`/`DynamicFetcher`), or the anti-bot `StealthyFetcher`/`ShadowFetcher` — install the `fetchers` extra, then download the browser binaries:
```bash
pip install "whispercrawler[fetchers]"

whispercrawler install           # download browsers + system deps
whispercrawler install --force   # force a clean reinstall
```
`whispercrawler install` downloads Playwright's Chromium, Camoufox's Firefox build, and their fingerprint-manipulation dependencies. This is a one-time step (rerun it after upgrading the package if a fetcher starts complaining about a missing browser).

You can also trigger it from Python instead of the shell:
```python
from whispercrawler.cli import install

install([], standalone_mode=False)          # normal install
install(["--force"], standalone_mode=False) # force reinstall
```

## Installing the MCP Server
To expose whispercrawler's fetchers as tools for AI agents (Claude, Cursor, etc.) via the [MCP server](ai/mcp-server.md):
```bash
pip install "whispercrawler[mcp]"
```
The MCP server also needs live fetchers, so run `whispercrawler install` as well if you haven't already.

## Everything at Once
For local development, or if you just want every capability available:
```bash
pip install "whispercrawler[dev,fetchers,mcp]"
whispercrawler install
```

## Docker
A ready-to-run image with every extra and every browser pre-installed is published on each release:
```bash
docker pull whispercrawl/whispercrawler
# or, from the GitHub registry
docker pull ghcr.io/whispercrawl/whispercrawler:latest
```
Useful if you'd rather skip managing Python/browser dependencies locally, e.g. for the [MCP server](ai/mcp-server.md#docker).

## Verifying the Install
```bash
whispercrawler --help
```
```python
from whispercrawler import Crawler
page = Crawler.get("https://example.com")
print(page.status, len(page.css("a")))
```
If the fetchers extra and browsers are installed correctly, this also works:
```python
from whispercrawler import GhostCrawler
page = GhostCrawler.fetch("https://example.com")
print(page.status)
```

## Next Steps
Head to the [Quickstart](quickstart.md) to make your first request and parse your first page.
