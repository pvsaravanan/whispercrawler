"""Tests for automatic next-page detection."""

from whispercrawler.parser import Selector


def _page(body: str, url: str = "https://example.com/list?page=2") -> Selector:
    return Selector(content=f"<html><body>{body}</body></html>", url=url)


class TestNextPageTextMatching:
    def test_rel_next_wins(self):
        page = _page('<link rel="next" href="/list?page=3">')

        assert page.next_page == "https://example.com/list?page=3"

    def test_next_word_link(self):
        page = _page('<a href="/list?page=3">Next</a>')

        assert page.next_page == "https://example.com/list?page=3"

    def test_chevron_link_still_detected(self):
        page = _page('<a href="/list?page=3">&gt;</a>')

        assert page.next_page == "https://example.com/list?page=3"

    def test_guillemet_link_still_detected(self):
        page = _page('<a href="/list?page=3">»</a>')

        assert page.next_page == "https://example.com/list?page=3"

    def test_prose_containing_chevron_is_not_a_next_link(self):
        """Regression: any link text merely containing '>' was read as Next."""
        page = _page('<a href="/cpp-guide">C++ &gt; Learn more</a><a href="/list?page=3">Next</a>')

        assert page.next_page == "https://example.com/list?page=3"

    def test_prose_chevron_alone_yields_no_next_page(self):
        page = _page('<a href="/cpp-guide">C++ &gt; Learn more</a>')

        assert page.next_page is None

    def test_breadcrumb_is_not_a_next_link(self):
        page = _page('<a href="/docs">Docs &gt; API &gt; Reference</a>')

        assert page.next_page is None

    def test_german_next_link_detected(self):
        """The German pattern was mojibake and never matched."""
        page = _page('<a href="/list?page=3">Nächste</a>')

        assert page.next_page == "https://example.com/list?page=3"

    def test_no_pagination_returns_none(self):
        page = _page("<p>nothing here</p>")

        assert page.next_page is None
