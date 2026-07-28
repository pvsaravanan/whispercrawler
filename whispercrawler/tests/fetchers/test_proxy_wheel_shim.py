"""ProxyWheel is a deprecated shim over ProxyRotator."""

import pytest

from whispercrawler.engines.toolbelt.proxy_rotation import ProxyRotator
from whispercrawler.proxy import ProxyWheel

PROXIES = ["http://p1:8080", "http://p2:8080", "http://p3:8080"]


def _wheel(**kwargs):
    with pytest.warns(DeprecationWarning):
        return ProxyWheel(PROXIES, **kwargs)


class TestDeprecation:
    def test_construction_warns_and_names_the_replacement(self):
        with pytest.warns(DeprecationWarning, match="ProxyRotator"):
            ProxyWheel(PROXIES)

    def test_is_a_proxy_rotator(self):
        assert isinstance(_wheel(), ProxyRotator)


class TestApiTranslation:
    def test_next_matches_get_proxy(self):
        wheel = _wheel()

        assert wheel.next() == "http://p1:8080"
        assert wheel.get_proxy() == "http://p2:8080"

    def test_all_proxies(self):
        assert _wheel().all_proxies == PROXIES

    def test_len_and_active_count(self):
        wheel = _wheel()

        assert len(wheel) == 3
        assert wheel.active_count == 3


class TestNamedStrategies:
    def test_round_robin_is_the_default(self):
        wheel = _wheel()

        assert [wheel.next() for _ in range(4)] == [
            "http://p1:8080",
            "http://p2:8080",
            "http://p3:8080",
            "http://p1:8080",
        ]

    def test_random_stays_in_the_pool(self):
        wheel = _wheel(strategy="random")

        assert all(wheel.next() in PROXIES for _ in range(20))

    def test_least_used_picks_the_least_used(self):
        """Exercises the strategy-calls-back-into-the-rotator path.

        This deadlocks if the rotator's lock is not reentrant.
        """
        wheel = _wheel(strategy="least_used")

        picked = [wheel.next() for _ in range(3)]

        assert sorted(picked) == sorted(PROXIES)

    def test_unknown_strategy_name_is_rejected(self):
        with pytest.warns(DeprecationWarning), pytest.raises(ValueError, match="strategy"):
            ProxyWheel(PROXIES, strategy="nonsense")


class TestQuarantineInherited:
    def test_mark_failed_withholds_the_proxy(self):
        wheel = _wheel()

        wheel.mark_failed("http://p1:8080")

        assert wheel.active_count == 2
        assert "http://p1:8080" not in {wheel.next() for _ in range(6)}

    def test_status_reports_failures(self):
        wheel = _wheel()

        wheel.mark_failed("http://p1:8080")

        assert wheel.status()["http://p1:8080"]["failures"] == 1

    def test_add_and_remove(self):
        wheel = _wheel()

        wheel.add("http://p4:8080")
        assert len(wheel) == 4

        wheel.remove("http://p4:8080")
        assert len(wheel) == 3
