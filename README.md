# WhisperCrawler
*Adaptive web scraping — fast, stealthy, and self-healing.*

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen.svg)



## What it does
* **Bypasses advanced bot protection** using stealthy, heavily-patched headless browsers.
* **Rapidly extracts data** using a fast concurrent static HTTP fetcher (HTTP/3 + TLS fingerprinting).
* **Self-heals broken scrapers** by recovering elements based on layout and similarity heuristics when selectors fail.

## Quick start
```python
from whispercrawler import Crawler, GhostCrawler, ShadowCrawler, Spider, Response

# Static HTTP fetch (fastest)
page = Crawler.get("https://example.com")
print(page.css("h1::text").get())

# JavaScript-heavy site
page = GhostCrawler.fetch("https://spa-example.com", headless=True)
items = page.css(".product-card")

# Cloudflare-protected site
page = ShadowCrawler.fetch("https://protected.example.com")
price = page.css(".price::text").get()

# Adaptive parsing — survives site redesigns
page = Crawler.get("https://example.com")
title = page.css("h1", auto_save=True)           # saves fingerprint
# Later, after site redesign — finds element by similarity
title = page.css("h1", adaptive=True)

# Spider
class QuoteSpider(Spider):
    name = "quotes"
    start_urls = ["https://quotes.toscrape.com/"]
    concurrent_requests = 10

    async def parse(self, response: Response):
        for quote in response.css(".quote"):
            yield {
                "text":   quote.css(".text::text").get(),
                "author": quote.css(".author::text").get(),
            }
        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield Request(url=response.url + next_page)

QuoteSpider().start()
```

## Fetcher selection table
| Fetcher | When to use | Backend | Speed |
|---|---|---|---|
| Crawler | Static HTML, APIs, JSON endpoints | curl_cffi HTTP/3 | Fastest |
| GhostCrawler | JavaScript-rendered pages, SPAs | Playwright/Patchright Chromium | Medium |
| ShadowCrawler | Cloudflare, advanced bot detection | Camoufox (modified Firefox) | Slower |

## Adaptive parsing
WhisperCrawler introduces self-healing element selection. By adding `auto_save=True` to your CSS or XPath calls, it saves a detailed structural fingerprint of the matched element to a local SQLite database. If a site undergoes a redesign and your selector stops matching, switching to `adaptive=True` allows WhisperCrawler to search the DOM for elements that closely match the stored fingerprint (using tag, text similarity, attribute overlap, and DOM depth calculation), returning the closest match automatically.

## Installation
```bash
pip install whispercrawler
pip install "whispercrawler[fetchers]"   # for GhostCrawler and ShadowCrawler
pip install "whispercrawler[mcp]"        # for MCP server
whispercrawler install                   # download browser binaries
```

## CLI reference
| Command | Options | Description |
|---|---|---|
| `whispercrawler install` | `--force` | Download browser binaries required for Ghost/Shadow fetchers |
| `whispercrawler get <url>` | `--stealth`, `--ghost`, `--css <sel>`, `--xpath <sel>`, `--output <type>`, `--adaptive` | Fetch URL and extract elements via CLI |
| `whispercrawler shell` | | Launch interactive Python shell with preloaded environment |

## MCP server setup
WhisperCrawler includes a Model Context Protocol (MCP) server that exposes scraping tools to AI agents like Claude Desktop or OpenCode.

Configure your agent's MCP settings to add the `whispercrawler` server via stdio:
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

## Session usage
Maintain shared persistent state (cookies, connection pools, proxies) across multiple requests using sessions.

```python
from whispercrawler import CrawlerSession, GhostSession, ShadowSession

# Static requests
with CrawlerSession(browser_type="chrome") as session:
    page1 = session.get("https://example.com/login")
    page2 = session.post("https://example.com/api", json={"user": "foo"})

# Playwright SPA session
with GhostSession(headless=True, max_pages=3) as session:
    page = session.fetch("https://example.com")

# Camoufox stealth session
with ShadowSession(humanize=True) as session:
    page = session.fetch("https://protected.com")
```

## ProxyWheel usage
Efficiently rotate through a pool of proxies using `ProxyWheel`. It automatically quarantines failed proxies for 5 minutes.

```python
from whispercrawler import Crawler, ProxyWheel

rotator = ProxyWheel(["http://proxy1:8080", "http://proxy2:8080"], strategy="least_used")

# Apply to a single request
page = Crawler.get("https://example.com", proxy_rotator=rotator)

# Or apply globally to the class
Crawler.proxy_rotator = rotator
```

## Interactive shell
The interactive shell provides a quick scratchpad to test scraping logic without writing full scripts. Running `whispercrawler shell` launches an IPython REPL with all fetcher classes, a persistent session history, and handy macros (like `curl2crawler()`) pre-imported to immediately begin querying pages interactively.

## License
**MIT License**

Copyright (c) 2026, Saravanan P V

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


