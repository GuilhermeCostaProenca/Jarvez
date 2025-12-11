from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


class LLMClient:
    """Simple wrapper around OpenAI with an offline fallback."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None, organization: Optional[str] = None):
        self.model = model or os.environ.get("JARVEZ_MODEL", "gpt-4o-mini")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.organization = organization or os.environ.get("OPENAI_ORG")
        self.client = None

        if OpenAI and self.api_key:
            self.client = OpenAI(api_key=self.api_key, organization=self.organization)
        else:
            logging.warning("OpenAI client not configured; falling back to offline stub")

    def generate(self, system_prompt: str, messages: List[Dict[str, str]], max_tokens: int = 256) -> str:
        if self.client:
            try:
                chat_messages = [{"role": "system", "content": system_prompt}, *messages]
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=chat_messages,
                    max_tokens=max_tokens,
                )
                content = response.choices[0].message.content
                return content or ""
            except Exception as exc:
                logging.error("LLM call failed: %s", exc)

        return self.offline_response(messages)

    def offline_response(self, messages: List[Dict[str, str]]) -> str:
        last_user = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
        hint = last_user[:160]
        return f"[offline stub] Echo: {hint}"
