"""Coordinate maths for the Cloudflare challenge click."""

from whispercrawler.engines._browsers._stealth import _captcha_click_point


class TestCaptchaClickPoint:
    """Playwright's `bounding_box()` returns None for an element that is not
    visible, so the challenge box is not guaranteed to exist by the time the
    solver wants to click it."""

    def test_returns_point_inside_the_box(self):
        point = _captcha_click_point({"x": 100.0, "y": 200.0, "width": 300.0, "height": 65.0})

        assert point is not None
        x, y = point
        # Offsets are randomised, so assert the point lands in the expected band.
        assert 126.0 <= x <= 128.0
        assert 225.0 <= y <= 227.0

    def test_handles_origin_box(self):
        point = _captcha_click_point({"x": 0.0, "y": 0.0, "width": 300.0, "height": 65.0})

        assert point is not None
        x, y = point
        assert 26.0 <= x <= 28.0
        assert 25.0 <= y <= 27.0

    def test_missing_box_returns_none(self):
        """Regression: this used to raise TypeError: 'NoneType' is not subscriptable."""
        assert _captcha_click_point(None) is None

    def test_empty_box_returns_none(self):
        """The solver seeds `outer_box` with {} before the iframe lookup."""
        assert _captcha_click_point({}) is None
