"""Tests for the captcha solver's async behaviour and HTTP hardening."""

import asyncio
import inspect
import time

import pytest

from whispercrawler.core.captcha import CaptchaSolver, get_solver


class TestSolverConstruction:
    def test_unsupported_service_rejected(self):
        with pytest.raises(ValueError):
            CaptchaSolver("key", service="nope")

    def test_get_solver_returns_none_without_key(self):
        assert get_solver(None) is None

    def test_get_solver_returns_solver_with_key(self):
        assert isinstance(get_solver("key"), CaptchaSolver)


class TestAsyncSolveDoesNotBlockLoop:
    def test_async_method_exists(self):
        solver = CaptchaSolver("key")

        assert inspect.iscoroutinefunction(solver.solve_recaptcha_v2_async)

    @pytest.mark.asyncio
    async def test_async_solve_leaves_event_loop_responsive(self, monkeypatch):
        """Regression: the sync solver froze the whole event loop while polling."""
        solver = CaptchaSolver("key")

        def slow_blocking_solve(site_key, url):
            time.sleep(0.5)
            return "token"

        monkeypatch.setattr(solver, "solve_recaptcha_v2", slow_blocking_solve)

        ticks = 0

        async def heartbeat():
            nonlocal ticks
            while True:
                await asyncio.sleep(0.02)
                ticks += 1

        beat = asyncio.create_task(heartbeat())
        try:
            token = await solver.solve_recaptcha_v2_async("sitekey", "https://example.com")
        finally:
            beat.cancel()

        assert token == "token"
        # If the loop had been blocked, the heartbeat could not have run.
        assert ticks > 5


class TestHttpTimeouts:
    """Requests without a timeout can hang the solve (and the thread) forever."""

    def test_submit_and_poll_use_timeouts(self, monkeypatch):
        solver = CaptchaSolver("key")
        seen_timeouts = []

        class FakeResponse:
            def __init__(self, payload):
                self._payload = payload

            def json(self):
                return self._payload

        def fake_post(url, **kwargs):
            seen_timeouts.append(kwargs.get("timeout"))
            return FakeResponse({"status": 1, "request": "task-1"})

        def fake_get(url, **kwargs):
            seen_timeouts.append(kwargs.get("timeout"))
            return FakeResponse({"status": 1, "request": "solved-token"})

        monkeypatch.setattr(solver.session, "post", fake_post)
        monkeypatch.setattr(solver.session, "get", fake_get)
        monkeypatch.setattr("whispercrawler.core.captcha.time.sleep", lambda _s: None)

        token = solver.solve_recaptcha_v2("sitekey", "https://example.com")

        assert token == "solved-token"
        assert seen_timeouts, "no HTTP calls recorded"
        assert all(t is not None for t in seen_timeouts)

    def test_anticaptcha_uses_timeouts(self, monkeypatch):
        solver = CaptchaSolver("key", service="anticaptcha")
        seen_timeouts = []
        calls = {"n": 0}

        class FakeResponse:
            def __init__(self, payload):
                self._payload = payload

            def json(self):
                return self._payload

        def fake_post(url, **kwargs):
            seen_timeouts.append(kwargs.get("timeout"))
            calls["n"] += 1
            if calls["n"] == 1:
                return FakeResponse({"errorId": 0, "taskId": 7})
            return FakeResponse(
                {"errorId": 0, "status": "ready", "solution": {"gRecaptchaResponse": "tok"}}
            )

        monkeypatch.setattr(solver.session, "post", fake_post)
        monkeypatch.setattr("whispercrawler.core.captcha.time.sleep", lambda _s: None)

        assert solver.solve_recaptcha_v2("sitekey", "https://example.com") == "tok"
        assert all(t is not None for t in seen_timeouts)
