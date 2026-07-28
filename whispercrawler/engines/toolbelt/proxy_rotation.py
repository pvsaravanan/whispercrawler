from random import choice as random_choice
from threading import RLock
from time import monotonic

from whispercrawler.core._types import Callable, Dict, List, Optional, ProxyType, Tuple
from whispercrawler.core.utils import log

RotationStrategy = Callable[[List[ProxyType], int], Tuple[ProxyType, int]]
#: Default time a proxy is withheld after a failure.
DEFAULT_QUARANTINE_SECONDS = 300.0
_PROXY_ERROR_INDICATORS = {
    "net::err_proxy",
    "net::err_tunnel",
    "connection refused",
    "connection reset",
    "connection timed out",
    "failed to connect",
    "could not resolve proxy",
}


def _get_proxy_key(proxy: ProxyType) -> str:
    """Generate a unique key for a proxy (for dicts it's server plus username)."""
    if isinstance(proxy, str):
        return proxy
    server = proxy.get("server", "")
    username = proxy.get("username", "")
    return f"{server}|{username}"


def is_proxy_error(error: Exception) -> bool:
    """Check if an error is proxy-related. Works for both HTTP and browser errors."""
    error_msg = str(error).lower()
    return any(indicator in error_msg for indicator in _PROXY_ERROR_INDICATORS)


def report_proxy_failure(
    rotator: "Optional[ProxyRotator]",
    proxy: Optional[ProxyType],
    error: Exception,
) -> bool:
    """Report a failed request, quarantining the proxy when one is in play.

    Returns whether `error` was proxy-related - **not** whether a quarantine happened.
    The two differ when there is nothing to quarantine (a static `proxy=` with no
    rotator, or no proxy at all), and callers rely on the classification regardless:
    the engines use it to choose between their proxy and generic retry log messages.

    Safe to call with no rotator or no proxy.
    """
    if not is_proxy_error(error):
        return False
    if rotator is not None and proxy is not None:
        rotator.mark_failed(proxy)
    return True


def cyclic_rotation(proxies: List[ProxyType], current_index: int) -> Tuple[ProxyType, int]:
    """Default cyclic rotation strategy — iterates through proxies sequentially, wrapping around at the end."""
    idx = current_index % len(proxies)
    return proxies[idx], (idx + 1) % len(proxies)


def random_rotation(proxies: List[ProxyType], current_index: int) -> Tuple[ProxyType, int]:
    """Pick a proxy at random, leaving the index untouched."""
    return random_choice(proxies), current_index


class _ProxyState:
    """Per-proxy bookkeeping: usage counts and the quarantine deadline."""

    __slots__ = ("uses", "failures", "quarantine_until")

    def __init__(self) -> None:
        self.uses = 0
        self.failures = 0
        #: Monotonic deadline, or None when the proxy is not quarantined.
        self.quarantine_until: Optional[float] = None


class ProxyRotator:
    """
    A thread-safe proxy rotator with pluggable rotation strategies.

    Supports:
    - Cyclic rotation (default)
    - Custom rotation strategies via callable
    - Both string URLs and Playwright-style dict proxies
    - Quarantining proxies that fail, so a dead proxy stops being handed out
    """

    __slots__ = (
        "_proxies",
        "_state",
        "_strategy",
        "_current_index",
        "_lock",
        "_quarantine",
        "_clock",
    )

    def __init__(
        self,
        proxies: List[ProxyType],
        strategy: RotationStrategy = cyclic_rotation,
        quarantine_seconds: float = DEFAULT_QUARANTINE_SECONDS,
        _clock: Callable[[], float] = monotonic,
    ):
        """
        Initialize the proxy rotator.

        :param proxies: List of proxy URLs or Playwright-style proxy dicts.
            - String format: "http://proxy1:8080" or "http://user:pass@proxy:8080"
            - Dict format: {"server": "http://proxy:8080", "username": "user", "password": "pass"}
        :param strategy: Rotation strategy function. Takes (proxies, current_index) and returns (proxy, next_index). Defaults to cyclic_rotation.
        :param quarantine_seconds: How long a proxy is withheld after `mark_failed`. Pass 0 to
            record failures without ever withholding.
        """
        if not proxies:
            raise ValueError("At least one proxy must be provided")

        if not callable(strategy):
            raise TypeError(f"strategy must be callable, got {type(strategy).__name__}")

        if quarantine_seconds < 0:
            raise ValueError(f"quarantine_seconds must be >= 0, got {quarantine_seconds!r}")

        self._strategy = strategy
        self._quarantine = float(quarantine_seconds)
        self._clock = _clock
        # Reentrant because `get_proxy` holds the lock while calling the strategy, and a
        # strategy may legitimately call back in - `least_used` reads use counts that way.
        self._lock = RLock()

        # Validate and store proxies, keyed by unique key (server + username) because
        # Playwright-style dict proxies are unhashable and cannot key a dict themselves.
        self._proxies: List[ProxyType] = []
        self._state: Dict[str, _ProxyState] = {}
        for proxy in proxies:
            if isinstance(proxy, (str, dict)):
                if isinstance(proxy, dict) and "server" not in proxy:
                    raise ValueError("Proxy dict must have a 'server' key")

                self._state[_get_proxy_key(proxy)] = _ProxyState()
                self._proxies.append(proxy)
            else:
                raise TypeError(f"Invalid proxy type: {type(proxy)}. Expected str or dict.")

        self._current_index = 0

    # -- internals -------------------------------------------------------

    def _is_active(self, proxy: ProxyType) -> bool:
        state = self._state.get(_get_proxy_key(proxy))
        if state is None or state.quarantine_until is None:
            return True
        return self._clock() >= state.quarantine_until

    def _uses_of(self, proxy: ProxyType) -> int:
        state = self._state.get(_get_proxy_key(proxy))
        return state.uses if state else 0

    def _record_use(self, proxy: ProxyType) -> None:
        state = self._state.get(_get_proxy_key(proxy))
        if state:
            state.uses += 1

    def _oldest_quarantined(self) -> ProxyType:
        """The quarantined proxy whose deadline expires soonest.

        Only meaningful when every proxy is quarantined; `float("inf")` keeps any
        non-quarantined proxy from being selected here by accident.
        """

        def deadline(proxy: ProxyType) -> float:
            until = self._state[_get_proxy_key(proxy)].quarantine_until
            return until if until is not None else float("inf")

        return min(self._proxies, key=deadline)

    # -- rotation --------------------------------------------------------

    def get_proxy(self) -> ProxyType:
        """Get the next active proxy according to the rotation strategy.

        The strategy always sees the full proxy list; quarantine filters its result.
        If every proxy is quarantined this returns the one closest to recovering rather
        than raising, so a total outage degrades an in-flight crawl instead of ending it.
        """
        with self._lock:
            # Bounded, not defensive: a sticky strategy that keeps returning the same
            # quarantined proxy would otherwise spin forever.
            for _ in range(len(self._proxies)):
                proxy, self._current_index = self._strategy(self._proxies, self._current_index)
                if self._is_active(proxy):
                    self._record_use(proxy)
                    return proxy

            # The strategy never surfaced an active proxy. That can mean everything is
            # quarantined, or that the strategy is pinned to a dead one while healthy
            # proxies sit idle. Prefer a working proxy over honouring the pin.
            active = [p for p in self._proxies if self._is_active(p)]
            if active:
                self._record_use(active[0])
                return active[0]

            log.warning(
                f"All {len(self._proxies)} proxies are quarantined; "
                f"reusing the one closest to recovering."
            )
            proxy = self._oldest_quarantined()
            self._record_use(proxy)
            return proxy

    # -- feedback --------------------------------------------------------

    def mark_failed(self, proxy: ProxyType) -> None:
        """Record a failure and quarantine the proxy. Unknown proxies are ignored."""
        with self._lock:
            state = self._state.get(_get_proxy_key(proxy))
            if state is None:
                return
            state.failures += 1
            if self._quarantine > 0:
                state.quarantine_until = self._clock() + self._quarantine
                log.debug(f"Proxy '{proxy}' quarantined for {self._quarantine}s")

    def mark_success(self, proxy: ProxyType) -> None:
        """Record a successful use, clearing any quarantine. Unknown proxies are ignored."""
        with self._lock:
            state = self._state.get(_get_proxy_key(proxy))
            if state is None:
                return
            state.quarantine_until = None

    def add(self, proxy: ProxyType) -> None:
        """Add a proxy to the pool at runtime."""
        with self._lock:
            key = _get_proxy_key(proxy)
            if key not in self._state:
                self._state[key] = _ProxyState()
                self._proxies.append(proxy)

    def remove(self, proxy: ProxyType) -> None:
        """Remove a proxy from the pool permanently. Unknown proxies are ignored."""
        with self._lock:
            key = _get_proxy_key(proxy)
            if self._state.pop(key, None) is None:
                return
            self._proxies = [p for p in self._proxies if _get_proxy_key(p) != key]
            if self._proxies:
                self._current_index %= len(self._proxies)

    @property
    def active_count(self) -> int:
        """Number of proxies not currently quarantined."""
        with self._lock:
            return sum(1 for p in self._proxies if self._is_active(p))

    def status(self) -> Dict[str, Dict[str, object]]:
        """Per-proxy diagnostics keyed by proxy key."""
        with self._lock:
            return {
                key: {
                    "active": state.quarantine_until is None
                    or self._clock() >= state.quarantine_until,
                    "uses": state.uses,
                    "failures": state.failures,
                    "quarantine_until": state.quarantine_until,
                }
                for key, state in self._state.items()
            }

    @property
    def proxies(self) -> List[ProxyType]:
        """Get a copy of all configured proxies."""
        return list(self._proxies)

    def __len__(self) -> int:
        """Return the total number of configured proxies."""
        return len(self._proxies)

    def __repr__(self) -> str:
        return f"ProxyRotator(proxies={len(self._proxies)})"
