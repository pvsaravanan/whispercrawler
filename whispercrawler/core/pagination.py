import re
from typing import Any, List, Optional, Set
from urllib.parse import urljoin

class PaginationDetector:
    """Detects pagination links (next page and page numbers) in a web page."""
    
    # Common text indicators for the "Next" button in many languages
    NEXT_TEXT_PATTERNS = [
        r'next', r'siguiente', r'proximo', r'proxima', r'suivant', r'weiter',
        r'nã¤chste', r'»', r'>', r'arrow-right', r'forward'
    ]
    
    # Common CSS classes for pagination containers and buttons
    PAGINATION_SELECTORS = [
        '.pagination', '.pager', '.paging', '.page-nav', '.pages',
        '[class*="pagination"]', '[class*="pager"]', '[class*="paging"]'
    ]
    
    NEXT_SELECTORS = [
        '.next', '.next-page', '.pg-next', '.arrow-next',
        '[class*="next"]', '[rel="next"]'
    ]

    def __init__(self, selector_obj: Any):
        self.selector = selector_obj
        self.url = selector_obj.url

    def get_next_page(self) -> Optional[str]:
        """Attempt to find the 'Next' page URL."""
        
        # 1. Look for <link rel="next"> or <a rel="next">
        for link in self.selector.xpath('//link[@rel="next"]/@href | //a[@rel="next"]/@href'):
            url = link.get()
            if url:
                return urljoin(self.url, url)

        # 2. Look for elements with "next" text/classes
        # We prefer links with "next" text that are inside common pagination containers
        for sel in self.NEXT_SELECTORS:
            for link in self.selector.css(f'a{sel}'):
                href = link.attrib.get('href')
                if href:
                    return urljoin(self.url, href)

        # 3. Search by text content
        for pattern in self.NEXT_TEXT_PATTERNS:
            # Look for <a> tags containing the pattern
            matches = self.selector.xpath(
                f'//a[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{pattern}")]'
            )
            for match in matches:
                href = match.attrib.get('href')
                if href:
                    return urljoin(self.url, href)
        
        # 4. Fallback: Identify the current active page and pick the next sibling if it's a number
        # Often pagination is a list of 1, 2, [3], 4
        # We look for the "active" or "current" class
        active = self.selector.css('.active, .current, [aria-current="page"]')
        if active:
            # Find the next immediate sibling anchor
            next_sibling = active.xpath('following-sibling::a[1]/@href | following-sibling::li[1]/a/@href').get()
            if next_sibling:
                return urljoin(self.url, next_sibling)

        return None

    def get_all_pages(self) -> List[str]:
        """Detect all available page links in a pagination block."""
        discovered_urls: List[str] = []
        seen: Set[str] = set()
        
        # Find the most likely pagination container
        container = None
        for sel in self.PAGINATION_SELECTORS:
            result = self.selector.css(sel)
            if result:
                container = result[0]
                break
        
        if container:
            # Extract all unique links from this container
            for link in container.css('a[href]'):
                href = link.attrib.get('href')
                if href:
                    abs_url = urljoin(self.url, href)
                    if abs_url not in seen and abs_url != self.url:
                        discovered_urls.append(abs_url)
                        seen.add(abs_url)
        
        return discovered_urls

def detect_next_page(selector: Any) -> Optional[str]:
    """Helper function to get the next page URL."""
    return PaginationDetector(selector).get_next_page()

def detect_all_pages(selector: Any) -> List[str]:
    """Helper function to get all page URLs."""
    return PaginationDetector(selector).get_all_pages()
