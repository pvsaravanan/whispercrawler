<p align="center">
  <img src="assets/logo.png" width="220" alt="WhisperCrawler Logo">
</p>
<div align="center">
  <pre>
██╗    ██╗██╗  ██╗██╗███████╗██████╗ ███████╗██████╗ 
██║    ██║██║  ██║██║██╔════╝██╔══██╗██╔════╝██╔══██╗
██║ █╗ ██║███████║██║███████╗██████╔╝█████╗  ██████╔╝
██║███╗██║██╔══██║██║╚════██║██╔═══╝ ██╔══╝  ██╔══██╗
╚███╔███╔╝██║  ██║██║███████║██║     ███████╗██║  ██║
 ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝

 ██████╗██████╗  █████╗ ██╗    ██╗██╗     ███████╗██████╗ 
██╔════╝██╔══██╗██╔══██╗██║    ██║██║     ██╔════╝██╔══██╗
██║     ██████╔╝███████║██║ █╗ ██║██║     █████╗  ██████╔╝
██║     ██╔══██╗██╔══██║██║███╗██║██║     ██╔══╝  ██╔══██╗
╚██████╗██║  ██║██║  ██║╚███╔███╔╝███████╗███████╗██║  ██║
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝╚══════╝╚═╝  ╚═╝
 </pre>
</div>

  <p align="center">
    <strong>The adaptive web scraping framework — fast, stealthy, and self-healing.</strong>
  </p>
  <p align="center">
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
    <a href="https://github.com/WhisperCrawl/WhisperCrawler"><img src="https://img.shields.io/badge/build-passing-brightgreen.svg" alt="Build Status"></a>
    <a href="https://github.com/WhisperCrawl/WhisperCrawler"><img src="https://img.shields.io/badge/coverage-80%25-brightgreen.svg" alt="Coverage"></a>
  </p>
</p>

---

## Overview

**WhisperCrawler** is an enterprise-ready Python framework designed for extreme resilience and stealth. It bridges the gap between high-performance static data extraction and hardened browser automation, all powered by a unique **adaptive selection engine** that automatically heals broken selectors after website redesigns.

### Why WhisperCrawler?

*   **Unbeatable Stealth**: Native bypass for Turnstile, Cloudflare, and advanced WAFs.
*   **Self-Healing DOM**: Adaptive parsing recovers data even when CSS/XPath structures change.
*   **High Performance**: Built on `curl_cffi` for HTTP/3 speed and `Playwright` for dynamic precision.
*   **Distributed Ready**: Seamless proxy rotation, session persistence, and persistent crawling.

---

## Installation

Install the core package via pip:

```bash
pip install whispercrawler
```

Enhance your toolkit with specialized fetchers or AI agent support:

```bash
# Full browser and anti-bot support
pip install "whispercrawler[fetchers]"

# MCP server for AI research agents
pip install "whispercrawler[mcp]"

# Initialize stealth browser environment
whispercrawler install
```

---

## Strategic Fetching

WhisperCrawler allows you to select the right tool for every site complexity:

| Strategy | Engine | Best For | Speed |
| :--- | :--- | :--- | :--- |
| **Crawler** | `curl_cffi` (HTTP/3) | Static HTML, JSON APIs, high-volume scraping | **Ultra-Fast** |
| **GhostCrawler** | `Playwright` | SPAs, React/Vue sites, login flows | **Fast** |
| **ShadowCrawler** | `Camoufox` (Hardened) | Cloudflare Turnstile, PerimeterX, Datadome | **Efficient** |

---

## Quick Start

WhisperCrawler exposes a unified API across all fetchers.

```python
from whispercrawler import Crawler, GhostCrawler, ShadowCrawler

# 1. High-speed extraction
page = Crawler.get("https://example.com")
print(page.css("h1::text").get())

# 2. Dynamic content (headless browser)
page = GhostCrawler.fetch("https://react-spa.com")
items = page.css(".product-card").getall()

# 3. Complete stealth bypass
page = ShadowCrawler.fetch("https://protected-site.com")
data = page.css("#secure-price", adaptive=True).get()
```

---

## Adaptive Parsing Engine

WhisperCrawler's standout feature is its **Self-Healing Logic**. When traditional selectors fail due to a site update, WhisperCrawler uses stored structural fingerprints to recover elements.

```python
# Initial run: Save fingerprints for the future
title = page.css("h1.main-title", auto_save=True)

# Site redesign? Selector changed to h1.header-title-new?
# No problem. Just enable adaptive mode:
title = page.css("h1.main-title", adaptive=True)
```

---

## Advanced Capabilities

### Automatic Pagination
Detect and follow navigation links automatically without inspecting the DOM.
```python
next_url = page.next_page  # Intelligent "Next" detection
all_pages = page.all_pages # Get all numerical page links
```

### Structured Data (Schema)
Instant JSON-LD and Microdata extraction.
```python
# Get all Product schema data as a clean dictionary
product_info = page.find_schema("Product")
```

### Metadata Enrichment
Learn everything about a page's SEO and Social profile in one call.
```python
meta = page.metadata  # Get SEO, OpenGraph, and Twitter tags
print(page.analyze(summary=True)) # Human-readable summary
```

### Regex Synthesis
Synthesize regular expressions from groups of elements for pattern matching.
```python
# Generate a regex that matches all product IDs in your selection
id_regex = page.css(".product-id").generate_regex()
```

### Automatic Captcha Solving
Internal bridge for 2Captcha and Anti-Captcha (ReCaptcha V2).
```python
page = ShadowCrawler.fetch(url, captcha_api_key="...", captcha_service="2captcha")
```

---

## Scaling to Production

### Integrated Spider Framework
Build robust, persistent crawlers with built-in concurrency and error handling.

```python
from whispercrawler import Spider, Response, Request

class MySpider(Spider):
    name = "enterprise_crawl"
    start_urls = ["https://site.com/catalog"]
    concurrent_requests = 16

    async def parse(self, response: Response):
        for item in response.css(".item"):
            yield {"price": item.css(".price::text").get()}
        
        if response.next_page:
            yield Request(response.next_page)

MySpider().start()
```

### Scrapy Native Support
Already using Scrapy? Inject WhisperCrawler's adaptive engine into your standard spiders.

```python
from whispercrawler.integrations.scrapy import whisper_response

class LegacySpider(scrapy.Spider):
    @whisper_response
    def parse(self, response):
        # response is now adaptive powered by WhisperCrawler
        data = response.css(".dynamic-element", adaptive=True).get()
```

---

## Developer Experience

### Interactive Research Shell
Test selectors and uncurl commands in a pre-configured IPython environment.
```bash
whispercrawler shell
# In shell: uncurl('curl https://site.com -H "..."')
```

### Model Context Protocol (MCP)
Plug WhisperCrawler into your AI Agent (Claude, ChatGPT) for real-time web research.
```bash
# Configuration in MCP settings
"whispercrawler": { "command": "whispercrawler-mcp" }
```

---

## Contributing

We welcome professional contributions. Please review our [Contributing Guide](CONTRIBUTING.md) to understand our coding standards, testing requirements, and branch management.

---

## License

Distributed under the [**MIT License**](LICENSE).

---

<p align="center">
  Built for the scraping community.
</p>
