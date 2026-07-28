import pytest

from whispercrawler.engines._browsers._validators import (
    PlaywrightConfig,
    StealthConfig,
    validate,
    validate_fetch,
)


class _FakeSession:
    """Stand-in for a browser session, which validate_fetch reads defaults from."""

    def __init__(self, config):
        self._config = config


class TestValidators:
    """Test configuration validators"""

    def test_playwright_config_valid(self):
        """Test valid PlaywrightConfig"""
        params = {
            "max_pages": 2,
            "headless": True,
            "timeout": 30000,
            "proxy": "http://proxy.example.com:8080",
        }

        config = validate(params, PlaywrightConfig)

        assert config.max_pages == 2
        assert config.headless is True
        assert config.timeout == 30000
        assert isinstance(config.proxy, dict)

    def test_playwright_config_invalid_max_pages(self):
        """Test PlaywrightConfig with invalid max_pages"""
        params = {"max_pages": 0}

        with pytest.raises(TypeError):
            validate(params, PlaywrightConfig)

        params = {"max_pages": 51}

        with pytest.raises(TypeError):
            validate(params, PlaywrightConfig)

    def test_playwright_config_invalid_timeout(self):
        """Test PlaywrightConfig with an invalid timeout"""
        params = {"timeout": -1}

        with pytest.raises(TypeError):
            validate(params, PlaywrightConfig)

    def test_playwright_config_invalid_cdp_url(self):
        """Test PlaywrightConfig with invalid CDP URL"""
        params = {"cdp_url": "invalid-url"}

        with pytest.raises(TypeError):
            validate(params, PlaywrightConfig)

    def test_stealth_config_valid(self):
        """Test valid StealthConfig"""
        params = {"max_pages": 1, "headless": True, "solve_cloudflare": False, "timeout": 30000}

        config = validate(params, StealthConfig)

        assert config.max_pages == 1
        assert config.headless is True
        assert config.solve_cloudflare is False
        assert config.timeout == 30000

    def test_stealth_config_cloudflare_timeout(self):
        """Test StealthConfig timeout adjustment for Cloudflare"""
        params = {
            "solve_cloudflare": True,
            "timeout": 10000,  # Less than the required 60,000
        }

        config = validate(params, StealthConfig)

        assert config.timeout == 60000  # Should be increased

    def test_playwright_config_blocked_domains(self):
        """Test PlaywrightConfig with blocked_domains"""
        params = {"blocked_domains": {"ads.example.com", "tracker.io"}}

        config = validate(params, PlaywrightConfig)

        assert config.blocked_domains == {"ads.example.com", "tracker.io"}

    def test_playwright_config_blocked_domains_default_none(self):
        """Test PlaywrightConfig blocked_domains defaults to None"""
        config = validate({}, PlaywrightConfig)

        assert config.blocked_domains is None

    def test_stealth_config_blocked_domains(self):
        """Test StealthConfig inherits blocked_domains"""
        params = {"blocked_domains": {"ads.example.com"}}

        config = validate(params, StealthConfig)

        assert config.blocked_domains == {"ads.example.com"}


class TestValidateFetchCaptchaDefaults:
    """Captcha settings live only on StealthConfig, but every `fetch` call builds the
    same `_fetch_params`. The Playwright path must still get usable defaults."""

    def test_playwright_fetch_defaults_captcha_fields(self):
        """Regression: DynamicFetcher raised TypeError on every fetch."""
        session = _FakeSession(validate({}, PlaywrightConfig))

        params = validate_fetch({}, session, PlaywrightConfig)

        assert params.captcha_api_key is None
        assert params.captcha_service == "2captcha"

    def test_stealth_fetch_reads_captcha_from_session_config(self):
        params = {"captcha_api_key": "sess-key", "captcha_service": "anticaptcha"}
        session = _FakeSession(validate(params, StealthConfig))

        params = validate_fetch({}, session, StealthConfig)

        assert params.captcha_api_key == "sess-key"
        assert params.captcha_service == "anticaptcha"

    def test_stealth_fetch_captcha_override_wins_over_session(self):
        session = _FakeSession(validate({"captcha_api_key": "sess-key"}, StealthConfig))

        params = validate_fetch({"captcha_api_key": "call-key"}, session, StealthConfig)

        assert params.captcha_api_key == "call-key"
