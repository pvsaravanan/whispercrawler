import json
from typing import Any

from whispercrawler.core.utils import log


class SchemaDetector:
    """Extracts and processes structured data (Schema.org, JSON-LD) from a page."""

    def __init__(self, selector_obj: Any):
        self.selector = selector_obj

    def get_json_ld(self) -> list[dict[str, Any]]:
        """Extract all JSON-LD blocks from the page."""
        schemas = []
        # Find all <script type="application/ld+json">
        scripts = self.selector.xpath('//script[@type="application/ld+json"]/text()')

        for script_text in scripts:
            content = script_text.get()
            if not content:
                continue

            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                log.warning(f"Failed to parse JSON-LD schema: {e}")
                continue

            # A JSON-LD block is only usable if it is an object (or an array of them).
            # Pages routinely ship placeholders like `null` or arrays of primitives,
            # and anything non-dict would blow up every consumer that calls .get().
            if isinstance(data, dict):
                schemas.append(data)
            elif isinstance(data, list):
                schemas.extend(entry for entry in data if isinstance(entry, dict))
            else:
                log.warning(f"Ignoring non-object JSON-LD schema of type {type(data).__name__}")

        return schemas

    def get_microdata(self) -> list[dict[str, Any]]:
        """
        Extract Microdata (itemscope/itemtype/itemprop) from the page.
        This is a basic implementation focusing on top-level items.
        """
        # Basic implementation: find all top-level itemscopes
        items = []
        # Elements with itemscope and itemtype
        itemscopes = self.selector.xpath("//*[@itemscope and @itemtype]")

        for scope in itemscopes:
            item = {"@type": scope.attrib.get("itemtype", ""), "properties": {}}
            # Find all props within this scope that are not nested in another scope
            # (Note: robust microdata parsing is complex, this is a useful approximation)
            props = scope.xpath(".//*[@itemprop]")
            for prop in props:
                name = prop.attrib.get("itemprop")
                # Get value from 'content', 'src', 'href' or text
                val = (
                    prop.attrib.get("content")
                    or prop.attrib.get("src")
                    or prop.attrib.get("href")
                    or prop.text.get()
                )
                if name and val:
                    item["properties"][name] = val

            items.append(item)

        return items

    def get_all(self) -> list[dict[str, Any]]:
        """Return all detected structured data normalized to a list of dicts."""
        return self.get_json_ld() + self.get_microdata()

    def find_by_type(self, schema_type: str) -> list[dict[str, Any]]:
        """Filter schemas by their @type or itemtype."""
        all_schemas = self.get_all()
        results = []
        for s in all_schemas:
            s_type = s.get("@type", "") or s.get("type", "")
            if schema_type.lower() in str(s_type).lower():
                results.append(s)
        return results
