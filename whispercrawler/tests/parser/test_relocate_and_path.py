"""Tests for relocate()'s return-type contract and the path property."""

from whispercrawler.parser import Selector, Selectors

HTML = """
<html><body>
  <div class="wrap"><ul id="list"><li class="item">One</li><li class="item">Two</li></ul></div>
</body></html>
"""


OTHER_HTML = """
<html><body><table><tr><td id="cell">Unrelated</td></tr></table></body></html>
"""


def _page() -> Selector:
    return Selector(content=HTML)


def _foreign_target() -> Selector:
    """An element from a structurally unrelated document, so it scores below 100%."""
    return Selector(content=OTHER_HTML).css_first("td#cell")


class TestRelocateReturnType:
    def test_returns_selectors_when_match_found(self):
        page = _page()
        target = page.css_first("li.item")

        result = page.relocate(target, percentage=0, selector_type=True)

        assert isinstance(result, Selectors)

    def test_returns_selectors_when_nothing_meets_threshold(self):
        """Regression: a bare [] was returned, breaking the documented contract."""
        page = _page()

        result = page.relocate(_foreign_target(), percentage=100, selector_type=True)

        assert isinstance(result, Selectors)

    def test_empty_result_supports_selectors_api(self):
        """Callers do .getall() on the result - a plain list would crash."""
        page = _page()

        result = page.relocate(_foreign_target(), percentage=100, selector_type=True)

        assert result.getall() == []
        assert result.get() is None

    def test_returns_plain_list_when_selector_type_false(self):
        page = _page()

        result = page.relocate(_foreign_target(), percentage=100, selector_type=False)

        assert isinstance(result, list)
        assert not isinstance(result, Selectors)


class TestPathProperty:
    """`path` returns ancestors nearest-first, excluding the element itself."""

    def test_path_is_ancestors_nearest_first(self):
        page = _page()
        item = page.css_first("li.item")

        tags = [node.tag for node in item.path]

        assert tags == ["ul", "div", "body", "html"]

    def test_path_excludes_the_element_itself(self):
        page = _page()
        item = page.css_first("li.item")

        assert all(node.tag != "li" for node in item.path)

    def test_path_returns_selectors(self):
        page = _page()
        item = page.css_first("li.item")

        assert isinstance(item.path, Selectors)

    def test_docstring_describes_actual_order(self):
        doc = Selector.path.__doc__ or ""

        assert "nearest" in doc.lower() or "parent" in doc.lower()
