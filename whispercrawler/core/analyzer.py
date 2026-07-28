from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PageMetadata:
    """Represents the extracted metadata and 'learned' information about a page."""

    title: str | None = None
    description: str | None = None
    keywords: list[str] = field(default_factory=list)
    author: str | None = None
    canonical_url: str | None = None

    # OpenGraph (Facebook, LinkedIn, etc.)
    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None
    og_type: str | None = None
    og_site_name: str | None = None

    # Twitter Cards
    twitter_card: str | None = None
    twitter_title: str | None = None
    twitter_description: str | None = None
    twitter_image: str | None = None

    # Technical
    robots: str | None = None
    viewport: str | None = None
    charset: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PageAnalyzer:
    """Analyzes a page to extract SEO, social, and technical metadata."""

    def __init__(self, selector_obj: Any):
        self.selector = selector_obj

    def _get_meta(self, name: str = "", property: str = "") -> str | None:
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
            charset=self.selector.xpath("//meta[@charset]/@charset").get(),
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
