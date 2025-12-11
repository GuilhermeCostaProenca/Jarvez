from __future__ import annotations

import httpx
from typing import Any, Dict, Optional


class MobileApiClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key}

    def chat(self, message: str, mode: Optional[str] = None, debug: bool = False) -> Dict[str, Any]:
        payload = {"message": message, "mode": mode, "debug": debug}
        resp = httpx.post(f"{self.base_url}/chat", json=payload, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def send_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        resp = httpx.post(f"{self.base_url}/events", json=event, headers=self.headers, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def send_push(self, push: Dict[str, Any]) -> Dict[str, Any]:
        resp = httpx.post(f"{self.base_url}/push/send", json=push, headers=self.headers, timeout=15)
        resp.raise_for_status()
        return resp.json()
