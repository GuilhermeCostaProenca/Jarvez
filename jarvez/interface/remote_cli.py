from __future__ import annotations

import argparse
import json
import sys

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Jarvez remote CLI (v0.8)")
    parser.add_argument("--url", required=True, help="Jarvez API base URL, e.g., https://jarvez-core.fly.dev")
    parser.add_argument("--api-key", required=True, help="API key for authentication")
    parser.add_argument("--mode", type=str, default=None, help="force mode for requests")
    parser.add_argument("--debug", action="store_true", help="show debug fields (mood, personality, vision, events)")
    args = parser.parse_args()

    base = args.url.rstrip("/")
    headers = {"X-API-Key": args.api_key}

    print("Jarvez remote CLI. Type 'exit' to quit.")
    while True:
        try:
            user_input = input("you> ").strip()
        except EOFError:
            print()
            break
        if user_input.lower() in {"exit", "quit"}:
            break

        payload = {"message": user_input, "mode": args.mode, "debug": args.debug}
        try:
            resp = httpx.post(f"{base}/chat", json=payload, headers=headers, timeout=30)
            if resp.status_code != 200:
                print(f"error ({resp.status_code}): {resp.text}")
                continue
            data = resp.json()
        except Exception as exc:
            print(f"request failed: {exc}")
            continue

        print(f"jarvez ({data.get('mode')})> {data.get('reply')}")
        if args.debug:
            for key in ("skill_used", "vision_used", "mood", "personality_profile", "journal_suggested", "note_context", "rag_context", "memory_updates"):
                val = data.get(key)
                if val:
                    print(f"[debug] {key}: {val}")

    print("Bye.")


if __name__ == "__main__":
    main()
