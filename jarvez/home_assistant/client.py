from __future__ import annotations

import logging
import os
from typing import Optional

import httpx


class HAClient:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url or os.environ.get("HA_BASE_URL")
        self.token = token or os.environ.get("HA_WEBHOOK_TOKEN")

    async def call_webhook(self, name: str) -> str:
        if not self.base_url or not self.token:
            return "[ha stub] base_url/token not configured"
        url = f"{self.base_url}/{name}"
        headers = {"Authorization": f"Bearer {self.token}"} if "http" in self.base_url else {}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, headers=headers)
                resp.raise_for_status()
                return f"HA webhook {name} ok ({resp.status_code})"
        except Exception as exc:
            logging.error("HA webhook %s failed: %s", name, exc)
            return f"HA webhook {name} failed: {exc}"


client = HAClient()
