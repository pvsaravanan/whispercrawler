import asyncio
import time

import requests

#: Per-request network timeout. Without it a hung service pins the calling thread
#: (and, before the async wrapper below, the whole event loop) indefinitely.
HTTP_TIMEOUT = 30


class CaptchaServiceError(Exception):
    """Base exception for captcha service errors."""

    pass


class CaptchaSolver:
    """Interface for third-party captcha solving services (2Captcha, Anti-Captcha)."""

    def __init__(self, api_key: str, service: str = "2captcha"):
        self.api_key = api_key
        self.service = service.lower()
        self.session = requests.Session()

        if self.service == "2captcha":
            self.base_url = "https://2captcha.com"
        elif self.service == "anticaptcha":
            self.base_url = "https://api.anti-captcha.com"
        else:
            raise ValueError(f"Unsupported captcha service: {service}")

    def solve_recaptcha_v2(self, site_key: str, url: str) -> str:
        """Solve Google ReCaptcha V2.

        Blocking: polls the service for up to ~150s. Call `solve_recaptcha_v2_async`
        from async code instead.
        """
        if self.service == "2captcha":
            return self._solve_2captcha(site_key, url, method="userrecaptcha")
        else:
            return self._solve_anticaptcha(site_key, url, task_type="NoCaptchaTaskProxyless")

    async def solve_recaptcha_v2_async(self, site_key: str, url: str) -> str:
        """Async-safe wrapper around `solve_recaptcha_v2`.

        The underlying services are polled over blocking HTTP with sleeps between
        attempts. Running that directly on the event loop would freeze every other
        in-flight request for the duration, so it is offloaded to a worker thread.
        """
        return await asyncio.to_thread(self.solve_recaptcha_v2, site_key, url)

    def _solve_2captcha(self, site_key: str, url: str, method: str) -> str:
        # Step 1: Submit request
        resp = self.session.post(
            f"{self.base_url}/in.php",
            data={
                "key": self.api_key,
                "method": method,
                "googlekey": site_key,
                "pageurl": url,
                "json": 1,
            },
            timeout=HTTP_TIMEOUT,
        )

        data = resp.json()
        if data.get("status") != 1:
            raise CaptchaServiceError(f"2Captcha submission failed: {data.get('request')}")

        request_id = data.get("request")

        # Step 2: Poll for result
        for _ in range(30):  # Poll for up to 150 seconds
            time.sleep(5)
            resp = self.session.get(
                f"{self.base_url}/res.php",
                params={"key": self.api_key, "action": "get", "id": request_id, "json": 1},
                timeout=HTTP_TIMEOUT,
            )
            data = resp.json()
            if data.get("status") == 1:
                return data.get("request")
            if data.get("request") == "CAPCHA_NOT_READY":
                continue
            raise CaptchaServiceError(f"2Captcha failed: {data.get('request')}")

        raise CaptchaServiceError("2Captcha timeout")

    def _solve_anticaptcha(self, site_key: str, url: str, task_type: str) -> str:
        # Step 1: Create Task
        resp = self.session.post(
            f"{self.base_url}/createTask",
            json={
                "clientKey": self.api_key,
                "task": {"type": task_type, "websiteURL": url, "websiteKey": site_key},
            },
            timeout=HTTP_TIMEOUT,
        )
        data = resp.json()
        if data.get("errorId") != 0:
            raise CaptchaServiceError(
                f"Anti-Captcha submission failed: {data.get('errorDescription')}"
            )

        task_id = data.get("taskId")

        # Step 2: Get Result
        for _ in range(30):
            time.sleep(5)
            resp = self.session.post(
                f"{self.base_url}/getTaskResult",
                json={"clientKey": self.api_key, "taskId": task_id},
                timeout=HTTP_TIMEOUT,
            )
            data = resp.json()
            if data.get("status") == "ready":
                return data.get("solution", {}).get("gRecaptchaResponse")
            if data.get("errorId") != 0:
                raise CaptchaServiceError(f"Anti-Captcha failed: {data.get('errorDescription')}")
            continue

        raise CaptchaServiceError("Anti-Captcha timeout")


def get_solver(api_key: str | None, service: str = "2captcha") -> CaptchaSolver | None:
    if not api_key:
        return None
    return CaptchaSolver(api_key, service)
