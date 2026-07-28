"""Tests for retries validation in the static fetcher."""

import pytest

from whispercrawler.fetchers import AsyncFetcher, Fetcher


class TestRetriesValidation:
    """retries must be >= 1 (it counts attempts, matching the browser config's ge=1)."""

    @pytest.mark.parametrize("bad", [0, -1, -10])
    def test_non_positive_retries_rejected(self, bad):
        """Regression: retries=0 ran zero requests and raised a misleading
        'No active session available' error."""
        with pytest.raises(ValueError) as exc:
            Fetcher.get("https://example.com", retries=bad)

        assert "retries" in str(exc.value).lower()

    def test_error_message_is_actionable(self):
        with pytest.raises(ValueError) as exc:
            Fetcher.get("https://example.com", retries=0)

        message = str(exc.value)
        assert "No active session available" not in message

    @pytest.mark.asyncio
    @pytest.mark.parametrize("bad", [0, -1])
    async def test_async_non_positive_retries_rejected(self, bad):
        with pytest.raises(ValueError) as exc:
            await AsyncFetcher.get("https://example.com", retries=bad)

        assert "retries" in str(exc.value).lower()
