# WhisperCrawler Codebase Report

**Generated:** 2026-04-03  
**Version:** 0.2.0 (package), 0.4.2 (skill)  
**License:** BSD-3-Clause

---

## Executive Summary

WhisperCrawler is an adaptive web scraping framework built for Python 3.10+. It combines three core capabilities:

1. **Stealth Fetching** - Multiple browser engines bypass anti-bot systems (Cloudflare Turnstile, etc.)
2. **Adaptive Parsing** - Self-healing element selection that survives website redesigns
3. **Spider Framework** - Scrapy-inspired concurrent crawling with pause/resume support

The codebase is well-structured with clear separation of concerns, comprehensive test coverage, and lazy-loading for performance.

---

## Package Structure

```
whispercrawler/
├── __init__.py           # Lazy imports via __getattr__
├── parser.py             # Core: Selector/Selectors classes (60KB)
├── cli.py                # CLI: shell, extract, mcp, install (28KB)
├── shell.py              # IPython shell with scraping shortcuts
├── mcp_server.py         # MCP server for AI agents
├── proxy.py              # ProxyWheel: thread-safe proxy rotation
│
├── core/
│   ├── _types.py         # Type aliases (Any, Dict, List, etc.)
│   ├── custom_types.py   # TextHandler, AttributesHandler, TextHandlers
│   ├── mixins.py         # SelectorsGeneration mixin
│   ├── storage.py        # SQLiteStorageSystem for adaptive parsing
│   ├── translator.py     # CSS to XPath translator
│   ├── shell.py          # Shell utilities (curl conversion)
│   └── utils/
│       ├── _utils.py     # HTML cleaning, logging helpers
│       └── _shell.py     # Cookie/header parsers
│
├── fetchers/
│   ├── __init__.py       # Lazy exports
│   ├── requests.py       # Fetcher/AsyncFetcher (curl_cffi HTTP/3)
│   ├── chrome.py         # DynamicFetcher (Playwright Chromium)
│   ├── stealth_chrome.py # StealthyFetcher (anti-bot)
│   └── shadow.py         # ShadowFetcher (Camoufox/Firefox)
│
├── spiders/
│   ├── __init__.py       # Exports: Spider, Request, Response
│   ├── spider.py         # Base Spider class (abstract)
│   ├── engine.py         # CrawlerEngine orchestration
│   ├── scheduler.py      # PriorityQueue with deduplication
│   ├── session.py        # SessionManager routing
│   ├── request.py        # Request with fingerprinting
│   ├── response.py       # Response wrapper
│   ├── checkpoint.py     # Pickle-based checkpoint system
│   └── result.py         # CrawlResult, CrawlStats, ItemList
│
├── engines/
│   ├── static.py         # _ConfigurationLogic, FetcherClient
│   ├── constants.py      # Browser flags: STEALTH_ARGS, DEFAULT_ARGS
│   ├── toolbelt/
│   │   ├── custom.py     # BaseFetcher, Response class
│   │   ├── convertor.py  # ResponseFactory
│   │   ├── fingerprints.py # User-agent generation
│   │   ├── navigation.py # Route interception handlers
│   │   └── proxy_rotation.py # ProxyRotator, is_proxy_error()
│   └── _browsers/
│       ├── _base.py      # SyncSession, AsyncSession base
│       ├── _controllers.py # DynamicSession, AsyncDynamicSession
│       ├── _page.py      # PageInfo, PagePool classes
│       ├── _config_tools.py # User-agent helpers
│       ├── _validators.py # PlaywrightConfig, StealthConfig
│       ├── _types.py     # Type definitions
│       └── _stealth.py   # Stealth mode implementations
│
└── tests/
    ├── parser/           # Parser tests (adaptive, attributes, general)
    ├── fetchers/         # Fetcher tests (sync/async, sessions)
    ├── spiders/          # Spider tests (engine, scheduler, checkpoint)
    ├── core/             # Core tests (storage, shell)
    ├── cli/              # CLI tests
    └── ai/               # MCP server tests
```

---

## Core Components

### 1. Parser Engine (`parser.py`)

**Key Class:** `Selector`

- Wraps `lxml.html.HtmlElement` without inheriting (avoids pickle issues)
- Uses `__slots__` for memory efficiency
- Supports CSS, XPath, text-based, and similarity-based selection
- Adaptive parsing via SQLite storage (`auto_save=True`, `adaptive=True`)

**Element Relationships:**
- `parent`, `children`, `siblings`, `next`, `previous`
- `iterancestors()`, `find_ancestor(func)`
- `find_similar()`, `below_elements()`

**Custom Types:**
- `TextHandler`: Extended string with chainable methods
- `AttributesHandler`: Dict-like attribute access with `.json()` conversion
- `Selectors`: Generator-based collection of Selector objects

**Storage System:**
- `SQLiteStorageSystem`: Thread-safe (RLock), WAL mode for concurrency
- `@lru_cache` decorated for instance reuse
- Stores element fingerprints as JSON in `elements_storage.db`

---

### 2. Fetchers

#### Static HTTP (`fetchers/requests.py`)

**Classes:** `Fetcher`, `AsyncFetcher`

- Backend: `curl_cffi` with HTTP/3 support
- TLS fingerprint impersonation (Chrome, Firefox, Safari)
- Stealthy headers generation (`stealthy_headers=True`)
- Built-in retry logic with configurable delays

**Configuration Logic:**
```python
# Internal engine handles:
- impersonate: Browser fingerprint selection
- http3: HTTP/3 protocol toggle
- stealth: Auto-generate real browser headers
- proxy/proxies: Static or rotating proxies
- retries/retry_delay: Retry configuration
```

#### Dynamic Content (`fetchers/chrome.py`)

**Classes:** `DynamicFetcher`, `DynamicSession`, `AsyncDynamicSession`

- Backend: Playwright/Patchright Chromium
- Page pooling for concurrent tab management
- Resource blocking for speed optimization
- CDP support for controlling existing browsers

**Key Features:**
- `network_idle`: Wait for network quiescence
- `load_dom`: Wait for JavaScript execution
- `page_action`: Custom automation hooks
- `real_chrome`: Use installed Chrome browser

#### Stealth Fetching (`fetchers/stealth_chrome.py`)

**Classes:** `StealthyFetcher`, `StealthySession`

- Modified Chromium with anti-detection patches
- CDP runtime leak prevention
- WebRTC isolation
- Canvas fingerprinting noise injection
- Headless mode detection bypass

#### Shadow Fetching (`fetchers/shadow.py`)

**Class:** `ShadowFetcher`

- Backend: Camoufox (modified Firefox)
- Built-in Cloudflare Turnstile bypass
- Humanization: random mouse movements, delays
- GeoIP-enabled fingerprinting
- OS randomization option

**Humanization Example:**
```python
def _humanize_sync(page):
    viewport = page.viewport_size or {"width": 1920, "height": 1080}
    for _ in range(random.randint(2, 5)):
        x = random.randint(0, viewport["width"])
        y = random.randint(0, viewport["height"])
        page.mouse.move(x, y)
        time.sleep(random.uniform(0.05, 0.15))
    time.sleep(random.uniform(0.5, 2.0))
```

---

### 3. Spider Framework (`spiders/`)

#### Architecture

```
Spider → Scheduler → CrawlerEngine → SessionManager → Fetcher → Response → Callback
          ↑                                                        ↓
          └────────────────────────────────────────────────────────┘
```

#### Key Classes

**`Spider` (abstract base):**
- `start_urls`, `allowed_domains`
- `concurrent_requests`, `download_delay`
- `max_blocked_retries`, `concurrent_requests_per_domain`
- Lifecycle hooks: `on_start()`, `on_close()`, `on_error()`, `on_scraped_item()`
- `configure_sessions()`: Custom session setup
- `is_blocked()`, `retry_blocked_request()`: Override for custom logic

**`CrawlerEngine`:**
- Manages task group with `anyio`
- Per-domain concurrency limiters
- Checkpoint system integration
- Real-time stats tracking

**`Scheduler`:**
- `asyncio.PriorityQueue` with counter for FIFO within priority
- Deduplication via SHA1 fingerprints
- `snapshot()` / `restore()` for checkpoints
- Configurable fingerprint components (URL, method, body, headers, kwargs)

**`Request`:**
- Fingerprint caching (`_fp` attribute)
- Pickle support via `__getstate__`/`__setstate__`
- Callback restoration via `_restore_callback(spider)`
- Priority comparison operators

**`SessionManager`:**
- Named session registry
- Lazy session initialization support
- Routes requests by `sid` (session ID)

---

### 4. Proxy Rotation (`proxy.py`)

**Class:** `ProxyWheel`

**Strategies:**
- `round_robin`: Sequential rotation
- `random`: Random selection
- `least_used`: Pick proxy with fewest total uses

**Features:**
- Thread-safe (`threading.Lock`)
- Quarantine system (5 minutes for failed proxies)
- Runtime add/remove support
- Status tracking (uses, failures, quarantine_until)

---

### 5. MCP Server (`mcp_server.py`)

**Tools Exposed:**
- `crawl` / `bulk_crawl`: Static HTTP fetching
- `ghost_crawl` / `bulk_ghost_crawl`: Playwright fetching
- `shadow_crawl` / `bulk_shadow_crawl`: Camoufox fetching

**Pattern:**
```python
async def crawl(url: str, css: str = "", xpath: str = "") -> CrawlResult:
    page = await asyncio.get_event_loop().run_in_executor(None, lambda: Crawler.get(url))
    return _extract_result(page, url, css, xpath)
```

**CrawlResult Structure:**
```python
url: str
status_code: int
title: str
text: str
selected: list[str]  # CSS/XPath matches
html_length: int
elapsed_ms: float
error: str | None
```

---

## Key Design Patterns

### 1. Lazy Loading

All main modules use `__getattr__` for deferred imports:

```python
_LAZY_IMPORTS = {
    "Selector": ("whispercrawler.parser", "Selector"),
    "Crawler": ("whispercrawler.fetchers", "Fetcher"),
    # ...
}

def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        module_path, class_name = _LAZY_IMPORTS[name]
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    raise AttributeError(...)
```

**Benefits:** Faster startup, circular import avoidance

### 2. Slot Optimization

Core classes use `__slots__`:

```python
class Selector:
    __slots__ = (
        "url", "encoding", "__adaptive_enabled", "_root", "_storage",
        "__keep_comments", "__huge_tree_enabled", "__attributes",
        "__text", "__tag", "__keep_cdata", "_raw_body",
    )
```

**Benefits:** ~40% memory reduction, faster attribute access

### 3. Async-First with Sync Wrappers

```python
# Async core
async def async_fetch(cls, url: str, **kwargs) -> Response:
    async with AsyncDynamicSession(**kwargs) as session:
        return await session.fetch(url)

# Sync wrapper
@classmethod
def fetch(cls, url: str, **kwargs) -> Response:
    with DynamicSession(**kwargs) as session:
        return session.fetch(url)
```

### 4. Context Managers for Resource Management

```python
class DynamicSession:
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
```

### 5. Fingerprint-Based Deduplication

```python
def update_fingerprint(self, include_kwargs=False, include_headers=False) -> bytes:
    if self._fp is not None:
        return self._fp  # Cache hit
    
    data = {
        "sid": self.sid,
        "body": body.hex(),
        "method": self._session_kwargs.get("method", "GET"),
        "url": canonicalize_url(self.url),
    }
    # ... add headers/kwargs if enabled
    fp = hashlib.sha1(orjson.dumps(data, option=orjson.OPT_SORT_KEYS)).digest()
    self._fp = fp
    return fp
```

---

## Testing Strategy

**Test Organization:**
```
tests/
├── parser/           # Unit tests for Selector, Selectors
├── fetchers/         # Integration tests for all fetcher types
│   ├── sync/         # Synchronous session tests
│   └── async/        # Asynchronous session tests
├── spiders/          # Spider framework tests
├── core/             # Storage, shell utilities
├── cli/              # CLI command tests
└── ai/               # MCP server tests
```

**Coverage Target:** 80% (enforced in CI)

**Key Test Patterns:**
- Mock external dependencies (HTTP servers, browser binaries)
- Async test fixtures with `pytest-asyncio`
- Property-based testing for selector edge cases

---

## Dependencies

### Core (required)
```toml
lxml>=5.2.0          # HTML parsing
cssselect>=1.2.0     # CSS selector engine
msgspec>=0.18.0      # Fast serialization
orjson>=3.10.0       # JSON processing
aiosqlite>=0.20.0    # Async SQLite
markdownify>=0.13.0  # HTML to Markdown
click>=8.1.0         # CLI framework
rich>=13.7.0         # Terminal formatting
ipython>=8.0.0       # Interactive shell
```

### Optional
```toml
# [fetchers]
curl-cffi>=0.7.0     # HTTP/3 requests
playwright>=1.44.0   # Chromium automation
patchright>=1.44.0   # Playwright fork
camoufox[geoip]>=0.4.0  # Firefox-based stealth

# [mcp]
mcp>=1.0.0           # Model Context Protocol

# [dev]
pytest>=8.2.0
pytest-asyncio>=0.23.0
pytest-cov>=5.0.0
ruff>=0.4.0
mypy>=1.10.0
```

---

## CLI Commands

```bash
# Installation
whispercrawler install [--force]

# Extraction
whispercrawler extract get <url> <output> [options]
whispercrawler extract post <url> <output> [options]
whispercrawler extract fetch <url> <output> [options]
whispercrawler extract stealthy-fetch <url> <output> [options]

# Interactive
whispercrawler shell [--loglevel info]

# MCP Server
whispercrawler mcp [--http] [--host 0.0.0.0] [--port 8000]
```

---

## Configuration

### pyproject.toml
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["whispercrawler/tests"]
addopts = "-v --tb=short"

[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E", "W", "F", "I", "B", "UP"]

[tool.mypy]
python_version = "3.10"
strict = true
ignore_missing_imports = true

[tool.coverage.run]
source = ["whispercrawler"]
omit = ["whispercrawler/tests/*"]

[tool.coverage.report]
fail_under = 80
```

---

## Security Considerations

### Implemented
- **Bandit audit** in CI workflow
- **No hardcoded credentials** - all auth via environment/arguments
- **Proxy support** - anonymity and geo-targeting
- **SSL verification** - enabled by default

### User Responsibility
- Respect `robots.txt`
- Comply with website Terms of Service
- Rate limiting (use `download_delay`)
- No bypass of paywalls/auth without permission

---

## Performance Optimizations

1. **Lazy imports** - Faster startup (~200ms savings)
2. **`__slots__`** - Reduced memory footprint
3. **LRU caching** - Storage system, URL parsing, fingerprints
4. **Page pooling** - Reuse browser tabs instead of spawn new
5. **Resource blocking** - Skip images, fonts, unused CSS
6. **HTTP/3 support** - Faster TLS handshakes
7. **Concurrent requests** - Configurable parallelism
8. **WAL mode SQLite** - Better concurrent writes

---

## Known Limitations

1. **Adaptive parsing** requires SQLite file I/O (not suitable for pure in-memory workflows)
2. **ShadowFetcher** status code always returns 200 (Camoufox limitation)
3. **Checkpoint system** uses pickle (Python-specific, not cross-language)
4. **Spider callbacks** must be async generators (Scrapy compatibility layer not implemented)
5. **Browser binaries** require separate download (`whispercrawler install`)

---

## Future Directions (Inferred from Code)

1. **AI Integration** - MCP server expansion, more extraction tools
2. **Adaptive Storage** - Pluggable backends beyond SQLite
3. **Enhanced Stealth** - More anti-detection techniques
4. **Distributed Crawling** - Multi-node checkpoint sharing
5. **Real-time Dashboards** - Stats streaming improvements

---

## Quick Reference

### Import Patterns
```python
# Top-level (lazy)
from whispercrawler import Crawler, Spider, Response, Request

# Direct (faster if module already loaded)
from whispercrawler.fetchers import Fetcher
from whispercrawler.parser import Selector
from whispercrawler.spiders import Spider
```

### Session Usage
```python
# Static HTTP
with FetcherSession(impersonate="chrome") as session:
    page = session.get(url)

# Dynamic
async with AsyncDynamicSession(headless=True) as session:
    page = await session.fetch(url)

# Stealth
async with AsyncStealthySession(solve_cloudflare=True) as session:
    page = await session.fetch(url)
```

### Spider Template
```python
from whispercrawler import Spider, Response, Request

class MySpider(Spider):
    name = "my_spider"
    start_urls = ["https://example.com"]
    concurrent_requests = 10
    
    async def parse(self, response: Response):
        for item in response.css(".item"):
            yield {"title": item.css("::text").get()}
        
        next_url = response.css("a.next::attr(href)").get()
        if next_url:
            yield Request(next_url)

result = MySpider(crawldir="./checkpoints").start()
print(f"Scraped {len(result.items)} items")
```

---

**Report End**
