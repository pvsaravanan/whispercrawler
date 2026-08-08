# Quickstart

This page gets you from zero to a parsed page in a few minutes. If you haven't installed whispercrawler yet, see [Installation](installation.md) first — the examples below need the `fetchers` extra and `whispercrawler install` to have been run.

## Your First Scrape
```python
from whispercrawler import Crawler

page = Crawler.get("https://quotes.toscrape.com/")

quotes = page.css(".quote")
print(f"Found {len(quotes)} quotes")

for quote in quotes[:3]:
    text = quote.css(".text::text").get()
    author = quote.css(".author::text").get()
    print(f"{author}: {text}")
```
`Crawler` (also importable as `Fetcher`) makes a fast HTTP request with browser-like TLS fingerprinting and headers, then hands you back a [`Response`](api-reference/response.md) you can query with CSS or XPath selectors — no browser required.

## From the Terminal — No Code Needed
```bash
whispercrawler extract get "https://quotes.toscrape.com/" quotes.html
```
Or convert a page straight to Markdown:
```bash
whispercrawler extract get "https://quotes.toscrape.com/" quotes.md
```
See [CLI extract commands](cli/extract-commands.md) for the full set of options, or try `whispercrawler shell` for an interactive IPython-based scraping console.

## JavaScript-Rendered Pages
If the site needs a real browser to render its content, swap `Crawler` for `GhostCrawler`:
```python
from whispercrawler import GhostCrawler

page = GhostCrawler.fetch("https://quotes.toscrape.com/js/")
quotes = page.css(".quote")
print(f"Found {len(quotes)} quotes")
```

## Anti-Bot Protected Pages
For sites behind Cloudflare Turnstile or similar protections, use `StealthyFetcher`:
```python
from whispercrawler import StealthyFetcher

page = StealthyFetcher.fetch("https://example.com", solve_cloudflare=True)
print(page.status)
```
Not sure which fetcher fits your target? See [Choosing a fetcher](fetching/choosing.md).

## Selectors That Survive Redesigns
Pass `auto_save=True` once to fingerprint an element, then `adaptive=True` later to relocate it even if the site's markup changes:
```python
products = page.css(".product", auto_save=True)
# ...weeks later, after a site redesign...
products = page.css(".product", adaptive=True)
```
More in [Adaptive parsing](parsing/adaptive.md).

## Scaling to a Crawl
Once a single page works, turn it into a full crawl with `Spider`:
```python
from whispercrawler.spiders import Spider, Response

class QuotesSpider(Spider):
    name = "quotes"
    start_urls = ["https://quotes.toscrape.com/"]

    async def parse(self, response: Response):
        for quote in response.css(".quote"):
            yield {
                "text": quote.css(".text::text").get(),
                "author": quote.css(".author::text").get(),
            }
        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

result = QuotesSpider().start()
result.items.to_json("quotes.json")
```
`Spider` gives you concurrency limits, pause/resume, multi-session support, and proxy rotation out of the box — see [Spiders: getting started](spiders/getting-started.md).

## Talk to It From an AI Agent
whispercrawler ships an [MCP server](ai/mcp-server.md) so tools like Claude can scrape on your behalf:
```bash
whispercrawler mcp
```
Point your MCP-compatible client at it (stdio by default, or `--http` for streamable HTTP) and it exposes `get`, `bulk_get`, `fetch`, `bulk_fetch`, `stealthy_fetch`, and `bulk_stealthy_fetch` as callable tools.

## Where to Next
| I want to... | Go to |
|:---|:---|
| Understand selectors in depth | [Querying elements](parsing/selection.md) |
| Compare fetchers | [Choosing a fetcher](fetching/choosing.md) |
| Build a production crawler | [Spiders: getting started](spiders/getting-started.md) |
| Use it from the terminal | [CLI overview](cli/overview.md) |
| Hook it up to an AI agent | [MCP server guide](ai/mcp-server.md) |
