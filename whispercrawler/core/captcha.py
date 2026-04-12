import time
from typing import Any, Dict, Optional
import requests

from whispercrawler.core.utils import log

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
        """Solve Google ReCaptcha V2."""
        if self.service == "2captcha":
            return self._solve_2captcha(site_key, url, method="userrecaptcha")
        else:
            return self._solve_anticaptcha(site_key, url, task_type="NoCaptchaTaskProxyless")

    def _solve_2captcha(self, site_key: str, url: str, method: str) -> str:
        # Step 1: Submit request
        resp = self.session.post(f"{self.base_url}/in.php", data={
            "key": self.api_key,
            "method": method,
            "googlekey": site_key,
            "pageurl": url,
            "json": 1
        })
        
        data = resp.json()
        if data.get("status") != 1:
            raise CaptchaServiceError(f"2Captcha submission failed: {data.get('request')}")
        
        request_id = data.get("request")
        
        # Step 2: Poll for result
        for _ in range(30): # Poll for up to 150 seconds
            time.sleep(5)
            resp = self.session.get(f"{self.base_url}/res.php", params={
                "key": self.api_key,
                "action": "get",
                "id": request_id,
                "json": 1
            })
            data = resp.json()
            if data.get("status") == 1:
                return data.get("request")
            if data.get("request") == "CAPCHA_NOT_READY":
                continue
            raise CaptchaServiceError(f"2Captcha failed: {data.get('request')}")
            
        raise CaptchaServiceError("2Captcha timeout")

    def _solve_anticaptcha(self, site_key: str, url: str, task_type: str) -> str:
        # Step 1: Create Task
        resp = self.session.post(f"{self.base_url}/createTask", json={
            "clientKey": self.api_key,
            "task": {
                "type": task_type,
                "websiteURL": url,
                "websiteKey": site_key
            }
        })
        data = resp.json()
        if data.get("errorId") != 0:
            raise CaptchaServiceError(f"Anti-Captcha submission failed: {data.get('errorDescription')}")
            
        task_id = data.get("taskId")
        
        # Step 2: Get Result
        for _ in range(30):
            time.sleep(5)
            resp = self.session.post(f"{self.base_url}/getTaskResult", json={
                "clientKey": self.api_key,
                "taskId": task_id
            })
            data = resp.json()
            if data.get("status") == "ready":
                return data.get("solution", {}).get("gRecaptchaResponse")
            if data.get("errorId") != 0:
                raise CaptchaServiceError(f"Anti-Captcha failed: {data.get('errorDescription')}")
            continue
            
        raise CaptchaServiceError("Anti-Captcha timeout")

def get_solver(api_key: Optional[str], service: str = "2captcha") -> Optional[CaptchaSolver]:
    if not api_key:
        return None
    return CaptchaSolver(api_key, service)
