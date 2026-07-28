"""Tests for DOM path extraction on deeply nested documents."""

from lxml import html

from whispercrawler.core.utils._utils import _StorageTools


def _nested(depth: int) -> str:
    return "<html><body>" + ("<div>" * depth) + "leaf" + ("</div>" * depth) + "</body></html>"


class TestGetElementPath:
    def test_shallow_path_is_root_to_element(self):
        tree = html.fromstring("<html><body><div><span>x</span></div></body></html>")
        span = tree.xpath("//span")[0]

        assert _StorageTools._get_element_path(span) == ("html", "body", "div", "span")

    def test_root_element_path(self):
        tree = html.fromstring("<html><body><p>x</p></body></html>")

        assert _StorageTools._get_element_path(tree) == ("html",)

    def test_deeply_nested_document_does_not_recurse(self):
        """Regression: a deep DOM used to raise RecursionError during save().

        Parsed with huge_tree=True, the way Selector parses documents - lxml's
        default parser silently caps nesting at 255 and would hide the bug.
        """
        depth = 3000
        parser = html.HTMLParser(huge_tree=True, recover=True)
        tree = html.fromstring(_nested(depth), parser=parser)
        leaf = tree.xpath("//div[not(div)]")[0]

        path = _StorageTools._get_element_path(leaf)

        # html + body + `depth` divs
        assert len(path) == depth + 2
        assert path[0] == "html"
        assert path[-1] == "div"
