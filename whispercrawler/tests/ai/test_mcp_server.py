"""Tests for the stdio MCP server's tool dispatch layer."""

import pytest

from whispercrawler import mcp_server
from whispercrawler.mcp_server import CrawlResult, dispatch_tool


def _ok(url: str = "https://example.com") -> CrawlResult:
    return CrawlResult(
        url=url,
        status_code=200,
        title="Example",
        text="hello",
        selected=[],
        html_length=42,
        elapsed_ms=1.0,
    )


def _response(status: int = 200, content: str = "<html><title>Example</title><p>hi</p></html>"):
    """A real Response, so _extract_result is tested against the actual attributes."""
    from whispercrawler.engines.toolbelt.custom import Response

    return Response(
        url="https://example.com",
        content=content,
        status=status,
        reason="OK",
        cookies={},
        headers={},
        request_headers={},
    )


class TestExtractResult:
    """_extract_result reads a real Response; a wrong attribute name here turns every
    tool call into a silent `error` payload rather than a visible crash."""

    def test_reads_status_from_response(self):
        """Regression: read page.status_code, but Response exposes .status."""
        result = mcp_server._extract_result(_response(status=418), "https://example.com")

        assert result.status_code == 418

    def test_extracts_title_and_text(self):
        result = mcp_server._extract_result(_response(), "https://example.com")

        assert result.title == "Example"
        assert "hi" in result.text
        assert result.error is None

    def test_css_selection(self):
        result = mcp_server._extract_result(
            _response(content="<html><body><p>one</p><p>two</p></body></html>"),
            "https://example.com",
            css="p",
        )

        assert result.selected == ["one", "two"]


class TestDispatchMissingArguments:
    """A malformed tool call must return an error payload, never raise."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tool", ["crawl", "ghost_crawl", "shadow_crawl"])
    async def test_missing_url_returns_error(self, tool):
        result = await dispatch_tool(tool, {})

        assert isinstance(result, dict)
        assert "url" in result["error"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tool", ["bulk_crawl", "bulk_ghost_crawl", "bulk_shadow_crawl"])
    async def test_missing_urls_returns_error(self, tool):
        result = await dispatch_tool(tool, {})

        assert isinstance(result, dict)
        assert "urls" in result["error"]

    @pytest.mark.asyncio
    async def test_none_arguments_returns_error(self):
        result = await dispatch_tool("crawl", None)

        assert isinstance(result, dict)
        assert result["error"]

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        result = await dispatch_tool("does_not_exist", {"url": "https://example.com"})

        assert isinstance(result, dict)
        assert "does_not_exist" in result["error"]

    @pytest.mark.asyncio
    async def test_bulk_rejects_string_instead_of_list(self, monkeypatch):
        """A bare string must not be iterated character-by-character into N crawls."""
        calls = []

        async def fake_crawl(url, css="", xpath=""):
            calls.append(url)
            return _ok(url)

        monkeypatch.setattr(mcp_server, "crawl", fake_crawl)

        result = await dispatch_tool("bulk_crawl", {"urls": "https://example.com"})

        assert isinstance(result, dict)
        assert result["error"]
        assert calls == []


class TestDispatchHandlerFailure:
    @pytest.mark.asyncio
    async def test_handler_exception_returns_error(self, monkeypatch):
        async def exploding_crawl(url, css="", xpath=""):
            raise RuntimeError("handler exploded")

        monkeypatch.setattr(mcp_server, "crawl", exploding_crawl)

        result = await dispatch_tool("crawl", {"url": "https://example.com"})

        assert isinstance(result, dict)
        assert "handler exploded" in result["error"]


class TestDispatchSuccess:
    @pytest.mark.asyncio
    async def test_single_result_serialised(self, monkeypatch):
        async def fake_crawl(url, css="", xpath=""):
            return _ok(url)

        monkeypatch.setattr(mcp_server, "crawl", fake_crawl)

        result = await dispatch_tool("crawl", {"url": "https://example.com"})

        assert result["url"] == "https://example.com"
        assert result["status_code"] == 200
        assert result["title"] == "Example"
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_bulk_result_serialised_as_list(self, monkeypatch):
        async def fake_crawl(url, css="", xpath=""):
            return _ok(url)

        monkeypatch.setattr(mcp_server, "crawl", fake_crawl)

        urls = ["https://a.com", "https://b.com"]
        result = await dispatch_tool("bulk_crawl", {"urls": urls})

        assert isinstance(result, list)
        assert [r["url"] for r in result] == urls

    @pytest.mark.asyncio
    async def test_text_is_truncated(self, monkeypatch):
        async def fake_crawl(url, css="", xpath=""):
            res = _ok(url)
            res.text = "x" * 10_000
            return res

        monkeypatch.setattr(mcp_server, "crawl", fake_crawl)

        result = await dispatch_tool("crawl", {"url": "https://example.com"})

        assert len(result["text"]) == 5000


class TestBulkConcurrencyCap:
    """Each browser crawl spawns a real browser, so bulk fan-out must be bounded."""

    @staticmethod
    def _tracking_crawl(peak: dict, delay: float = 0.01):
        import asyncio

        state = {"live": 0}

        async def crawl_one(url, css="", xpath="", *args, **kwargs):
            state["live"] += 1
            peak["max"] = max(peak.get("max", 0), state["live"])
            try:
                await asyncio.sleep(delay)
                return _ok(url)
            finally:
                state["live"] -= 1

        return crawl_one

    @pytest.mark.asyncio
    async def test_bulk_ghost_crawl_caps_browsers(self, monkeypatch):
        """Regression: 50 URLs used to launch 50 concurrent browsers."""
        peak: dict = {}
        monkeypatch.setattr(mcp_server, "ghost_crawl", self._tracking_crawl(peak))

        urls = [f"https://example.com/{i}" for i in range(20)]
        results = await mcp_server.bulk_ghost_crawl(urls)

        assert len(results) == 20
        assert peak["max"] <= mcp_server.DEFAULT_BROWSER_CONCURRENCY

    @pytest.mark.asyncio
    async def test_bulk_shadow_crawl_caps_browsers(self, monkeypatch):
        peak: dict = {}
        monkeypatch.setattr(mcp_server, "shadow_crawl", self._tracking_crawl(peak))

        urls = [f"https://example.com/{i}" for i in range(20)]
        results = await mcp_server.bulk_shadow_crawl(urls)

        assert len(results) == 20
        assert peak["max"] <= mcp_server.DEFAULT_BROWSER_CONCURRENCY

    @pytest.mark.asyncio
    async def test_cap_is_configurable(self, monkeypatch):
        peak: dict = {}
        monkeypatch.setattr(mcp_server, "ghost_crawl", self._tracking_crawl(peak))

        urls = [f"https://example.com/{i}" for i in range(10)]
        await mcp_server.bulk_ghost_crawl(urls, max_concurrent=1)

        assert peak["max"] == 1

    @pytest.mark.asyncio
    async def test_results_stay_in_input_order(self, monkeypatch):
        """A bounded runner must not reorder results."""
        import asyncio
        import random

        async def jittery(url, css="", xpath="", *args, **kwargs):
            await asyncio.sleep(random.uniform(0, 0.01))
            return _ok(url)

        monkeypatch.setattr(mcp_server, "ghost_crawl", jittery)

        urls = [f"https://example.com/{i}" for i in range(12)]
        results = await mcp_server.bulk_ghost_crawl(urls)

        assert [r.url for r in results] == urls

    @pytest.mark.asyncio
    async def test_static_bulk_crawl_still_unbounded(self, monkeypatch):
        """Static HTTP is cheap - it keeps its full fan-out."""
        peak: dict = {}
        monkeypatch.setattr(mcp_server, "crawl", self._tracking_crawl(peak))

        urls = [f"https://example.com/{i}" for i in range(10)]
        await mcp_server.bulk_crawl(urls)

        assert peak["max"] > mcp_server.DEFAULT_BROWSER_CONCURRENCY
