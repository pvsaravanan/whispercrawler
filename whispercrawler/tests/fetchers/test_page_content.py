"""Tests for the page.content() retry workaround."""

import pytest
from playwright._impl._errors import Error as PlaywrightError

from whispercrawler.engines.toolbelt.convertor import ResponseFactory


class FlakyPage:
    """Fails `failures` times before returning content."""

    def __init__(self, failures: int, content: str = "<html>ok</html>"):
        self._remaining = failures
        self._content = content
        self.waits = 0

    def content(self):
        if self._remaining > 0:
            self._remaining -= 1
            raise PlaywrightError("Unable to retrieve content because the page is navigating")
        return self._content

    def wait_for_timeout(self, _ms):
        self.waits += 1


class AsyncFlakyPage(FlakyPage):
    async def content(self):  # type: ignore[override]
        return FlakyPage.content(self)

    async def wait_for_timeout(self, _ms):  # type: ignore[override]
        self.waits += 1


class TestGetPageContent:
    def test_returns_content_immediately(self):
        page = FlakyPage(failures=0)

        assert ResponseFactory._get_page_content(page) == "<html>ok</html>"
        assert page.waits == 0

    def test_retries_transient_failures(self):
        page = FlakyPage(failures=3)

        assert ResponseFactory._get_page_content(page) == "<html>ok</html>"
        assert page.waits == 3

    def test_gives_up_on_permanently_broken_page(self):
        """Regression: a crashed page used to hang this loop forever."""
        page = FlakyPage(failures=10_000)

        with pytest.raises(PlaywrightError):
            ResponseFactory._get_page_content(page)

        # Bounded, not unbounded
        assert page.waits < 100


class TestGetAsyncPageContent:
    @pytest.mark.asyncio
    async def test_returns_content_immediately(self):
        page = AsyncFlakyPage(failures=0)

        assert await ResponseFactory._get_async_page_content(page) == "<html>ok</html>"

    @pytest.mark.asyncio
    async def test_retries_transient_failures(self):
        page = AsyncFlakyPage(failures=3)

        assert await ResponseFactory._get_async_page_content(page) == "<html>ok</html>"
        assert page.waits == 3

    @pytest.mark.asyncio
    async def test_gives_up_on_permanently_broken_page(self):
        """Regression: a crashed page used to hang this loop forever."""
        page = AsyncFlakyPage(failures=10_000)

        with pytest.raises(PlaywrightError):
            await ResponseFactory._get_async_page_content(page)

        assert page.waits < 100
