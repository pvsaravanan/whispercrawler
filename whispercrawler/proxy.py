# whispercrawler — Adaptive Web Scraping Framework
# MIT License
#
# Copyright (c) 2026, Saravanan P V
#
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the conditions of the MIT License are met.

"""Deprecated proxy rotator — kept as a thin shim over `ProxyRotator`."""

from __future__ import annotations

import warnings
from typing import Literal

from whispercrawler.core._types import List, ProxyType, cast
from whispercrawler.engines.toolbelt.proxy_rotation import (
    DEFAULT_QUARANTINE_SECONDS,
    ProxyRotator,
    RotationStrategy,
    cyclic_rotation,
    random_rotation,
)

StrategyName = Literal["round_robin", "random", "least_used"]


def _least_used_strategy(rotator: ProxyRotator) -> RotationStrategy:
    """Pick the proxy with the fewest recorded uses.

    Use counts are rotator state, and the `RotationStrategy` signature does not
    expose them, so this closes over the rotator instead. That call happens while
    `get_proxy` already holds the lock, which is why the lock must be reentrant.
    """

    def strategy(proxies: List[ProxyType], current_index: int) -> tuple[ProxyType, int]:
        return min(proxies, key=rotator._uses_of), current_index

    return strategy


class ProxyWheel(ProxyRotator):
    """Deprecated. Use :class:`ProxyRotator` instead.

    `ProxyRotator` now provides the quarantine behaviour this class was written for,
    and additionally accepts Playwright-style dict proxies and custom strategy
    callables. This subclass only translates the old API onto the new one.
    """

    def __init__(
        self,
        proxies: List[str],
        strategy: StrategyName = "round_robin",
        quarantine_seconds: float = DEFAULT_QUARANTINE_SECONDS,
    ) -> None:
        """
        :param proxies: List of proxy URL strings.
        :param strategy: One of "round_robin", "random", or "least_used".
        :param quarantine_seconds: How long a proxy is withheld after `mark_failed`.
        """
        warnings.warn(
            "ProxyWheel is deprecated and will be removed in the next minor release; "
            "use whispercrawler.fetchers.ProxyRotator instead, which supports the same "
            "quarantine behaviour plus dict proxies and custom strategies.",
            DeprecationWarning,
            stacklevel=2,
        )

        if strategy == "round_robin":
            resolved: RotationStrategy = cyclic_rotation
        elif strategy == "random":
            resolved = random_rotation
        elif strategy == "least_used":
            # Bound after super().__init__ below, once there is a rotator to close over.
            resolved = cyclic_rotation
        else:
            raise ValueError(
                f"Unknown strategy {strategy!r}; expected one of "
                f"'round_robin', 'random', 'least_used'"
            )

        # `list` is invariant, so a list[str] is not a list[ProxyType] to the checker
        # even though every str is a valid ProxyType.
        super().__init__(
            cast(List[ProxyType], proxies),
            strategy=resolved,
            quarantine_seconds=quarantine_seconds,
        )

        if strategy == "least_used":
            self._strategy = _least_used_strategy(self)

    def next(self) -> str:
        """Deprecated alias for :meth:`ProxyRotator.get_proxy`.

        Narrowed to `str`: this class only accepts string proxies, so widening the
        return to `ProxyType` would break downstream callers annotated for `str`.
        """
        return cast(str, self.get_proxy())

    @property
    def all_proxies(self) -> List[str]:
        """Deprecated alias for :attr:`ProxyRotator.proxies`."""
        return cast(List[str], self.proxies)

    def __repr__(self) -> str:
        return f"ProxyWheel(proxies={len(self.proxies)})"
