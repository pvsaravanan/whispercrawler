# WhisperCrawler — Adaptive Web Scraping Framework
# MIT License
#
# Copyright (c) 2026, Saravanan P V
#

"""
WhisperCrawler — Adaptive Web Scraping Framework

This framework provides fast, stealthy, and self-healing web scraping.
"""

__version__ = "0.1.1"

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from whispercrawler.fetchers import (
        AsyncCrawler,
        AsyncFetcher,
        AsyncGhostCrawler,
        AsyncShadowCrawler,
        Crawler,
        DynamicFetcher,
        Fetcher,
        FetcherSession,
        GhostCrawler,
        ShadowCrawler,
        ShadowFetcher,
        StealthyFetcher,
    )
    from whispercrawler.parser import Page, PageList, Selector, Selectors
    from whispercrawler.proxy import ProxyWheel
    from whispercrawler.spiders import Request, Response, Spider

_LAZY_IMPORTS = {
    # Core WhisperCrawler logic renamed/aliased
    "Selector": ("whispercrawler.parser", "Selector"),
    "Selectors": ("whispercrawler.parser", "Selectors"),
    "Page": ("whispercrawler.parser", "Page"),
    "PageList": ("whispercrawler.parser", "PageList"),
    # Fetchers (WhisperCrawler names)
    "Fetcher": ("whispercrawler.fetchers", "Fetcher"),
    "AsyncFetcher": ("whispercrawler.fetchers", "AsyncFetcher"),
    "FetcherSession": ("whispercrawler.fetchers.requests", "FetcherSession"),
    "DynamicFetcher": ("whispercrawler.fetchers", "DynamicFetcher"),
    "StealthyFetcher": ("whispercrawler.fetchers", "StealthyFetcher"),
    "ShadowFetcher": ("whispercrawler.fetchers", "ShadowFetcher"),
    # WhisperCrawler specific naming/aliases
    "Crawler": ("whispercrawler.fetchers", "Fetcher"),
    "AsyncCrawler": ("whispercrawler.fetchers", "AsyncFetcher"),
    "GhostCrawler": ("whispercrawler.fetchers", "DynamicFetcher"),
    "AsyncGhostCrawler": ("whispercrawler.fetchers", "DynamicFetcher"),  # One class handles both
    "ShadowCrawler": ("whispercrawler.fetchers", "ShadowFetcher"),
    "AsyncShadowCrawler": ("whispercrawler.fetchers", "ShadowFetcher"),  # One class handles both
    # Spider logic
    "Spider": ("whispercrawler.spiders", "Spider"),
    "Request": ("whispercrawler.spiders", "Request"),
    "Response": ("whispercrawler.spiders", "Response"),
    # Proxy
    "ProxyWheel": ("whispercrawler.proxy", "ProxyWheel"),
}

__all__ = sorted(list(_LAZY_IMPORTS.keys()))


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        module_path, class_name = _LAZY_IMPORTS[name]
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Support for dir() and autocomplete."""
    return sorted(__all__ + ["fetchers", "parser", "cli", "core", "__version__"])
