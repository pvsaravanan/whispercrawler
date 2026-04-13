# MIT License
#
# Copyright (c) 2026, Saravanan P V
#
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the conditions of the BSD-3-Clause License are met.

"""Shared browser stealth utilities for GhostCrawler and ShadowCrawler."""

from __future__ import annotations

import logging
import random

logger = logging.getLogger("whispercrawler.toolbelt")

_STEALTH_JS = """
// Override navigator.webdriver
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// Override navigator.plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});

// Override navigator.languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en', 'es']
});

// Set window.chrome
window.chrome = {
    runtime: {},
    loadTimes: function() {},
    csi: function() {},
    app: {}
};

// Override permissions.query
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);
"""

_COMMON_VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 2560, "height": 1440},
    {"width": 1536, "height": 864},
    {"width": 1280, "height": 720},
]

_HEADERS_CHROME = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

_HEADERS_FIREFOX = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
}

_HEADERS_SAFARI = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
}

_HEADERS_EDGE = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
}

_BROWSER_HEADERS = {
    "chrome": _HEADERS_CHROME,
    "firefox": _HEADERS_FIREFOX,
    "safari": _HEADERS_SAFARI,
    "edge": _HEADERS_EDGE,
}


def apply_stealth_scripts(page: object) -> None:
    """Inject JS patches into Playwright page to evade common bot detection.

    Overrides navigator.webdriver, plugins, languages, window.chrome,
    and permissions.query.

    Args:
        page: A Playwright page object.
    """
    if hasattr(page, "add_init_script"):
        page.add_init_script(_STEALTH_JS)  # type: ignore[union-attr]
    elif hasattr(page, "evaluate"):
        page.evaluate(_STEALTH_JS)  # type: ignore[union-attr]
    logger.debug("Stealth scripts applied")


def generate_realistic_headers(browser_type: str = "chrome") -> dict[str, str]:
    """Return a realistic HTTP headers dict for the given browser type.

    Args:
        browser_type: One of 'chrome', 'firefox', 'safari', 'edge'.

    Returns:
        Dict of realistic HTTP headers.
    """
    return dict(_BROWSER_HEADERS.get(browser_type, _HEADERS_CHROME))


def random_viewport() -> dict[str, int]:
    """Return a dict with width and height chosen from common screen resolutions.

    Returns:
        Dict with 'width' and 'height' keys.
    """
    return dict(random.choice(_COMMON_VIEWPORTS))


def build_proxy_dict(proxy_url: str) -> dict[str, str]:
    """Parse proxy URL string into a dict compatible with Playwright and Camoufox.

    Args:
        proxy_url: Proxy URL (http://user:pass@host:port).

    Returns:
        Dict with 'server', 'username', 'password' keys.
    """
    from urllib.parse import urlparse

    parsed = urlparse(proxy_url)
    result: dict[str, str] = {
        "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
    }
    if parsed.username:
        result["username"] = parsed.username
    if parsed.password:
        result["password"] = parsed.password
    return result
