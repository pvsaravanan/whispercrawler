"""Quarantine behaviour on ProxyRotator.

Time is injected via the private `_clock` seam so expiry is deterministic and
no test has to sleep.
"""

import pytest

from whispercrawler.engines.toolbelt.proxy_rotation import ProxyRotator, cyclic_rotation


class FakeClock:
    """Monotonic clock under test control."""

    def __init__(self, start: float = 1000.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _rotator(proxies=None, **kwargs):
    return ProxyRotator(proxies or ["http://p1:8080", "http://p2:8080"], **kwargs)


class TestQuarantineBasics:
    def test_failed_proxy_is_skipped(self):
        rotator = _rotator()

        rotator.mark_failed("http://p1:8080")

        assert {rotator.get_proxy() for _ in range(6)} == {"http://p2:8080"}

    def test_quarantine_expires(self):
        clock = FakeClock()
        rotator = _rotator(quarantine_seconds=300, _clock=clock)
        rotator.mark_failed("http://p1:8080")
        assert rotator.get_proxy() == "http://p2:8080"

        clock.advance(301)

        assert {rotator.get_proxy() for _ in range(4)} == {"http://p1:8080", "http://p2:8080"}

    def test_quarantine_still_active_just_before_expiry(self):
        clock = FakeClock()
        rotator = _rotator(quarantine_seconds=300, _clock=clock)
        rotator.mark_failed("http://p1:8080")

        clock.advance(299)

        assert {rotator.get_proxy() for _ in range(4)} == {"http://p2:8080"}

    def test_active_count_reflects_quarantine(self):
        rotator = _rotator()
        assert rotator.active_count == 2

        rotator.mark_failed("http://p1:8080")

        assert rotator.active_count == 1

    def test_mark_failed_on_unknown_proxy_is_a_no_op(self):
        rotator = _rotator()

        rotator.mark_failed("http://never-configured:9999")

        assert rotator.active_count == 2

    def test_quarantine_seconds_zero_disables_withholding(self):
        rotator = _rotator(quarantine_seconds=0)

        rotator.mark_failed("http://p1:8080")

        assert rotator.active_count == 2
        assert {rotator.get_proxy() for _ in range(4)} == {"http://p1:8080", "http://p2:8080"}
        # The failure is still counted, it just does not withhold the proxy.
        assert rotator.status()["http://p1:8080"]["failures"] == 1


class TestAllQuarantined:
    """Degrade rather than raise - a total outage must not kill an in-flight crawl."""

    def test_serves_oldest_quarantined_instead_of_raising(self):
        clock = FakeClock()
        rotator = _rotator(_clock=clock)

        rotator.mark_failed("http://p1:8080")
        clock.advance(10)
        rotator.mark_failed("http://p2:8080")

        # p1 was quarantined first, so its deadline is the earliest.
        assert rotator.get_proxy() == "http://p1:8080"

    def test_warns_when_all_quarantined(self, caplog):
        import logging

        rotator = _rotator()
        rotator.mark_failed("http://p1:8080")
        rotator.mark_failed("http://p2:8080")

        with caplog.at_level(logging.WARNING):
            rotator.get_proxy()

        assert any("quarantined" in record.message.lower() for record in caplog.records)

    def test_recovers_once_a_quarantine_expires(self):
        clock = FakeClock()
        rotator = _rotator(quarantine_seconds=300, _clock=clock)
        rotator.mark_failed("http://p1:8080")
        clock.advance(100)
        rotator.mark_failed("http://p2:8080")

        clock.advance(201)  # p1 free at 1300, now 1301; p2 free at 1400

        assert {rotator.get_proxy() for _ in range(4)} == {"http://p1:8080"}


class TestStrategyContractPreserved:
    """Quarantine filters the strategy's result, never its input."""

    def test_strategy_receives_the_full_proxy_list(self):
        seen = []

        def recording_strategy(proxies, idx):
            seen.append(list(proxies))
            return cyclic_rotation(proxies, idx)

        rotator = _rotator(strategy=recording_strategy)
        rotator.mark_failed("http://p1:8080")
        rotator.get_proxy()

        assert seen, "strategy was never called"
        assert all(len(batch) == 2 for batch in seen)

    def test_sticky_strategy_pinned_to_dead_proxy_yields_a_healthy_one(self):
        """Without a bounded retry this spins forever.

        The strategy is pinned to p1, which is quarantined, while p2 is healthy.
        Honouring the pin would hand back a proxy known to be dead, so an active
        proxy wins over the strategy's preference.
        """
        rotator = _rotator(strategy=lambda proxies, idx: (proxies[0], idx))
        rotator.mark_failed("http://p1:8080")

        assert rotator.get_proxy() == "http://p2:8080"

    def test_sticky_strategy_with_everything_quarantined_terminates(self):
        rotator = _rotator(strategy=lambda proxies, idx: (proxies[0], idx))
        rotator.mark_failed("http://p1:8080")
        rotator.mark_failed("http://p2:8080")

        assert rotator.get_proxy() in {"http://p1:8080", "http://p2:8080"}


class TestDictProxies:
    def test_dict_proxy_can_be_quarantined(self):
        proxies = [{"server": "http://p1:8080"}, {"server": "http://p2:8080"}]
        rotator = ProxyRotator(proxies)

        rotator.mark_failed({"server": "http://p1:8080"})

        assert rotator.active_count == 1
        assert rotator.get_proxy() == {"server": "http://p2:8080"}

    def test_same_server_different_username_are_distinct(self):
        a = {"server": "http://p:8080", "username": "alice"}
        b = {"server": "http://p:8080", "username": "bob"}
        rotator = ProxyRotator([a, b])

        rotator.mark_failed(a)

        assert rotator.active_count == 1
        assert rotator.get_proxy() == b


class TestStatus:
    def test_status_reports_state_per_proxy(self):
        rotator = _rotator()
        rotator.get_proxy()
        rotator.mark_failed("http://p1:8080")

        status = rotator.status()

        assert set(status) == {"http://p1:8080", "http://p2:8080"}
        assert status["http://p1:8080"]["active"] is False
        assert status["http://p1:8080"]["failures"] == 1
        assert status["http://p2:8080"]["active"] is True

    def test_reports_seconds_remaining_not_a_raw_deadline(self):
        """A monotonic deadline is not interpretable on its own.

        `quarantine_seconds_remaining` is a duration the caller can act on directly.
        """
        clock = FakeClock()
        rotator = _rotator(quarantine_seconds=300, _clock=clock)
        rotator.mark_failed("http://p1:8080")

        clock.advance(120)

        entry = rotator.status()["http://p1:8080"]
        assert entry["quarantine_seconds_remaining"] == pytest.approx(180.0)
        assert "quarantine_until" not in entry

    def test_active_proxy_has_no_remaining_time(self):
        assert _rotator().status()["http://p1:8080"]["quarantine_seconds_remaining"] is None

    def test_expired_quarantine_reports_none_not_a_negative(self):
        """`active` and `quarantine_seconds_remaining` must never disagree."""
        clock = FakeClock()
        rotator = _rotator(quarantine_seconds=300, _clock=clock)
        rotator.mark_failed("http://p1:8080")

        clock.advance(400)  # deadline passed, but the field was never cleared

        entry = rotator.status()["http://p1:8080"]
        assert entry["active"] is True
        assert entry["quarantine_seconds_remaining"] is None

    def test_remaining_time_counts_down(self):
        clock = FakeClock()
        rotator = _rotator(quarantine_seconds=100, _clock=clock)
        rotator.mark_failed("http://p1:8080")

        first = rotator.status()["http://p1:8080"]["quarantine_seconds_remaining"]
        clock.advance(30)
        second = rotator.status()["http://p1:8080"]["quarantine_seconds_remaining"]

        assert first == pytest.approx(100.0)
        assert second == pytest.approx(70.0)

    def test_quarantine_disabled_never_reports_remaining_time(self):
        rotator = _rotator(quarantine_seconds=0)

        rotator.mark_failed("http://p1:8080")

        entry = rotator.status()["http://p1:8080"]
        assert entry["failures"] == 1
        assert entry["quarantine_seconds_remaining"] is None


class TestAddRemove:
    def test_add_makes_a_proxy_available(self):
        rotator = ProxyRotator(["http://p1:8080"])

        rotator.add("http://p2:8080")

        assert len(rotator) == 2
        assert {rotator.get_proxy() for _ in range(4)} == {"http://p1:8080", "http://p2:8080"}

    def test_remove_takes_a_proxy_out_of_rotation(self):
        rotator = _rotator()

        rotator.remove("http://p1:8080")

        assert len(rotator) == 1
        assert {rotator.get_proxy() for _ in range(4)} == {"http://p2:8080"}

    def test_remove_unknown_proxy_is_a_no_op(self):
        rotator = _rotator()

        rotator.remove("http://never-configured:9999")

        assert len(rotator) == 2


class TestMarkSuccess:
    def test_mark_success_clears_quarantine(self):
        rotator = _rotator()
        rotator.mark_failed("http://p1:8080")
        assert rotator.active_count == 1

        rotator.mark_success("http://p1:8080")

        assert rotator.active_count == 2

    def test_mark_success_on_unknown_proxy_is_a_no_op(self):
        rotator = _rotator()

        rotator.mark_success("http://never-configured:9999")

        assert rotator.active_count == 2


class TestThreadSafety:
    def test_concurrent_get_and_mark_failed(self):
        from concurrent.futures import ThreadPoolExecutor

        proxies = [f"http://p{i}:8080" for i in range(10)]
        rotator = ProxyRotator(proxies)

        def churn(i):
            proxy = rotator.get_proxy()
            if i % 3 == 0:
                rotator.mark_failed(proxy)
            return proxy

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(churn, range(200)))

        assert len(results) == 200
        assert all(p in proxies for p in results)

    def test_strategy_may_call_back_into_the_rotator(self):
        """The least_used strategy does exactly this, so the lock must be reentrant."""

        rotator = ProxyRotator(["http://p1:8080", "http://p2:8080"])
        rotator._strategy = lambda proxies, idx: (min(proxies, key=rotator._uses_of), idx)

        # Deadlocks under a non-reentrant Lock.
        assert rotator.get_proxy() in {"http://p1:8080", "http://p2:8080"}


class TestQuarantineValidation:
    def test_negative_quarantine_is_rejected(self):
        with pytest.raises(ValueError, match="quarantine_seconds"):
            _rotator(quarantine_seconds=-1)
