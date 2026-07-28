# Proxy quarantine — design

**Date:** 2026-07-28
**Status:** Approved, ready for implementation planning

## Problem

`CLAUDE.md` documents `ProxyWheel` as *"Automatic proxy rotation with quarantine for failed proxies."* The quarantine is implemented and never runs.

The codebase has two proxy classes with overlapping purpose:

| | `ProxyRotator` (`engines/toolbelt/proxy_rotation.py`) | `ProxyWheel` (`proxy.py`) |
|---|---|---|
| Used by | all 6 engine call sites | nothing |
| Proxy types | `str` or Playwright dict | `str` only |
| Strategy | pluggable callable | `Literal["round_robin","random","least_used"]` |
| Failure feedback | none | `mark_failed` + 5-minute quarantine |
| Public API | yes, `docs/api-reference/proxy-rotation.md` | yes, `whispercrawler.ProxyWheel` |

The engines already detect proxy failures — `is_proxy_error(e)` is checked at all 6 sites — but only log them. Nothing marks the proxy bad, so the rotator keeps handing out a dead proxy for the rest of the crawl.

## Decisions

1. **One class.** `ProxyRotator` gains quarantine. `ProxyWheel` becomes a deprecated shim delegating to it.
2. **Degrade, never raise.** When every proxy is quarantined, serve the longest-quarantined one and log a warning.
3. **Strategy contract is untouched.** Strategies keep receiving the full proxy list; quarantine filters the result.

## 1. `ProxyRotator` changes

`engines/toolbelt/proxy_rotation.py`.

### Public surface

```python
class ProxyRotator:
    def __init__(
        self,
        proxies: List[ProxyType],
        strategy: RotationStrategy = cyclic_rotation,
        quarantine_seconds: float = 300.0,
    ): ...

    def get_proxy(self) -> ProxyType: ...        # existing name, new filtering
    def mark_failed(self, proxy: ProxyType) -> None: ...
    def mark_success(self, proxy: ProxyType) -> None: ...
    def add(self, proxy: ProxyType) -> None: ...
    def remove(self, proxy: ProxyType) -> None: ...

    @property
    def active_count(self) -> int: ...
    def status(self) -> Dict[str, Dict[str, object]]: ...
```

`quarantine_seconds=0` disables quarantine entirely: `mark_failed` still counts the failure but never withholds the proxy.

Existing members (`proxies`, `__len__`, `__repr__`) are unchanged.

### State

Per-proxy state is keyed by `_get_proxy_key(proxy)` — the existing `server|username` helper — **not** by the proxy object. Playwright dict proxies are unhashable, so a `dict[proxy, state]` map is not possible. Two dicts sharing a server but differing in username are distinct entries.

State per proxy: `uses`, `failures`, `quarantine_until` (a monotonic deadline, or `None`).

`__slots__` must be extended with the new state field. It currently reads
`("_proxies", "_proxy_to_index", "_strategy", "_current_index", "_lock")`.

Private helpers referenced by the pseudocode below, none of them public API:

| helper | purpose |
|---|---|
| `_is_active(proxy)` | `quarantine_until is None or _clock() >= quarantine_until` |
| `_record_use(proxy)` | increment `uses` |
| `_uses_of(proxy)` | read `uses`; used by the `least_used` closure in section 3 |
| `_oldest_quarantined()` | proxy with the earliest `quarantine_until` |

### Clock

The rotator takes a private `_clock` parameter defaulting to `time.monotonic`. Tests substitute it to exercise expiry without sleeping.

This is deliberately **not** `datetime.now(timezone.utc)`, which is what `ProxyWheel` uses today: a wall clock can step backwards on an NTP correction and either extend a quarantine indefinitely or end one early. `time.monotonic` cannot.

`_clock` is underscore-prefixed and excluded from the public docs.

### `get_proxy()`

```python
with self._lock:
    for _ in range(len(self._proxies)):
        proxy, self._current_index = self._strategy(self._proxies, self._current_index)
        if self._is_active(proxy):
            self._record_use(proxy)
            return proxy
    log.warning("all %d proxies quarantined, reusing oldest failure", len(self._proxies))
    return self._oldest_quarantined()
```

The `len(self._proxies)` bound is required, not defensive: a sticky strategy such as `lambda proxies, idx: (proxies[0], idx)` would otherwise loop forever once `proxies[0]` is quarantined.

`_oldest_quarantined()` returns the proxy with the earliest `quarantine_until`. It also records a use, so `status()` stays accurate.

### Locking

`_lock` changes from `threading.Lock` to `threading.RLock`.

`get_proxy()` holds the lock while calling the strategy. The `least_used` strategy needed by the `ProxyWheel` shim is a closure that calls back into the rotator, which self-deadlocks under a non-reentrant lock. `RLock` also removes the same footgun for any user strategy that touches the rotator — latent today only because no strategy does.

### No escalating backoff

`failures` is a diagnostic counter. Repeat failures do not lengthen the quarantine. Consequently nothing needs to call `mark_success` to reset it, which keeps that method off the engines' hot path. Escalation can be added later without changing any of the interfaces above.

## 2. Engine wiring

### New helper

In `engines/toolbelt/proxy_rotation.py`:

```python
def report_proxy_failure(
    rotator: Optional[ProxyRotator],
    proxy: Optional[ProxyType],
    error: Exception,
) -> bool:
    """Quarantine `proxy` if `error` looks proxy-related. Returns whether it did."""
    if not is_proxy_error(error):
        return False
    if rotator is not None and proxy is not None:
        rotator.mark_failed(proxy)
    return True
```

It subsumes the existing `is_proxy_error(e)` call rather than adding a second one.

### Call sites

Six, all structurally identical:

| File | Sync | Async |
|---|---|---|
| `engines/static.py` | ~line 283 | ~line 513 |
| `engines/_browsers/_controllers.py` | ~line 200 | ~line 387 |
| `engines/_browsers/_stealth.py` | ~line 394 | ~line 762 |

Each becomes:

```python
except Exception as e:
    page_info.mark_error()                      # browser engines only
    proxy_failed = report_proxy_failure(rotator, proxy, e)
    if attempt < retries - 1:
        if proxy_failed:
            log.warning(f"Proxy '{proxy}' failed (attempt {attempt + 1}) | Retrying in ...")
        else:
            log.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in ...")
        sleep(retry_delay)
    else:
        log.error(f"Failed after {retries} attempts: {e}")
        raise
```

**The call must sit above the `if attempt < retries - 1` check.** Today `is_proxy_error(e)` is nested *inside* that branch, so on the final attempt a proxy error skips it and re-raises. Hanging quarantine off the existing check would mean a proxy that fails on its last permitted attempt is never quarantined — the case that most warrants it.

The rotator is passed in rather than read from `self`, because `static.py` stores it as `self._proxy_rotator` while the browser engines use `self._config.proxy_rotator`.

When a user supplies a static `proxy=` and no rotator, `rotator is None` makes the call a no-op that still returns the correct bool for the log message.

## 3. `ProxyWheel` deprecation

`proxy.py`. `ProxyWheel` becomes a subclass of `ProxyRotator` that emits a `DeprecationWarning` on construction naming `ProxyRotator` as the replacement, and translates its API:

| `ProxyWheel` | maps to |
|---|---|
| `next()` | `get_proxy()` |
| `all_proxies` | `proxies` |
| `strategy="round_robin"` | `cyclic_rotation` |
| `strategy="random"` | new `random_rotation` built-in |
| `strategy="least_used"` | closure over the rotator (below) |
| `add()`, `remove()` | inherited (new on `ProxyRotator`) |
| `mark_failed`, `mark_success`, `active_count`, `status()` | inherited |

`least_used` cannot be a plain strategy — the `Callable[[List[ProxyType], int], Tuple[ProxyType, int]]` signature gives a strategy no access to use counts. It is instead built as a closure over the rotator instance:

```python
def _least_used_strategy(rotator: "ProxyRotator") -> RotationStrategy:
    def strategy(proxies, idx):
        return min(proxies, key=rotator._uses_of), idx
    return strategy
```

This stays within the published contract — it is still just a callable — so section 1 is unaffected. It is the reason `_lock` must be an `RLock`.

The shim adds no features. `ProxyWheel` has zero consumers in this codebase; it exists solely for anyone who imported `whispercrawler.ProxyWheel` from the public API. Removal target: the next minor release after this ships.

`_QUARANTINE_DURATION = timedelta(minutes=5)` in `proxy.py` is replaced by the `quarantine_seconds=300.0` default; `ProxyWheel` passes nothing and inherits it, preserving its current behaviour.

## 4. Testing

### Unit — rotator quarantine

- a failed proxy is skipped by `get_proxy()`
- quarantine expires after `quarantine_seconds` (fake `_clock`, no sleeping)
- all-quarantined returns the oldest and logs a warning, and does **not** raise
- "oldest" is the earliest `quarantine_until`
- `quarantine_seconds=0` disables withholding
- dict proxies quarantine by `server|username`; same server, different username stay distinct
- `mark_failed` on an unknown proxy is a silent no-op
- a sticky strategy aimed at a quarantined proxy terminates via the `len(proxies)` bound

### Unit — contract preservation

- an explicit assertion that the strategy receives the **full** proxy list, not a filtered one
- **the existing 39 tests in `tests/fetchers/test_proxy_rotation.py` must pass unmodified.** This is the primary regression signal for section 1.

### Unit — helper

`report_proxy_failure` across: proxy error with rotator; non-proxy error; `rotator=None`; `proxy=None`.

### Unit — shim

- `DeprecationWarning` is emitted
- `next()` agrees with `get_proxy()`
- all three named strategies resolve
- `least_used` selects the fewest-used proxy — this test deadlocks under the old non-reentrant `Lock`, so it is also the regression test for the `RLock` change

### End-to-end — no external network

Point a rotator at `http://127.0.0.1:1` (nothing listening) and issue a real `Fetcher.get` through it. curl fails with "Failed to connect", `is_proxy_error` matches it, and the assertion is that `rotator.status()` reports the proxy quarantined. This exercises the real `static.py` retry loop rather than a stand-in.

### Known coverage gap

The four browser call sites in `_controllers.py` and `_stealth.py` are single-line calls to a unit-tested helper, at sites structurally identical to the static one covered end-to-end. Verifying them properly requires browsers and a working proxy; they are not covered by this work and should not be described as verified.

## Out of scope

- Escalating or per-proxy quarantine durations
- Health checks or proactive proxy probing
- Wiring `mark_success` into the engines' success path
- Any change to `is_proxy_error`'s detection strings
