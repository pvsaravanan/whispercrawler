from whispercrawler.engines.constants import (
    DEFAULT_ARGS,
    EXTRA_RESOURCES,
    HARMFUL_ARGS,
    STEALTH_ARGS,
)


class TestConstants:
    """Test constant values"""

    def test_default_disabled_resources(self):
        """Test default disabled resources"""
        assert "image" in EXTRA_RESOURCES
        assert "font" in EXTRA_RESOURCES
        assert "stylesheet" in EXTRA_RESOURCES
        assert "media" in EXTRA_RESOURCES

    def test_harmful_default_args(self):
        """Test harmful default arguments"""
        assert "--enable-automation" in HARMFUL_ARGS
        assert "--disable-popup-blocking" in HARMFUL_ARGS

    def test_flags(self):
        """Test default stealth flags"""
        assert "--no-pings" in DEFAULT_ARGS
        # assert "--incognito" in STEALTH_ARGS
        assert "--disable-blink-features=AutomationControlled" in STEALTH_ARGS
