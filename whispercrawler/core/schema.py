import json
from typing import Any, Dict, List, Optional

from whispercrawler.core.utils import log

class SchemaDetector:
    """Extracts and processes structured data (Schema.org, JSON-LD) from a page."""
    
    def __init__(self, selector_obj: Any):
        self.selector = selector_obj

    def get_json_ld(self) -> List[Dict[str, Any]]:
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
                if isinstance(data, list):
                    schemas.extend(data)
                else:
                    schemas.append(data)
            except json.JSONDecodeError as e:
                log(f"Failed to parse JSON-LD schema: {e}", level="warning")
        
        return schemas

    def get_microdata(self) -> List[Dict[str, Any]]:
        """
        Extract Microdata (itemscope/itemtype/itemprop) from the page.
        This is a basic implementation focusing on top-level items.
        """
        # Basic implementation: find all top-level itemscopes
        items = []
        # Elements with itemscope and itemtype
        itemscopes = self.selector.xpath('//*[@itemscope and @itemtype]')
        
        for scope in itemscopes:
            item = {
                "@type": scope.attrib.get("itemtype", ""),
                "properties": {}
            }
            # Find all props within this scope that are not nested in another scope
            # (Note: robust microdata parsing is complex, this is a useful approximation)
            props = scope.xpath('.//*[@itemprop]')
            for prop in props:
                name = prop.attrib.get("itemprop")
                # Get value from 'content', 'src', 'href' or text
                val = prop.attrib.get("content") or prop.attrib.get("src") or prop.attrib.get("href") or prop.text.get()
                if name and val:
                    item["properties"][name] = val
            
            items.append(item)
            
        return items

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all detected structured data normalized to a list of dicts."""
        return self.get_json_ld() + self.get_microdata()

    def find_by_type(self, schema_type: str) -> List[Dict[str, Any]]:
        """Filter schemas by their @type or itemtype."""
        all_schemas = self.get_all()
        results = []
        for s in all_schemas:
            s_type = s.get("@type", "") or s.get("type", "")
            if schema_type.lower() in str(s_type).lower():
                results.append(s)
        return results
