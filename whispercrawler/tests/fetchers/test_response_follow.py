"""Tests for Response.follow()'s handling of inherited session kwargs."""

import pytest

from whispercrawler.engines.toolbelt.custom import Response
from whispercrawler.spiders.request import Request


def _response(request: Request) -> Response:
    response = Response(
        url="https://example.com/page",
        content="<html><body><a href='/next'>n</a></body></html>",
        status=200,
        reason="OK",
        cookies={},
        headers={},
        request_headers={},
    )
    response.request = request
    return response


class TestFollowDoesNotMutateOriginal:
    def test_original_headers_untouched(self):
        """Regression: follow() set referer on the *original* request's dict."""
        original = Request("https://example.com/page", headers={"accept": "text/html"})
        response = _response(original)

        response.follow("/next")

        assert "referer" not in original._session_kwargs["headers"]

    def test_original_extra_headers_untouched(self):
        original = Request("https://example.com/page", extra_headers={"x-a": "1"})
        response = _response(original)

        response.follow("/next")

        assert "referer" not in original._session_kwargs["extra_headers"]

    def test_new_request_gets_referer(self):
        original = Request("https://example.com/page", headers={"accept": "text/html"})
        response = _response(original)

        followed = response.follow("/next")

        assert followed._session_kwargs["headers"]["referer"] == "https://example.com/page"

    def test_inherited_headers_are_preserved(self):
        original = Request("https://example.com/page", headers={"accept": "text/html"})
        response = _response(original)

        followed = response.follow("/next")

        assert followed._session_kwargs["headers"]["accept"] == "text/html"

    def test_two_follows_do_not_share_header_dicts(self):
        original = Request("https://example.com/page", headers={"accept": "text/html"})
        response = _response(original)

        first = response.follow("/a")
        second = response.follow("/b")

        assert first._session_kwargs["headers"] is not second._session_kwargs["headers"]
        assert first._session_kwargs["headers"] is not original._session_kwargs["headers"]

    def test_referer_flow_disabled_leaves_headers_alone(self):
        original = Request("https://example.com/page", headers={"accept": "text/html"})
        response = _response(original)

        followed = response.follow("/next", referer_flow=False)

        assert "referer" not in followed._session_kwargs.get("headers", {})
        assert "referer" not in original._session_kwargs["headers"]

    def test_explicit_kwargs_override_inherited(self):
        original = Request("https://example.com/page", headers={"accept": "text/html"})
        response = _response(original)

        followed = response.follow("/next", headers={"accept": "application/json"})

        assert followed._session_kwargs["headers"]["accept"] == "application/json"
        assert original._session_kwargs["headers"]["accept"] == "text/html"

    def test_requires_a_request(self):
        response = Response(
            url="https://example.com/page",
            content="<html></html>",
            status=200,
            reason="OK",
            cookies={},
            headers={},
            request_headers={},
        )

        with pytest.raises(TypeError):
            response.follow("/next")
