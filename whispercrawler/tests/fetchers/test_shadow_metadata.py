"""Tests for ShadowFetcher's HTTP metadata extraction."""

from whispercrawler.fetchers.shadow import _response_metadata


class FakeRequest:
    def __init__(self, headers=None):
        self.headers = headers or {"user-agent": "camoufox"}


class FakeNavResponse:
    def __init__(self, status=200, status_text="OK", headers=None, request=None):
        self.status = status
        self.status_text = status_text
        self.headers = headers or {"content-type": "text/html"}
        self.request = request or FakeRequest()


class TestResponseMetadata:
    def test_reads_real_status(self):
        status, _reason, _headers, _req_headers = _response_metadata(FakeNavResponse(status=404))

        assert status == 404

    def test_reads_real_headers(self):
        _s, _r, headers, _rh = _response_metadata(
            FakeNavResponse(headers={"content-type": "application/json"})
        )

        assert headers == {"content-type": "application/json"}

    def test_reads_request_headers(self):
        _s, _r, _h, req_headers = _response_metadata(
            FakeNavResponse(request=FakeRequest({"accept": "*/*"}))
        )

        assert req_headers == {"accept": "*/*"}

    def test_reads_status_text_as_reason(self):
        _s, reason, _h, _rh = _response_metadata(
            FakeNavResponse(status=500, status_text="Internal Server Error")
        )

        assert reason == "Internal Server Error"

    def test_server_error_is_not_reported_as_success(self):
        """Regression: every fetch used to report 200 regardless of the real outcome."""
        status, _r, _h, _rh = _response_metadata(FakeNavResponse(status=503))

        assert status == 503

    def test_blank_status_text_falls_back(self):
        _s, reason, _h, _rh = _response_metadata(FakeNavResponse(status=200, status_text=""))

        assert reason == "OK"

    def test_none_response_falls_back_to_defaults(self):
        """page.goto() returns None for same-document navigations."""
        status, reason, headers, req_headers = _response_metadata(None)

        assert status == 200
        assert reason == "OK"
        assert headers == {}
        assert req_headers == {}

    def test_unreadable_response_falls_back(self):
        """A response object whose attributes raise must not break the fetch."""

        class Exploding:
            @property
            def status(self):
                raise RuntimeError("target closed")

        status, reason, headers, req_headers = _response_metadata(Exploding())

        assert status == 200
        assert reason == "OK"
        assert headers == {}
        assert req_headers == {}
