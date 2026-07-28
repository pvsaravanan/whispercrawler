from unittest.mock import AsyncMock, Mock

import pytest

from whispercrawler.engines._browsers._base import AsyncSession, SyncSession
from whispercrawler.engines._browsers._page import PageInfo, PagePool


class TestPageInfo:
    """Test PageInfo functionality"""

    def test_page_info_creation(self):
        """Test PageInfo creation"""
        mock_page = Mock()
        page_info = PageInfo(mock_page, "ready", "https://example.com")

        assert page_info.page == mock_page
        assert page_info.state == "ready"
        assert page_info.url == "https://example.com"

    def test_page_info_marking(self):
        """Test marking page"""
        mock_page = Mock()
        page_info = PageInfo(mock_page, "ready", None)

        page_info.mark_busy("https://example.com")
        assert page_info.state == "busy"
        assert page_info.url == "https://example.com"

        page_info.mark_error()
        assert page_info.state == "error"

    def test_page_info_equality(self):
        """Test PageInfo equality comparison"""
        mock_page1 = Mock()
        mock_page2 = Mock()

        page_info1 = PageInfo(mock_page1, "ready", None)
        page_info2 = PageInfo(mock_page1, "busy", None)  # Same page, different state
        page_info3 = PageInfo(mock_page2, "ready", None)  # Different page

        assert page_info1 == page_info2  # Same page
        assert page_info1 != page_info3  # Different page
        assert page_info1 != "not a page info"  # Different type

    def test_page_info_repr(self):
        """Test PageInfo string representation"""
        mock_page = Mock()
        page_info = PageInfo(mock_page, "ready", "https://example.com")

        repr_str = repr(page_info)
        assert "ready" in repr_str
        assert "https://example.com" in repr_str


class TestPagePool:
    """Test PagePool functionality"""

    def test_page_pool_creation(self):
        """Test PagePool creation"""
        pool = PagePool(max_pages=5)

        assert pool.max_pages == 5
        assert pool.pages_count == 0
        assert pool.busy_count == 0

    def test_add_page(self):
        """Test adding page to pool"""
        pool = PagePool(max_pages=2)
        mock_page = Mock()

        page_info = pool.add_page(mock_page)

        assert isinstance(page_info, PageInfo)
        assert page_info.page == mock_page
        assert page_info.state == "ready"
        assert pool.pages_count == 1

    def test_add_page_limit_exceeded(self):
        """Test adding page when limit exceeded"""
        pool = PagePool(max_pages=1)

        # Add first page
        pool.add_page(Mock())

        # Try to add a second page
        with pytest.raises(RuntimeError):
            pool.add_page(Mock())

    def test_cleanup_error_pages(self):
        """Test cleaning up error pages"""
        pool = PagePool(max_pages=3)

        # Add pages
        page1 = pool.add_page(Mock())
        _ = pool.add_page(Mock())
        page3 = pool.add_page(Mock())

        # Mark some as error
        page1.mark_error()
        page3.mark_error()

        assert pool.pages_count == 3

        pool.cleanup_error_pages()

        assert pool.pages_count == 1  # Only 2 should remain


class _StubSyncSession(SyncSession):
    """SyncSession with the browser/context layer stubbed out."""

    def __init__(self, max_pages: int = 1):
        super().__init__(max_pages=max_pages)
        self._config = Mock(init_script=None, cookies=None)
        self._context_options = {}
        self.browser = Mock()
        self.closed_contexts: list = []

        def _new_context(**kwargs):
            ctx = Mock()
            ctx.new_page.return_value = Mock()
            ctx.close.side_effect = lambda: self.closed_contexts.append(ctx)
            return ctx

        self.browser.new_context.side_effect = _new_context

    def _build_context_with_proxy(self, proxy=None):
        return {}


class _StubAsyncSession(AsyncSession):
    """AsyncSession with the browser/context layer stubbed out."""

    def __init__(self, max_pages: int = 1):
        super().__init__(max_pages=max_pages)
        self._config = Mock(init_script=None, cookies=None)
        self._context_options = {}
        self.browser = Mock()
        self.closed_contexts: list = []

        async def _new_context(**kwargs):
            ctx = Mock()
            ctx.new_page = AsyncMock(return_value=Mock())
            ctx.close = AsyncMock(side_effect=lambda: self.closed_contexts.append(ctx))
            return ctx

        self.browser.new_context = _new_context

    def _build_context_with_proxy(self, proxy=None):
        return {}

    async def _initialize_context(self, config, ctx):
        return ctx


class TestPageGeneratorProxyRotation:
    """Pages acquired in proxy-rotation mode must be released from the pool."""

    def test_sync_proxy_mode_releases_page_from_pool(self):
        session = _StubSyncSession(max_pages=1)

        with session._page_generator(1000, None, False, proxy="http://p:8080"):
            assert session.page_pool.pages_count == 1

        assert session.page_pool.pages_count == 0

    def test_sync_proxy_mode_allows_repeated_fetches(self):
        """Regression: the pool used to fill up permanently after the first request."""
        session = _StubSyncSession(max_pages=1)

        for _ in range(3):
            with session._page_generator(1000, None, False, proxy="http://p:8080"):
                pass

        assert session.page_pool.pages_count == 0
        assert len(session.closed_contexts) == 3

    def test_sync_proxy_mode_releases_page_on_exception(self):
        session = _StubSyncSession(max_pages=1)

        with pytest.raises(ValueError):
            with session._page_generator(1000, None, False, proxy="http://p:8080"):
                raise ValueError("boom")

        assert session.page_pool.pages_count == 0

    @pytest.mark.asyncio
    async def test_async_proxy_mode_releases_page_from_pool(self):
        session = _StubAsyncSession(max_pages=1)

        async with session._page_generator(1000, None, False, proxy="http://p:8080"):
            assert session.page_pool.pages_count == 1

        assert session.page_pool.pages_count == 0

    @pytest.mark.asyncio
    async def test_async_proxy_mode_allows_repeated_fetches(self):
        """Regression: the pool used to fill up permanently after the first request."""
        session = _StubAsyncSession(max_pages=1)

        for _ in range(3):
            async with session._page_generator(1000, None, False, proxy="http://p:8080"):
                pass

        assert session.page_pool.pages_count == 0
        assert len(session.closed_contexts) == 3

    @pytest.mark.asyncio
    async def test_async_proxy_mode_releases_page_on_exception(self):
        session = _StubAsyncSession(max_pages=1)

        with pytest.raises(ValueError):
            async with session._page_generator(1000, None, False, proxy="http://p:8080"):
                raise ValueError("boom")

        assert session.page_pool.pages_count == 0


class TestSessionCloseResilience:
    """A failure in one cleanup step must not strand the rest."""

    def _sync_session(self):
        session = _StubSyncSession(max_pages=1)
        session._is_alive = True
        session.context = Mock()
        session.browser = Mock()
        session.playwright = Mock()
        return session

    def test_sync_close_releases_everything(self):
        session = self._sync_session()

        session.close()

        assert session._is_alive is False
        assert session.context is None
        assert session.browser is None
        assert session.playwright is None

    def test_sync_close_continues_after_context_failure(self):
        """Regression: a raising context.close() used to leak the browser process."""
        session = self._sync_session()
        context, browser, playwright = session.context, session.browser, session.playwright
        context.close.side_effect = RuntimeError("browser already died")

        session.close()

        browser.close.assert_called_once()
        playwright.stop.assert_called_once()
        assert session._is_alive is False

    def test_sync_close_continues_after_browser_failure(self):
        session = self._sync_session()
        playwright = session.playwright
        session.browser.close.side_effect = RuntimeError("browser already died")

        session.close()

        playwright.stop.assert_called_once()
        assert session._is_alive is False

    def test_sync_close_survives_playwright_failure(self):
        session = self._sync_session()
        session.playwright.stop.side_effect = RuntimeError("driver gone")

        session.close()

        assert session._is_alive is False

    async def _async_session(self):
        session = _StubAsyncSession(max_pages=1)
        session._is_alive = True
        session.context = Mock(close=AsyncMock())
        session.browser = Mock(close=AsyncMock())
        session.playwright = Mock(stop=AsyncMock())
        return session

    @pytest.mark.asyncio
    async def test_async_close_releases_everything(self):
        session = await self._async_session()

        await session.close()

        assert session._is_alive is False
        assert session.context is None
        assert session.browser is None
        assert session.playwright is None

    @pytest.mark.asyncio
    async def test_async_close_continues_after_context_failure(self):
        """Regression: a raising context.close() used to leak the browser process."""
        session = await self._async_session()
        browser, playwright = session.browser, session.playwright
        session.context.close.side_effect = RuntimeError("browser already died")

        await session.close()

        browser.close.assert_awaited_once()
        playwright.stop.assert_awaited_once()
        assert session._is_alive is False

    @pytest.mark.asyncio
    async def test_async_close_continues_after_browser_failure(self):
        session = await self._async_session()
        playwright = session.playwright
        session.browser.close.side_effect = RuntimeError("browser already died")

        await session.close()

        playwright.stop.assert_awaited_once()
        assert session._is_alive is False
