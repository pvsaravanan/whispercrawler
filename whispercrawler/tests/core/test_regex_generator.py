"""Tests for programmatic regex synthesis."""

import re

from whispercrawler.core.regex import RegexGenerator


def _matches(pattern: str, value: str) -> bool:
    return re.match(pattern, value) is not None


class TestIdenticalAndEmpty:
    def test_empty_list(self):
        assert RegexGenerator.generate([]) == ""

    def test_all_blank_entries(self):
        assert RegexGenerator.generate(["", "   ", None]) == ""  # type: ignore[list-item]

    def test_identical_strings(self):
        pattern = RegexGenerator.generate(["/a/b", "/a/b"])

        assert _matches(pattern, "/a/b")


class TestDigitGeneralization:
    """The \\d+ branch must actually fire - it silently never did."""

    def test_numeric_paths_produce_digit_class(self):
        pattern = RegexGenerator.generate(["/page-1.html", "/page-22.html", "/page-333.html"])

        assert r"\d+" in pattern

    def test_generated_pattern_matches_all_examples(self):
        examples = ["/page-1.html", "/page-22.html", "/page-333.html"]
        pattern = RegexGenerator.generate(examples)

        assert all(_matches(pattern, e) for e in examples)

    def test_generated_pattern_rejects_non_numeric(self):
        """Regression: the fallback branch produced `.*?` and matched anything."""
        pattern = RegexGenerator.generate(["/page-1.html", "/page-22.html", "/page-333.html"])

        assert not _matches(pattern, "/page-notanumber.html")

    def test_multiple_digit_groups(self):
        examples = ["/2024/01/post-1", "/2023/12/post-42"]
        pattern = RegexGenerator.generate(examples)

        assert all(_matches(pattern, e) for e in examples)

    def test_query_string_ids(self):
        examples = ["?id=1", "?id=99", "?id=1234"]
        pattern = RegexGenerator.generate(examples)

        assert all(_matches(pattern, e) for e in examples)
        assert not _matches(pattern, "?id=abc")


class TestPrefixSuffixFallback:
    def test_non_numeric_variation_still_produces_usable_pattern(self):
        examples = ["/shop/red-shirt", "/shop/blue-shirt"]
        pattern = RegexGenerator.generate(examples)

        assert all(_matches(pattern, e) for e in examples)

    def test_pattern_is_always_valid_regex(self):
        for examples in (
            ["a.b", "a-b"],
            ["x(1)", "x(22)"],
            ["/a+b/1", "/a+b/2"],
        ):
            pattern = RegexGenerator.generate(examples)
            re.compile(pattern)  # must not raise
