from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class PageMetadata:
    """Represents the extracted metadata and 'learned' information about a page."""
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: List[str] = None
    author: Optional[str] = None
    canonical_url: Optional[str] = None
    
    # OpenGraph (Facebook, LinkedIn, etc.)
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    og_type: Optional[str] = None
    og_site_name: Optional[str] = None
    
    # Twitter Cards
    twitter_card: Optional[str] = None
    twitter_title: Optional[str] = None
    twitter_description: Optional[str] = None
    twitter_image: Optional[str] = None
    
    # Technical
    robots: Optional[str] = None
    viewport: Optional[str] = None
    charset: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class PageAnalyzer:
    """Analyzes a page to extract SEO, social, and technical metadata."""
    
    def __init__(self, selector_obj: Any):
        self.selector = selector_obj

    def _get_meta(self, name: str = "", property: str = "") -> Optional[str]:
        """Helper to extract content from meta tags."""
        if name:
            xpath = f'//meta[@name="{name}"]/@content'
        elif property:
            xpath = f'//meta[@property="{property}"]/@content'
        else:
            return None
            
        result = self.selector.xpath(xpath).get()
        return result.strip() if result else None

    def analyze(self) -> PageMetadata:
        """Extracts all metadata and returns a PageMetadata object."""
        # Keywords extraction
        kw_str = self._get_meta(name="keywords")
        keywords = [k.strip() for k in kw_str.split(",")] if kw_str else []

        return PageMetadata(
            # Basic
            title=self.selector.xpath("//title/text()").get() or self._get_meta(name="title"),
            description=self._get_meta(name="description"),
            keywords=keywords,
            author=self._get_meta(name="author"),
            canonical_url=self.selector.xpath('//link[@rel="canonical"]/@href').get(),
            
            # Social - OpenGraph
            og_title=self._get_meta(property="og:title"),
            og_description=self._get_meta(property="og:description"),
            og_image=self._get_meta(property="og:image"),
            og_type=self._get_meta(property="og:type"),
            og_site_name=self._get_meta(property="og:site_name"),
            
            # Social - Twitter
            twitter_card=self._get_meta(name="twitter:card"),
            twitter_title=self._get_meta(name="twitter:title"),
            twitter_description=self._get_meta(name="twitter:description"),
            twitter_image=self._get_meta(name="twitter:image"),
            
            # Technical
            robots=self._get_meta(name="robots"),
            viewport=self._get_meta(name="viewport"),
            charset=self.selector.xpath("//meta[@charset]/@charset").get()
        )

    def summary(self) -> str:
        """Returns a human-readable summary of the page based on metadata."""
        meta = self.analyze()
        lines = []
        if meta.title:
            lines.append(f"Title: {meta.title}")
        if meta.description:
            lines.append(f"Description: {meta.description}")
        if meta.og_type:
            lines.append(f"Type: {meta.og_type}")
        if meta.og_site_name:
            lines.append(f"Site: {meta.og_site_name}")
            
        return "\n".join(lines) if lines else "No significant metadata found."
