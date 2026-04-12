from functools import wraps
from typing import Any, Callable, TypeVar

from whispercrawler.parser import Selector, Selectors

_T = TypeVar("_T")

class WhisperResponse:
    """A proxy wrapper for Scrapy Response that uses WhisperCrawler's Selector logic.
    
    This replaces Scrapy's default parsel-based selection with WhisperCrawler's 
    high-performance, adaptive selection engine while maintaining compatibility 
    with Scrapy's response API (follow, urljoin, status, etc).
    """
    
    def __init__(self, response: Any):
        self._response = response
        self._whisper_selector = Selector(
            content=response.text,
            url=response.url,
            encoding=response.encoding
        )

    def __getattr__(self, name: str) -> Any:
        # Check WhisperCrawler Selector methods first (css, xpath, find_by_text, etc.)
        if hasattr(self._whisper_selector, name):
            return getattr(self._whisper_selector, name)
        # Fall back to Scrapy Response methods/attributes (status, headers, cookies, meta)
        return getattr(self._response, name)

    @property
    def selector(self) -> Selector:
        """Return the WhisperCrawler Selector instance."""
        return self._whisper_selector

    def css(self, selector: str, adaptive: bool = False, **kwargs: Any) -> Selectors:
        """Search using CSS3 selectors with optional WhisperCrawler adaptive mode."""
        return self._whisper_selector.css(selector, adaptive=adaptive, **kwargs)

    def xpath(self, selector: str, adaptive: bool = False, **kwargs: Any) -> Selectors:
        """Search using XPath expressions with optional WhisperCrawler adaptive mode."""
        return self._whisper_selector.xpath(selector, adaptive=adaptive, **kwargs)

    def urljoin(self, url: str) -> str:
        """Forward to Scrapy's urljoin."""
        return self._response.urljoin(url)

    def follow(self, *args: Any, **kwargs: Any) -> Any:
        """Forward to Scrapy's follow method for crawling."""
        return self._response.follow(*args, **kwargs)

    def __repr__(self) -> str:
        return f"<WhisperResponse ({self._response.status}) {self._response.url}>"


def whisper_response(func: Callable) -> Callable:
    """
    A Scrapy decorator to replace the 'response' argument with a WhisperResponse proxy.
    
    Usage in a Scrapy Spider:
    
    @whisper_response
    def parse(self, response):
        # response is now a WhisperResponse
        # Use standard CSS/XPath:
        items = response.css(".item-class")
        
        # Or use adaptive mode to survive website redesigns:
        title = response.css("h1.title", adaptive=True)
        
        # Use WhisperCrawler specific helpers:
        author = response.find_by_text("Written by", partial=True)
    """
    @wraps(func)
    def wrapper(self, response: Any, *args: Any, **kwargs: Any) -> Any:
        # Wrap the Scrapy response before calling the parse method
        return func(self, WhisperResponse(response), *args, **kwargs)
    return wrapper
