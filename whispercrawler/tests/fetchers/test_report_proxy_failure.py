"""The shared hook the engines use to quarantine a proxy on failure."""

from whispercrawler.engines.toolbelt.proxy_rotation import ProxyRotator, report_proxy_failure

PROXY_ERROR = Exception("Failed to connect to proxy server")
OTHER_ERROR = Exception("404 Not Found")


def _rotator():
    return ProxyRotator(["http://p1:8080", "http://p2:8080"])


class TestReportProxyFailure:
    def test_proxy_error_quarantines_and_reports_true(self):
        rotator = _rotator()

        assert report_proxy_failure(rotator, "http://p1:8080", PROXY_ERROR) is True
        assert rotator.active_count == 1

    def test_non_proxy_error_leaves_the_pool_alone(self):
        rotator = _rotator()

        assert report_proxy_failure(rotator, "http://p1:8080", OTHER_ERROR) is False
        assert rotator.active_count == 2

    def test_no_rotator_still_classifies_the_error(self):
        """A static `proxy=` with no rotator: nothing to quarantine, but the caller
        still needs to know which log line to emit."""
        assert report_proxy_failure(None, "http://p1:8080", PROXY_ERROR) is True
        assert report_proxy_failure(None, "http://p1:8080", OTHER_ERROR) is False

    def test_no_proxy_is_safe(self):
        rotator = _rotator()

        assert report_proxy_failure(rotator, None, PROXY_ERROR) is True
        assert rotator.active_count == 2

    def test_unknown_proxy_is_safe(self):
        rotator = _rotator()

        assert report_proxy_failure(rotator, "http://never-configured:1", PROXY_ERROR) is True
        assert rotator.active_count == 2

    def test_dict_proxy_is_quarantined(self):
        rotator = ProxyRotator([{"server": "http://p1:8080"}, {"server": "http://p2:8080"}])

        report_proxy_failure(rotator, {"server": "http://p1:8080"}, PROXY_ERROR)

        assert rotator.active_count == 1
