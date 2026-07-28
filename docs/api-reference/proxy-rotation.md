---
search:
  exclude: true
---

# Proxy Rotation

The `ProxyRotator` class provides thread-safe proxy rotation for any fetcher or session.

You can import it directly like below:

```python
from whispercrawler.fetchers import ProxyRotator
```

## Quarantine

When a request fails with a proxy-related error, the fetcher reports it and the rotator
withholds that proxy for `quarantine_seconds` (5 minutes by default) so it stops being
handed out. This is automatic — no wiring is required beyond passing a rotator:

```python
from whispercrawler.fetchers import FetcherSession, ProxyRotator

rotator = ProxyRotator([
    "http://user:pass@proxy1:8080",
    "http://user:pass@proxy2:8080",
])

with FetcherSession(proxy_rotator=rotator) as session:
    page = session.get("https://example.com")

rotator.status()     # per-proxy uses, failures, and quarantine deadline
rotator.active_count # proxies not currently quarantined
```

`status()` returns one entry per proxy:

```python
{
    "http://proxy1:8080": {
        "active": False,                       # False while withheld
        "uses": 12,
        "failures": 1,
        "quarantine_seconds_remaining": 180.0,  # None when active
    },
}
```

`quarantine_seconds_remaining` counts down and is `None` whenever the proxy is
available, so it never disagrees with `active` and never goes negative:

```python
for proxy, info in rotator.status().items():
    if not info["active"]:
        print(f"{proxy}: {info['quarantine_seconds_remaining']:.0f}s left")
```

Deadlines are tracked internally with [`time.monotonic`][monotonic] so that an NTP
correction cannot extend or collapse a quarantine window.

[monotonic]: https://docs.python.org/3/library/time.html#time.monotonic

Pass `quarantine_seconds=0` to record failures without ever withholding a proxy.

If every proxy is quarantined, `get_proxy()` returns the one closest to recovering and
logs a warning rather than raising, so a total outage degrades an in-flight crawl instead
of ending it.

You can also report outcomes yourself with `mark_failed()` and `mark_success()`.

!!! note "`ProxyWheel` is deprecated"
    `ProxyWheel` predates this feature and is now a thin shim over `ProxyRotator`. It
    emits a `DeprecationWarning` and will be removed in the next minor release. Use
    `ProxyRotator`, which also accepts Playwright-style dict proxies and custom strategy
    callables.

## ::: whispercrawler.engines.toolbelt.proxy_rotation.ProxyRotator
    handler: python
    :docstring:
