"""Tests for the Scrapy @whisper_response integration proxy."""

import pytest

from whispercrawler.integrations.scrapy import WhisperResponse, whisper_response

HTML = "<html><body><h1>Title</h1><p class='x'>Body text</p></body></html>"


class FakeScrapyResponse:
    """Stand-in for scrapy.http.Response."""

    def __init__(self, text: str = HTML, url: str = "https://example.com"):
        self.text = text
        self.body = text.encode()
        self.url = url
        self.encoding = "utf-8"
        self.status = 200
        self.headers = {"Content-Type": "text/html"}
        self.meta = {"depth": 1}

    def urljoin(self, url: str) -> str:
        return f"{self.url}/{url.lstrip('/')}"

    def follow(self, url: str, **kwargs):
        return ("followed", url)


class TestResponseAttributesNotShadowed:
    """Response-level attributes must come from the Scrapy response, not the Selector."""

    def test_text_returns_raw_html(self):
        """Regression: Selector.text returned the root's own text node instead."""
        response = WhisperResponse(FakeScrapyResponse())

        assert response.text == HTML

    def test_body_returns_raw_bytes(self):
        response = WhisperResponse(FakeScrapyResponse())

        assert response.body == HTML.encode()

    def test_url_comes_from_response(self):
        response = WhisperResponse(FakeScrapyResponse())

        assert response.url == "https://example.com"

    def test_status_and_headers_pass_through(self):
        response = WhisperResponse(FakeScrapyResponse())

        assert response.status == 200
        assert response.headers["Content-Type"] == "text/html"

    def test_meta_passes_through(self):
        response = WhisperResponse(FakeScrapyResponse())

        assert response.meta == {"depth": 1}


class TestSelectorFeaturesStillReachable:
    def test_css_uses_whisper_selector(self):
        response = WhisperResponse(FakeScrapyResponse())

        assert response.css("h1::text").get() == "Title"

    def test_selector_property_exposed(self):
        response = WhisperResponse(FakeScrapyResponse())

        assert response.selector.css("p.x::text").get() == "Body text"

    def test_selector_only_helper_still_proxied(self):
        """Names that exist only on the Selector must still resolve to it."""
        response = WhisperResponse(FakeScrapyResponse())

        assert callable(response.find_by_text)

    def test_urljoin_and_follow_forward_to_response(self):
        response = WhisperResponse(FakeScrapyResponse())

        assert response.urljoin("/page") == "https://example.com/page"
        assert response.follow("/next") == ("followed", "/next")

    def test_unknown_attribute_raises(self):
        response = WhisperResponse(FakeScrapyResponse())

        with pytest.raises(AttributeError):
            _ = response.definitely_not_a_real_attribute


class TestDecorator:
    def test_decorator_wraps_response(self):
        captured = {}

        @whisper_response
        def parse(self, response):
            captured["type"] = type(response)
            captured["text"] = response.text
            return "done"

        result = parse(None, FakeScrapyResponse())

        assert result == "done"
        assert captured["type"] is WhisperResponse
        assert captured["text"] == HTML
