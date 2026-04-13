# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

```bash
# Install with all dependencies
pip install -e ".[dev,fetchers,mcp]"

# Install browser binaries (required for GhostCrawler/ShadowCrawler)
whispercrawler install

# Run tests
pytest whispercrawler/tests -v --tb=short

# Run with coverage
pytest whispercrawler/tests -v --tb=short --cov=whispercrawler --cov-report=term-missing

# Run a single test
pytest whispercrawler/tests/test_parser.py::TestClass::test_method -v

# Lint
ruff check whispercrawler/

# Type check
mypy whispercrawler/
```

## High-Level Architecture

### Core Modules

```
whispercrawler/
├── parser.py           # Selector/Selectors classes - HTML parsing with CSS/XPath
├── cli.py              # CLI entry points (shell, get, mcp, install)
├── shell.py            # Interactive IPython shell
├── mcp_server.py       # Model Context Protocol server for AI agents
├── proxy.py            # ProxyWheel for proxy rotation
├── fetchers/           # HTTP and browser-based fetchers
│   ├── requests.py     # Static HTTP fetcher (curl_cffi)
│   ├── chrome.py       # Playwright-based dynamic fetcher
│   ├── stealth_chrome.py  # Anti-bot protected sites (Camoufox)
│   └── shadow.py       # Cloudflare bypass fetcher
├── spiders/            # Scrapy-inspired crawling framework
│   ├── spider.py       # Base Spider class
│   ├── engine.py       # CrawlerEngine orchestrates crawl loop
│   ├── scheduler.py    # Priority queue with deduplication
│   ├── session.py      # SessionManager routes requests
│   ├── request.py      # Request objects
│   └── response.py     # Response objects
├── engines/            # Browser engines and toolbelt
│   ├── _browsers/      # Browser controllers (Playwright/Camoufox)
│   └── toolbelt/       # Utilities (proxy rotation, fingerprints)
└── core/
    ├── storage.py      # SQLite storage for adaptive parsing
    ├── mixins.py       # Selector generation mixins
    ├── translator.py   # CSS to XPath translator
    └── utils/          # Shell utilities, helpers
```

### Key Classes

| Class | Purpose |
|-------|---------|
| `Selector` / `Page` | HTML parsing, CSS/XPath selection, adaptive element recovery |
| `Fetcher` (`Crawler`) | Fast static HTTP requests via curl_cffi (HTTP/3, TLS fingerprinting) |
| `DynamicFetcher` (`GhostCrawler`) | Playwright-based for JavaScript-heavy sites |
| `StealthyFetcher` | Camoufox-based for Cloudflare/anti-bot protected sites |
| `ShadowFetcher` (`ShadowCrawler`) | Advanced Cloudflare bypass |
| `Spider` | Async crawling framework with concurrency, pause/resume |
| `ProxyWheel` | Automatic proxy rotation with quarantine for failed proxies |

### Fetcher Selection

| Fetcher | Use Case | Backend |
|---------|----------|---------|
| `Crawler` / `Fetcher` | Static HTML, APIs | curl_cffi HTTP/3 |
| `GhostCrawler` | JavaScript-rendered, SPAs | Playwright Chromium |
| `ShadowCrawler` | Cloudflare, bot protection | Camoufox (Firefox) |

### Adaptive Parsing

WhisperCrawler supports self-healing element selection:
- `auto_save=True`: Saves element fingerprint to SQLite
- `adaptive=True`: Recovers elements by similarity after site redesigns

### Spider Architecture

Data flow: `Spider` → `Scheduler` (queue) → `SessionManager` → `Fetcher` → `Response` → callback

Key features:
- Concurrent requests with configurable limits
- Multi-session support (different fetcher types per spider)
- Checkpoint system for pause/resume via `crawldir`
- Built-in blocked response detection and retry logic

### MCP Server

The MCP server exposes scraping tools to AI agents:
- `get` / `bulk_get`: Static HTTP requests
- `fetch` / `bulk_fetch`: Dynamic browser fetching
- `stealthy_fetch` / `bulk_stealthy_fetch`: Anti-bot protected sites

## Development Notes

- **Lazy imports**: Main packages use lazy loading via `__getattr__` for faster startup
- **Async-first**: Spider callbacks are `async def`, uses `anyio` for runtime
- **Type hints**: Full type annotations throughout, checked with mypy
- **Testing**: pytest with asyncio mode, 80% coverage requirement

## Common Patterns

```python
# Basic scraping
from whispercrawler import Crawler
page = Crawler.get("https://example.com")
items = page.css(".product").getall()

# Session-based (efficient for multiple requests)
from whispercrawler import CrawlerSession
with CrawlerSession() as session:
    page1 = session.get(url1)
    page2 = session.get(url2)

# Spider example
from whispercrawler import Spider, Response, Request

class MySpider(Spider):
    name = "my_spider"
    start_urls = ["https://example.com"]
    
    async def parse(self, response: Response):
        for item in response.css(".item"):
            yield {"name": item.css("::text").get()}
        next_url = response.css("a.next::attr(href)").get()
        if next_url:
            yield Request(next_url)

MySpider().start()
```
