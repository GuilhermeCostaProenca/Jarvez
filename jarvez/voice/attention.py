from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class AttentionContext:
    silence_before: float = 0.0
    since_last_trigger: float = 999.0
    cooldown_seconds: float = 3.0


QUESTION_TERMS = {
    "what",
    "who",
    "where",
    "when",
    "how",
    "why",
    "que",
    "qual",
    "quais",
    "quem",
    "onde",
    "quando",
    "como",
    "porque",
    "por que",
}

DIRECTIVE_TERMS = {
    "listen",
    "escuta",
    "ouve",
    "responde",
    "fala",
    "ajuda",
    "ajude",
    "pode",
    "preciso",
    "me diz",
    "me fale",
    "me ajuda",
}

VOCATIVE_TERMS = {"jarvez", "jarvis", "amigo", "cara", "hey", "oi", "olha", "voce", "você", "vc"}


def compute_attention_score(text: str, meta: Dict, ctx: AttentionContext) -> Tuple[float, Dict]:
    """Heuristic attention scorer; prefers false negatives."""
    clean = text.strip()
    lower = clean.lower()
    words = re.findall(r"\w+", lower)
    word_count = len(words)
    score = 0.1  # start conservative
    reasons: Dict[str, float] = {}

    if word_count <= 3:
        delta = 0.35
    elif word_count <= 6:
        delta = 0.25
    elif word_count <= 12:
        delta = 0.12
    else:
        delta = -0.08
    score += delta
    reasons["length"] = delta

    if "?" in clean or any(term in lower for term in QUESTION_TERMS):
        score += 0.2
        reasons["question"] = 0.2

    if any(term in lower for term in DIRECTIVE_TERMS):
        score += 0.18
        reasons["directive"] = 0.18

    if any(term in lower for term in VOCATIVE_TERMS):
        score += 0.25
        reasons["vocative"] = 0.25

    silence = ctx.silence_before
    if silence >= 3.0:
        delta = 0.22
    elif silence >= 1.5:
        delta = 0.16
    elif silence >= 0.8:
        delta = 0.1
    else:
        delta = -0.18  # continuous talking -> penalize
    score += delta
    reasons["silence_before"] = delta

    utter_sec = meta.get("utterance_sec", 0.0)
    voiced_sec = meta.get("voiced_sec", 0.0)
    if utter_sec > 8.0:
        score -= 0.12
        reasons["long_utterance"] = -0.12
    if voiced_sec < 0.6:
        score -= 0.05
        reasons["very_short_voice"] = -0.05

    if ctx.since_last_trigger < ctx.cooldown_seconds:
        score -= 0.3
        reasons["cooldown"] = -0.3

    score = max(0.0, min(1.0, score))
    return score, reasons
