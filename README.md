<p align="center">
  <img src="assets/logo.png" width="250" alt="WhisperCrawler Logo">
</p>

# WhisperCrawler

Adaptive web scraping framework — fast, stealthy, and self-healing.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/WhisperCrawl/WhisperCrawler)
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen.svg)](https://github.com/WhisperCrawl/WhisperCrawler)

WhisperCrawler is a modern Python-based web scraping framework designed for speed, resilience, and stealth. It integrates advanced fetchers to bypass sophisticated anti-bot systems while providing a self-healing selection engine that survives website redesigns.

## Core Capabilities

- **Anti-Bot Bypass**: Native integration with heavily-patched headless browsers to evade fingerprinting and perimeter security.
- **Stealth Fingerprinting**: High-performance concurrent static HTTP fetcher supporting HTTP/3 and TLS fingerprinting.
- **Self-Healing Selectors**: Adaptive parsing technology that recovers elements based on structural similarity when traditional CSS/XPath selectors fail.
- **Distributed Readiness**: Built-in support for proxy rotation, session persistence, and concurrent request scheduling.

## Installation

Install the core package using pip:

```bash
pip install whispercrawler
```

For advanced browser-based fetchers or MCP support, use the following extras:

```bash
# Install with browser automation support
pip install "whispercrawler[fetchers]"

# Install with MCP server support
pip install "whispercrawler[mcp]"

# Download required browser binaries
whispercrawler install
```

## Quick Start

WhisperCrawler provides multiple fetcher strategies depending on the target site's complexity.

```python
from whispercrawler import Crawler, GhostCrawler, ShadowCrawler, Spider, Request, Response

# 1. High-Performance Static Fetch (Best for APIs and simple sites)
page = Crawler.get("https://example.com")
print(page.css("h1::text").get())

# 2. Dynamic Content Parsing (Best for SPAs and JS-rendered content)
page = GhostCrawler.fetch("https://spa-example.com", headless=True)
items = page.css(".product-card")

# 3. Advanced Stealth (Best for sites protected by Cloudflare/WAFs)
page = ShadowCrawler.fetch("https://protected.example.com")
price = page.css(".price::text").get()

# 4. Adaptive Parsing (Self-healing selectors)
page = Crawler.get("https://example.com")
title = page.css("h1", auto_save=True)  # Fingerprints and saves the element
# During a redesign, the selector survives by searching for similarity
title = page.css("h1", adaptive=True)
```

## Fetcher Strategy Documentation

| Fetcher           | Implementation                | Ideal For                                 | Performance |
| :---------------- | :---------------------------- | :---------------------------------------- | :---------- |
| **Crawler**       | `curl_cffi` (HTTP/3)          | Static HTML, REST APIs, JSON Endpoints    | Ultra-Fast  |
| **GhostCrawler**  | `Playwright` / `Patchright`   | SPAs, Interactive JS Applications         | Fast        |
| **ShadowCrawler** | `Camoufox` (Hardened Firefox) | Advanced anti-bot, Cloudflare, PerimeterX | Moderate    |

## Technical Features

### Adaptive Parsing Engine

WhisperCrawler introduces a resilient selection mechanism. When `auto_save=True` is enabled, the engine stores a structural fingerprint (tag name, attribute distributions, text density, and DOM depth) in a local SQLite database. If the website's layout changes and the selector fails, the `adaptive=True` mode triggers a similarity search to find the new location of the target element.

### Session Management

Maintain shared state across multiple requests, including cookies, connection pools, and browser context.

```python
from whispercrawler import FetcherSession, DynamicSession

# Static HTTP session
with FetcherSession() as session:
    session.get("https://example.com/login")
    response = session.post("https://example.com/api", json={"key": "val"})

# Dynamic browser session
with DynamicSession(headless=True, max_pages=5) as session:
    page = session.fetch("https://example.com/dashboard")
```

### Proxy Rotation with ProxyWheel

The `ProxyWheel` utility handles intelligent proxy rotation and automatic quarantine for failing proxies.

```python
from whispercrawler import Crawler, ProxyWheel

rotator = ProxyWheel(
    proxies=["http://proxy1:8080", "http://proxy2:8080"],
    strategy="least_used"
)

# Apply to specific request
page = Crawler.get("https://example.com", proxy_rotator=rotator)

# Or set globally
Crawler.proxy_rotator = rotator
```

## Spider Framework

Build scalable crawlers using the built-in Spider class.

```python
from whispercrawler import Spider, Response, Request

class QuoteSpider(Spider):
    name = "quotes_crawler"
    start_urls = ["https://quotes.toscrape.com/"]
    concurrent_requests = 10

    async def parse(self, response: Response):
        for quote in response.css(".quote"):
            yield {
                "text": quote.css(".text::text").get(),
                "author": quote.css(".author::text").get(),
            }

        if next_page := response.css("li.next a::attr(href)").get():
            yield Request(url=response.urljoin(next_page))

QuoteSpider().start()
```

## CLI Reference

| Command          | Sub-command   | Parameters       | Description                     |
| :--------------- | :------------ | :--------------- | :------------------------------ |
| `whispercrawler` | `install`     | `--force`        | Setup browser binaries          |
| `whispercrawler` | `extract get` | `<url> <output>` | Command-line extraction         |
| `whispercrawler` | `shell`       |                  | Interactive IPython environment |
| `whispercrawler` | `mcp`         | `--http`         | Launch the MCP server           |

## Advanced Features

### Automatic Pagination Detection
WhisperCrawler can automatically identify pagination links using structural heuristics and common patterns (Next, Page numbers, rel="next").

```python
page = Crawler.get("https://blog.example.com")

# Detect the next page URL automatically
next_url = page.next_page
if next_url:
    next_page = Crawler.get(next_url)

# Detect all available page links in a pagination block
all_links = page.all_pages
for link in all_links:
    print(f"Found page: {link}")
```

## Integrations

### Scrapy Integration
WhisperCrawler provides a seamless decorator to replace Scrapy's default `parsel` selectors with its own adaptive engine. This allows you to use self-healing selectors directly within standard Scrapy spiders.

```python
from whispercrawler.integrations.scrapy import whisper_response

class MySpider(scrapy.Spider):
    name = "my_spider"
    
    @whisper_response
    def parse(self, response):
        # response is now powered by WhisperCrawler
        # Standard selection
        title = response.css("h1::text").get()
        
        # Adaptive selection (survives site redesigns)
        price = response.css(".current-price", adaptive=True).get()
        
        # WhisperCrawler specific helpers
        contact = response.find_by_text("Contact Us", partial=True)
```

## MCP Server Integration

WhisperCrawler provides a Model Context Protocol (MCP) server, allowing AI agents (such as Claude Desktop) to perform real-time web research and data extraction.

### Configuration

Add the following to your MCP settings file:

```json
{
  "mcpServers": {
    "whispercrawler": {
      "command": "whispercrawler-mcp",
      "args": []
    }
  }
}
```

## Professional Development Environment

The project provides an interactive shell for testing extraction logic. Execute `whispercrawler shell` to enter an IPython REPL with all fetchers and parsing utilities pre-loaded. It includes specialized macros like `uncurl()` to transform browser curl commands into WhisperCrawler requests instantly.

## Contributing

We welcome contributions from the community! Whether you are fixing a bug, improving documentation, or adding new stealth features, your help is appreciated. Please see our [Contributing Guide](CONTRIBUTING.md) for details on our development workflow and standards.

## License

**MIT License**

Copyright (c) 2026, Saravanan P V

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
