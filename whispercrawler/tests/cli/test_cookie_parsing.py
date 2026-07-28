"""Cookie string handling in the `extract` CLI commands."""

import logging

from whispercrawler import cli

# Module-level double-underscore names are not name-mangled, but referencing them
# from inside a class body would be, so bind it once here.
_parse_extract_arguments = getattr(cli, "_ParseExtractArguments", None) or getattr(
    cli, "__ParseExtractArguments"
)


class TestCookieParsing:
    def test_valid_cookies_are_parsed(self):
        _, cookies, _, _ = _parse_extract_arguments([], "session=abc123; user=bob", ())

        assert cookies == {"session": "abc123", "user": "bob"}

    def test_empty_cookie_string_is_silent(self, caplog):
        with caplog.at_level(logging.WARNING):
            _, cookies, _, _ = _parse_extract_arguments([], "", ())

        assert cookies == {}
        assert not caplog.records

    def test_malformed_cookie_string_warns_instead_of_silently_dropping(self, caplog):
        """Regression: one bad pair makes SimpleCookie discard the whole string.

        `--cookies "session=abc123; =oops"` used to send the request with no
        cookies at all and no diagnostic, which is indistinguishable from a
        server-side auth failure.
        """
        with caplog.at_level(logging.WARNING):
            _, cookies, _, _ = _parse_extract_arguments([], "session=abc123; =oops", ())

        assert cookies == {}
        assert any("cookie" in record.message.lower() for record in caplog.records)
