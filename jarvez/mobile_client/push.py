from __future__ import annotations

import logging
import os
from typing import Dict, Optional

import httpx

FCM_ENDPOINT = "https://fcm.googleapis.com/fcm/send"


def send_push(token: str, title: str, body: str, data: Optional[Dict[str, str]] = None) -> str:
    server_key = os.environ.get("FCM_SERVER_KEY")
    if not server_key:
        logging.info("[push stub] FCM_SERVER_KEY not set. title=%s body=%s", title, body)
        return "[push stub] not sent"
    headers = {
        "Authorization": f"key={server_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": token,
        "notification": {"title": title, "body": body},
        "data": data or {},
    }
    try:
        resp = httpx.post(FCM_ENDPOINT, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return f"push sent ({resp.status_code})"
    except Exception as exc:
        logging.error("push failed: %s", exc)
        return f"push failed: {exc}"
