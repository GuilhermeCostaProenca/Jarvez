from __future__ import annotations

import datetime as dt
from typing import Dict, Optional


MOOD_KEYWORDS = {
    "ansioso": ["ansioso", "ansiedade", "preocupado", "tenso"],
    "triste": ["triste", "chateado", "deprimido"],
    "irritado": ["irritado", "bravo", "raiva", "irritacao"],
    "sobrecarregado": ["sobrecarregado", "muito trabalho", "exausto", "cansado demais", "stress", "estressado"],
    "empolgado": ["empolgado", "animado", "motivado", "energia"],
    "neutro": [],
}


def detect_mood(user_input: str, mode: Optional[str] = None) -> Dict[str, str]:
    text = user_input.lower()
    sentiment = "neutro"
    intensity = 4

    for label, words in MOOD_KEYWORDS.items():
        if any(w in text for w in words):
            sentiment = label
            intensity = 7
            break

    # heuristic: long messages with negative words
    if "erro" in text or "problema" in text or "falhou" in text:
        sentiment = "frustrado"
        intensity = 6
    if len(text) > 240 and sentiment == "neutro":
        intensity = 5

    return {
        "sentiment": sentiment,
        "intensity": str(intensity),
        "mode": mode or "system",
        "timestamp": dt.datetime.utcnow().isoformat() + "Z",
    }
