from typing import TYPE_CHECKING, Any

from whispercrawler.engines.toolbelt import ProxyRotator

if TYPE_CHECKING:
    from whispercrawler.fetchers.chrome import AsyncDynamicSession, DynamicFetcher, DynamicSession
    from whispercrawler.fetchers.requests import AsyncFetcher, Fetcher, FetcherSession
    from whispercrawler.fetchers.stealth_chrome import (
        AsyncStealthySession,
        StealthyFetcher,
        StealthySession,
    )


# Lazy import mapping
_LAZY_IMPORTS = {
    "Fetcher": ("whispercrawler.fetchers.requests", "Fetcher"),
    "AsyncFetcher": ("whispercrawler.fetchers.requests", "AsyncFetcher"),
    "FetcherSession": ("whispercrawler.fetchers.requests", "FetcherSession"),
    "DynamicFetcher": ("whispercrawler.fetchers.chrome", "DynamicFetcher"),
    "DynamicSession": ("whispercrawler.fetchers.chrome", "DynamicSession"),
    "AsyncDynamicSession": ("whispercrawler.fetchers.chrome", "AsyncDynamicSession"),
    "StealthyFetcher": ("whispercrawler.fetchers.stealth_chrome", "StealthyFetcher"),
    "StealthySession": ("whispercrawler.fetchers.stealth_chrome", "StealthySession"),
    "AsyncStealthySession": ("whispercrawler.fetchers.stealth_chrome", "AsyncStealthySession"),
    "ShadowFetcher": ("whispercrawler.fetchers.shadow", "ShadowFetcher"),
    "ShadowCrawler": ("whispercrawler.fetchers.shadow", "ShadowCrawler"),
    "AsyncShadowCrawler": ("whispercrawler.fetchers.shadow", "AsyncShadowCrawler"),
}

__all__ = [
    "Fetcher",
    "AsyncFetcher",
    "ProxyRotator",
    "FetcherSession",
    "DynamicFetcher",
    "DynamicSession",
    "AsyncDynamicSession",
    "StealthyFetcher",
    "StealthySession",
    "AsyncStealthySession",
    "ShadowFetcher",
    "ShadowCrawler",
    "AsyncShadowCrawler",
]


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        module_path, class_name = _LAZY_IMPORTS[name]
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Support for dir() and autocomplete."""
    return sorted(list(_LAZY_IMPORTS.keys()))
