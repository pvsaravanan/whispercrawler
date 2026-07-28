"""End-to-end quarantine through the real static fetcher.

No external network: the proxy points at a local port with nothing listening, so
curl fails to connect and the engine's real retry handler runs.
"""

import pytest
from curl_cffi.requests.exceptions import ConnectionError as CurlConnectionError

from whispercrawler.engines.toolbelt.proxy_rotation import ProxyRotator
from whispercrawler.fetchers import FetcherSession

DEAD_PROXY = "http://127.0.0.1:1"


class TestQuarantineThroughStaticFetcher:
    def test_dead_proxy_is_quarantined_on_the_final_attempt(self):
        """`retries=1` makes the only attempt the final one.

        Regression: the engines checked `is_proxy_error` inside
        `if attempt < retries - 1`, so a proxy failing on its last permitted attempt
        was never quarantined - exactly the case that most warrants it.
        """
        rotator = ProxyRotator([DEAD_PROXY])

        with FetcherSession(proxy_rotator=rotator, retries=1, retry_delay=0, timeout=5) as session:
            with pytest.raises(CurlConnectionError):
                session.get("http://example.com")

        status = rotator.status()[DEAD_PROXY]
        assert status["failures"] == 1
        assert status["active"] is False
        assert rotator.active_count == 0

    def test_healthy_proxy_is_preferred_after_one_goes_bad(self):
        """With a second proxy configured, the dead one drops out of rotation."""
        healthy = "http://127.0.0.2:1"
        rotator = ProxyRotator([DEAD_PROXY, healthy])
        rotator.mark_failed(DEAD_PROXY)

        assert rotator.active_count == 1
        assert {rotator.get_proxy() for _ in range(6)} == {healthy}
