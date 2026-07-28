"""Tests for PageAnalyzer / PageMetadata."""

from whispercrawler.core.analyzer import PageAnalyzer, PageMetadata
from whispercrawler.parser import Selector


def _analyzer(html: str) -> PageAnalyzer:
    return PageAnalyzer(Selector(content=html))


class TestPageMetadataDefaults:
    def test_keywords_defaults_to_empty_list(self):
        """`keywords` is annotated `list[str]`, so the default must be a list.

        A bare `PageMetadata()` used to hand back None, so any caller iterating
        `metadata.keywords` hit a TypeError.
        """
        assert PageMetadata().keywords == []

    def test_keywords_default_is_not_shared_between_instances(self):
        first = PageMetadata()
        first.keywords.append("leaked")

        assert PageMetadata().keywords == []

    def test_to_dict_reports_empty_keywords(self):
        assert PageMetadata().to_dict()["keywords"] == []


class TestAnalyzeKeywords:
    def test_parses_and_strips_comma_separated_keywords(self):
        meta = _analyzer(
            '<html><head><meta name="keywords" content="one, two ,three"></head></html>'
        ).analyze()

        assert meta.keywords == ["one", "two", "three"]

    def test_missing_keywords_yields_empty_list(self):
        meta = _analyzer("<html><head></head></html>").analyze()

        assert meta.keywords == []


class TestAnalyzeFields:
    def test_extracts_title_and_description(self):
        meta = _analyzer(
            "<html><head><title>Hello</title>"
            '<meta name="description" content="A page"></head></html>'
        ).analyze()

        assert meta.title == "Hello"
        assert meta.description == "A page"

    def test_falls_back_to_meta_title_when_no_title_tag(self):
        meta = _analyzer(
            '<html><head><meta name="title" content="Meta Title"></head></html>'
        ).analyze()

        assert meta.title == "Meta Title"

    def test_extracts_opengraph_and_twitter(self):
        meta = _analyzer(
            "<html><head>"
            '<meta property="og:title" content="OG Title">'
            '<meta property="og:site_name" content="Example">'
            '<meta name="twitter:card" content="summary">'
            "</head></html>"
        ).analyze()

        assert meta.og_title == "OG Title"
        assert meta.og_site_name == "Example"
        assert meta.twitter_card == "summary"

    def test_extracts_canonical_and_charset(self):
        meta = _analyzer(
            '<html><head><link rel="canonical" href="https://example.com/x">'
            '<meta charset="utf-8"></head></html>'
        ).analyze()

        assert meta.canonical_url == "https://example.com/x"
        assert meta.charset == "utf-8"

    def test_absent_fields_are_none(self):
        meta = _analyzer("<html><head></head></html>").analyze()

        assert meta.title is None
        assert meta.og_image is None
        assert meta.robots is None


class TestSummary:
    def test_summary_lists_present_fields(self):
        summary = _analyzer(
            "<html><head><title>Hello</title>"
            '<meta property="og:site_name" content="Example"></head></html>'
        ).summary()

        assert "Title: Hello" in summary
        assert "Site: Example" in summary

    def test_summary_when_nothing_present(self):
        assert _analyzer("<html><head></head></html>").summary() == (
            "No significant metadata found."
        )
