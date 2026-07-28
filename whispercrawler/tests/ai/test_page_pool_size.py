"""The browser page pool for bulk MCP tools is bounded by the session validator."""

import pytest

from whispercrawler.core.ai import _page_pool_size
from whispercrawler.fetchers import AsyncDynamicSession

# Mirrors `PagesCount = Annotated[int, Meta(ge=1, le=50)]` in _browsers/_validators.py
MIN_PAGES, MAX_PAGES = 1, 50


class TestPagePoolSize:
    """Regression: `max_pages=len(urls)` raised TypeError for 0 or >50 URLs.

    `bulk_fetch` is exposed to AI agents, so an oversized batch used to fail with
    "Invalid argument type: Expected `int` <= 50" before a single page was fetched.
    """

    def test_matches_url_count_within_bounds(self):
        assert _page_pool_size(1) == 1
        assert _page_pool_size(7) == 7
        assert _page_pool_size(50) == 50

    def test_empty_batch_clamps_to_minimum(self):
        assert _page_pool_size(0) == MIN_PAGES

    def test_oversized_batch_clamps_to_maximum(self):
        assert _page_pool_size(51) == MAX_PAGES
        assert _page_pool_size(500) == MAX_PAGES

    @pytest.mark.parametrize("count", [0, 1, 7, 50, 51, 500])
    def test_result_is_always_accepted_by_the_session(self, count):
        """The real validator must accept whatever this returns, for any batch size."""
        session = AsyncDynamicSession(max_pages=_page_pool_size(count))

        assert MIN_PAGES <= session._config.max_pages <= MAX_PAGES
