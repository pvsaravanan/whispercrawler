# WhisperCrawler — Adaptive Web Scraping Framework
# MIT License
#
# Copyright (c) 2026, Saravanan P V
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the conditions of the MIT License are met.

"""Interactive WhisperCrawler shell using IPython."""

from __future__ import annotations

import re
import sys
import tempfile
import webbrowser
from typing import Any


def _store(page: Any) -> Any:
    """Store fetched page in shell namespace and return it."""
    import IPython

    ip = IPython.get_ipython()
    if ip:
        ip.user_ns["page"] = page
        pages = ip.user_ns.get("pages", [])
        pages.append(page)
        ip.user_ns["pages"] = pages
    return page


def view(page: Any) -> None:
    """Open page.html in browser tab."""
    html_content = page.html if hasattr(page, "html") else str(page)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(str(html_content))
        webbrowser.open(f"file://{f.name}")


def curl2crawler(curl_cmd: str) -> str:
    """Convert curl command to Crawler code string.

    Args:
        curl_cmd: A curl command string.

    Returns:
        A Python code string using Crawler.

    Example:
        Input:  "curl 'https://example.com' -H 'Accept: text/html'"
        Output: "Crawler.get('https://example.com', headers={'Accept': 'text/html'})"
    """
    # Extract URL
    url_match = re.search(r"curl\s+['\"]?(https?://[^\s'\"]+)['\"]?", curl_cmd)
    url = url_match.group(1) if url_match else "https://example.com"

    # Extract headers
    headers: dict[str, str] = {}
    header_matches = re.findall(r"-H\s+['\"]([^'\"]+)['\"]", curl_cmd)
    for h in header_matches:
        if ":" in h:
            key, value = h.split(":", 1)
            headers[key.strip()] = value.strip()

    # Detect method
    method = "GET"
    method_match = re.search(r"-X\s+(\w+)", curl_cmd)
    if method_match:
        method = method_match.group(1).upper()
    elif "-d" in curl_cmd or "--data" in curl_cmd:
        method = "POST"

    # Extract data
    data_match = re.search(r"(?:-d|--data)\s+['\"]([^'\"]*)['\"]", curl_cmd)
    data = data_match.group(1) if data_match else None

    # Build code string
    parts = [f"'{url}'"]
    if headers:
        parts.append(f"headers={headers!r}")
    if data:
        parts.append(f"data='{data}'")

    if method == "POST":
        return f"Crawler.post({', '.join(parts)})"
    elif method in ("PUT", "DELETE", "HEAD"):
        return f"Crawler.{method.lower()}({', '.join(parts)})"
    else:
        return f"Crawler.get({', '.join(parts)})"


def launch() -> None:
    """Launch IPython shell with WhisperCrawler pre-loaded."""
    try:
        import IPython
    except ImportError:
        sys.stderr.write("Error: IPython is required. Install with: pip install ipython\n")
        sys.exit(1)

    from whispercrawler import __version__

    # Lazy import fetchers — they're heavy
    def _get(url: str, **kw: Any) -> Any:
        from whispercrawler.fetchers import Fetcher

        return _store(Fetcher.get(url, **kw))

    def _post(url: str, **kw: Any) -> Any:
        from whispercrawler.fetchers import Fetcher

        return _store(Fetcher.post(url, **kw))

    def _fetch(url: str, **kw: Any) -> Any:
        from whispercrawler.fetchers import DynamicFetcher

        return _store(DynamicFetcher.fetch(url, **kw))

    def _ghost_fetch(url: str, **kw: Any) -> Any:
        from whispercrawler.fetchers import DynamicFetcher

        return _store(DynamicFetcher.fetch(url, **kw))

    def _shadow_fetch(url: str, **kw: Any) -> Any:
        from whispercrawler.fetchers import ShadowFetcher

        return _store(ShadowFetcher.fetch(url, **kw))

    namespace: dict[str, Any] = {
        # Shortcut functions
        "get": _get,
        "post": _post,
        "fetch": _fetch,
        "ghost_fetch": _ghost_fetch,
        "shadow_fetch": _shadow_fetch,
        # History
        "page": None,
        "pages": [],
        # Dev tools
        "view": view,
        "curl2crawler": curl2crawler,
        "uncurl": curl2crawler,
    }

    # Lazy-load class references into namespace
    try:
        from whispercrawler.fetchers import Fetcher as Crawler

        namespace["Crawler"] = Crawler
    except ImportError:
        pass
    try:
        from whispercrawler.fetchers import DynamicFetcher as GhostCrawler

        namespace["GhostCrawler"] = GhostCrawler
    except ImportError:
        pass
    try:
        from whispercrawler.fetchers import ShadowFetcher as ShadowCrawler

        namespace["ShadowCrawler"] = ShadowCrawler
    except ImportError:
        pass

    ip_version = IPython.__version__
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    banner = (
        f"\n[bold cyan]WhisperCrawler Interactive Shell v{__version__}[/bold cyan]\n"
        f"Python {py_version} | IPython {ip_version}\n\n"
        "Shortcuts: get(url)  post(url)  fetch(url)  ghost_fetch(url)  shadow_fetch(url)\n"
        "History:   page (last result)   pages (all results)\n"
        'Tools:     view(page)   curl2crawler("curl ...")\n\n'
        "Type help(Crawler) for full API reference.\n"
    )

    IPython.start_ipython(argv=[], user_ns=namespace, display_banner=False)
    # Print banner manually since IPython display_banner doesn't support Rich
    sys.stdout.write(banner.replace("[bold cyan]", "").replace("[/bold cyan]", "") + "\n")
