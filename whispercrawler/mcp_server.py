# MIT License
#
# Copyright (c) 2026, Saravanan P V
#
#
# This project is licensed under the MIT License. See the [LICENSE](https://github.com/WhisperCrawl/WhisperCrawler/blob/main/LICENSE) file for details.

"""MCP server — expose six scraping tools for AI agent use."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("whispercrawler.mcp")


@dataclass
class CrawlResult:
    """Standardised output from all MCP tools."""

    url: str
    status_code: int
    title: str
    text: str
    selected: list[str] = field(default_factory=list)
    html_length: int = 0
    elapsed_ms: float = 0.0
    error: str | None = None


def _extract_result(
    page: Any,
    url: str,
    css: str = "",
    xpath: str = "",
    elapsed_ms: float = 0.0,
) -> CrawlResult:
    """Build CrawlResult from a Page object."""
    title_el = page.css_first("title")
    title = str(title_el.text) if title_el else ""
    text = str(page.get_all_text())[:50000]
    html_len = len(str(page.html_content))

    selected: list[str] = []
    if css:
        matches = page.css(css)
        selected.extend(str(m.text) if hasattr(m, "text") else str(m) for m in matches)
    if xpath:
        matches = page.xpath(xpath)
        selected.extend(str(m.text) if hasattr(m, "text") else str(m) for m in matches)

    return CrawlResult(
        url=url,
        status_code=page.status_code,
        title=title,
        text=text,
        selected=selected,
        html_length=html_len,
        elapsed_ms=elapsed_ms,
    )


async def crawl(url: str, css: str = "", xpath: str = "") -> CrawlResult:
    """Fetch URL using Crawler (static HTTP). Optionally extract elements."""
    from whispercrawler.fetchers import Fetcher as Crawler

    start = time.monotonic()
    try:
        page = await asyncio.get_event_loop().run_in_executor(None, lambda: Crawler.get(url))
        elapsed = (time.monotonic() - start) * 1000
        return _extract_result(page, url, css, xpath, elapsed)
    except Exception as exc:
        elapsed = (time.monotonic() - start) * 1000
        return CrawlResult(
            url=url,
            status_code=0,
            title="",
            text="",
            elapsed_ms=elapsed,
            error=str(exc),
        )


async def bulk_crawl(urls: list[str], css: str = "", xpath: str = "") -> list[CrawlResult]:
    """Fetch multiple URLs concurrently using Crawler."""
    tasks = [crawl(url, css, xpath) for url in urls]
    return list(await asyncio.gather(*tasks))


async def ghost_crawl(
    url: str, css: str = "", xpath: str = "", headless: bool = True
) -> CrawlResult:
    """Fetch URL using GhostCrawler (Playwright/Patchright Chromium)."""
    from whispercrawler.fetchers import DynamicFetcher as AsyncGhostCrawler

    start = time.monotonic()
    try:
        page = await AsyncGhostCrawler.async_fetch(url, headless=headless)
        elapsed = (time.monotonic() - start) * 1000
        return _extract_result(page, url, css, xpath, elapsed)
    except Exception as exc:
        elapsed = (time.monotonic() - start) * 1000
        return CrawlResult(
            url=url,
            status_code=0,
            title="",
            text="",
            elapsed_ms=elapsed,
            error=str(exc),
        )


async def bulk_ghost_crawl(urls: list[str], css: str = "", xpath: str = "") -> list[CrawlResult]:
    """Fetch multiple URLs concurrently using GhostCrawler."""
    tasks = [ghost_crawl(url, css, xpath) for url in urls]
    return list(await asyncio.gather(*tasks))


async def shadow_crawl(
    url: str, css: str = "", xpath: str = "", headless: bool = True
) -> CrawlResult:
    """Fetch URL using ShadowCrawler (Camoufox — anti-Cloudflare)."""
    from whispercrawler.fetchers import ShadowFetcher as AsyncShadowCrawler

    start = time.monotonic()
    try:
        page = await AsyncShadowCrawler.async_fetch(url, headless=headless)
        elapsed = (time.monotonic() - start) * 1000
        return _extract_result(page, url, css, xpath, elapsed)
    except Exception as exc:
        elapsed = (time.monotonic() - start) * 1000
        return CrawlResult(
            url=url,
            status_code=0,
            title="",
            text="",
            elapsed_ms=elapsed,
            error=str(exc),
        )


async def bulk_shadow_crawl(urls: list[str], css: str = "", xpath: str = "") -> list[CrawlResult]:
    """Fetch multiple URLs concurrently using ShadowCrawler."""
    tasks = [shadow_crawl(url, css, xpath) for url in urls]
    return list(await asyncio.gather(*tasks))


def main() -> None:
    """Start the MCP server via stdio."""
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import TextContent, Tool
    except ImportError:
        logger.error("MCP package not installed. Install with: pip install 'whispercrawler[mcp]'")
        return

    import orjson

    server = Server("whispercrawler")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available MCP tools."""
        return [
            Tool(
                name="crawl",
                description="Fetch URL using static HTTP (fastest). Optionally extract elements with CSS/XPath.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to fetch"},
                        "css": {
                            "type": "string",
                            "description": "CSS selector to extract",
                            "default": "",
                        },
                        "xpath": {
                            "type": "string",
                            "description": "XPath to extract",
                            "default": "",
                        },
                    },
                    "required": ["url"],
                },
            ),
            Tool(
                name="bulk_crawl",
                description="Fetch multiple URLs concurrently using static HTTP.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "URLs to fetch",
                        },
                        "css": {"type": "string", "default": ""},
                        "xpath": {"type": "string", "default": ""},
                    },
                    "required": ["urls"],
                },
            ),
            Tool(
                name="ghost_crawl",
                description="Fetch URL using Playwright Chromium (for JS-heavy pages).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "css": {"type": "string", "default": ""},
                        "xpath": {"type": "string", "default": ""},
                        "headless": {"type": "boolean", "default": True},
                    },
                    "required": ["url"],
                },
            ),
            Tool(
                name="bulk_ghost_crawl",
                description="Fetch multiple URLs concurrently using Playwright Chromium.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "urls": {"type": "array", "items": {"type": "string"}},
                        "css": {"type": "string", "default": ""},
                        "xpath": {"type": "string", "default": ""},
                    },
                    "required": ["urls"],
                },
            ),
            Tool(
                name="shadow_crawl",
                description="Fetch URL using Camoufox (anti-Cloudflare stealth browser).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "css": {"type": "string", "default": ""},
                        "xpath": {"type": "string", "default": ""},
                        "headless": {"type": "boolean", "default": True},
                    },
                    "required": ["url"],
                },
            ),
            Tool(
                name="bulk_shadow_crawl",
                description="Fetch multiple URLs concurrently using Camoufox.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "urls": {"type": "array", "items": {"type": "string"}},
                        "css": {"type": "string", "default": ""},
                        "xpath": {"type": "string", "default": ""},
                    },
                    "required": ["urls"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Dispatch tool calls."""
        handlers = {
            "crawl": lambda args: crawl(args["url"], args.get("css", ""), args.get("xpath", "")),
            "bulk_crawl": lambda args: bulk_crawl(
                args["urls"], args.get("css", ""), args.get("xpath", "")
            ),
            "ghost_crawl": lambda args: ghost_crawl(
                args["url"], args.get("css", ""), args.get("xpath", ""), args.get("headless", True)
            ),
            "bulk_ghost_crawl": lambda args: bulk_ghost_crawl(
                args["urls"], args.get("css", ""), args.get("xpath", "")
            ),
            "shadow_crawl": lambda args: shadow_crawl(
                args["url"], args.get("css", ""), args.get("xpath", ""), args.get("headless", True)
            ),
            "bulk_shadow_crawl": lambda args: bulk_shadow_crawl(
                args["urls"], args.get("css", ""), args.get("xpath", "")
            ),
        }

        handler = handlers.get(name)
        if handler is None:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        result = await handler(arguments)

        if isinstance(result, list):
            data = [
                {
                    "url": r.url,
                    "status_code": r.status_code,
                    "title": r.title,
                    "text": r.text[:5000],
                    "selected": r.selected,
                    "html_length": r.html_length,
                    "elapsed_ms": r.elapsed_ms,
                    "error": r.error,
                }
                for r in result
            ]
        else:
            data = {
                "url": result.url,
                "status_code": result.status_code,
                "title": result.title,
                "text": result.text[:5000],
                "selected": result.selected,
                "html_length": result.html_length,
                "elapsed_ms": result.elapsed_ms,
                "error": result.error,
            }

        return [
            TextContent(
                type="text",
                text=orjson.dumps(data, option=orjson.OPT_INDENT_2).decode(),
            )
        ]

    async def _run_server() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(_run_server())


if __name__ == "__main__":
    main()
