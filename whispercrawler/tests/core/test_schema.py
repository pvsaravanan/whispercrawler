"""Tests for JSON-LD / Microdata extraction robustness."""

from whispercrawler.parser import Selector


def _page(body: str) -> Selector:
    return Selector(content=f"<html><body>{body}</body></html>")


class TestJsonLdMalformedPayloads:
    """Real-world pages carry placeholder and non-object JSON-LD blocks."""

    def test_null_payload_is_ignored(self):
        page = _page('<script type="application/ld+json">null</script>')

        assert page.schemas == []

    def test_array_of_primitives_is_ignored(self):
        page = _page('<script type="application/ld+json">["a", "b"]</script>')

        assert page.schemas == []

    def test_bare_string_payload_is_ignored(self):
        page = _page('<script type="application/ld+json">"just a string"</script>')

        assert page.schemas == []

    def test_number_payload_is_ignored(self):
        page = _page('<script type="application/ld+json">42</script>')

        assert page.schemas == []

    def test_valid_object_still_extracted(self):
        page = _page('<script type="application/ld+json">{"@type": "Product"}</script>')

        assert page.schemas == [{"@type": "Product"}]

    def test_mixed_array_keeps_only_objects(self):
        page = _page(
            '<script type="application/ld+json">[{"@type": "Product"}, null, "x"]</script>'
        )

        assert page.schemas == [{"@type": "Product"}]

    def test_find_schema_does_not_crash_on_null_payload(self):
        """Regression: find_by_type used to raise AttributeError on a null entry."""
        page = _page(
            '<script type="application/ld+json">null</script>'
            '<script type="application/ld+json">{"@type": "Product"}</script>'
        )

        assert page.find_schema("Product") == [{"@type": "Product"}]

    def test_invalid_json_still_ignored(self):
        page = _page('<script type="application/ld+json">{not json}</script>')

        assert page.schemas == []
