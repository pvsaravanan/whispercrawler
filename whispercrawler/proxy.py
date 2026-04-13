# WhisperCrawler — Adaptive Web Scraping Framework
# MIT License
#
# Copyright (c) 2026, Saravanan P V
#
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the conditions of the MIT License are met.

"""Proxy rotation — round-robin, random, and least-used strategies."""

from __future__ import annotations

import logging
import random
import threading
from datetime import datetime, timedelta, timezone
from typing import Literal

logger = logging.getLogger("whispercrawler.proxy")

_QUARANTINE_DURATION = timedelta(minutes=5)


class _ProxyState:
    """Internal state for a single proxy."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.uses = 0
        self.failures = 0
        self.quarantine_until: datetime | None = None

    @property
    def is_active(self) -> bool:
        """Return True if proxy is not quarantined."""
        if self.quarantine_until is None:
            return True
        return datetime.now(timezone.utc) >= self.quarantine_until


class ProxyWheel:
    """Thread-safe proxy rotator.

    Maintains a pool of proxy URLs and rotates through them
    according to the configured strategy. Failed proxies are
    quarantined for 5 minutes before re-entry.
    """

    def __init__(
        self,
        proxies: list[str],
        strategy: Literal["round_robin", "random", "least_used"] = "round_robin",
    ) -> None:
        """Initialize ProxyWheel.

        Args:
            proxies: List of proxy URL strings.
                Accepted formats: http://host:port, http://user:pass@host:port, socks5://host:port
            strategy: Rotation strategy — round_robin, random, or least_used.
        """
        if not proxies:
            raise ValueError("At least one proxy URL is required")
        self._lock = threading.Lock()
        self._strategy = strategy
        self._proxies: dict[str, _ProxyState] = {url: _ProxyState(url) for url in proxies}
        self._order: list[str] = list(proxies)
        self._rr_index = 0

    def get_proxy(self) -> str:
        """Alias for next() to maintain compatibility with WhisperCrawler engine."""
        return self.next()

    def next(self) -> str:
        """Return next proxy URL according to strategy.

        Thread-safe. Skips quarantined proxies.

        Raises:
            RuntimeError: If all proxies are quarantined.
        """
        with self._lock:
            active = [s for s in self._proxies.values() if s.is_active]
            if not active:
                raise RuntimeError("All proxies are quarantined")

            if self._strategy == "round_robin":
                return self._next_round_robin(active)
            elif self._strategy == "random":
                return self._next_random(active)
            elif self._strategy == "least_used":
                return self._next_least_used(active)
            else:
                return self._next_round_robin(active)

    def _next_round_robin(self, active: list[_ProxyState]) -> str:
        """Pick next proxy in round-robin order."""
        active_urls = {s.url for s in active}
        attempts = 0
        while attempts < len(self._order):
            idx = self._rr_index % len(self._order)
            self._rr_index += 1
            url = self._order[idx]
            if url in active_urls:
                state = self._proxies[url]
                state.uses += 1
                return url
            attempts += 1
        # Fallback
        state = active[0]
        state.uses += 1
        return state.url

    def _next_random(self, active: list[_ProxyState]) -> str:
        """Pick a random active proxy."""
        state = random.choice(active)
        state.uses += 1
        return state.url

    def _next_least_used(self, active: list[_ProxyState]) -> str:
        """Pick the proxy with fewest total uses."""
        state = min(active, key=lambda s: s.uses)
        state.uses += 1
        return state.url

    def mark_failed(self, proxy: str) -> None:
        """Mark proxy as failed. Quarantine it for 5 minutes. Thread-safe."""
        with self._lock:
            state = self._proxies.get(proxy)
            if state:
                state.failures += 1
                state.quarantine_until = datetime.now(timezone.utc) + _QUARANTINE_DURATION
                logger.warning(
                    "Proxy %s quarantined until %s (failure #%d)",
                    proxy,
                    state.quarantine_until.isoformat(),
                    state.failures,
                )

    def mark_success(self, proxy: str) -> None:
        """Record successful use of proxy."""
        with self._lock:
            state = self._proxies.get(proxy)
            if state:
                state.uses += 1

    def add(self, proxy: str) -> None:
        """Add a new proxy to the pool at runtime. Thread-safe."""
        with self._lock:
            if proxy not in self._proxies:
                self._proxies[proxy] = _ProxyState(proxy)
                self._order.append(proxy)
                logger.info("Added proxy: %s", proxy)

    def remove(self, proxy: str) -> None:
        """Remove proxy from pool permanently. Thread-safe."""
        with self._lock:
            self._proxies.pop(proxy, None)
            if proxy in self._order:
                self._order.remove(proxy)
            logger.info("Removed proxy: %s", proxy)

    @property
    def active_count(self) -> int:
        """Number of non-quarantined proxies."""
        with self._lock:
            return sum(1 for s in self._proxies.values() if s.is_active)

    @property
    def all_proxies(self) -> list[str]:
        """All proxy URLs regardless of quarantine status."""
        with self._lock:
            return list(self._order)

    def status(self) -> dict[str, dict[str, object]]:
        """Return dict mapping proxy URL to status dict.

        Returns:
            {proxy_url: {"active": bool, "uses": int, "failures": int, "quarantine_until": str|None}}
        """
        with self._lock:
            result: dict[str, dict[str, object]] = {}
            for url, state in self._proxies.items():
                result[url] = {
                    "active": state.is_active,
                    "uses": state.uses,
                    "failures": state.failures,
                    "quarantine_until": (
                        state.quarantine_until.isoformat() if state.quarantine_until else None
                    ),
                }
            return result
