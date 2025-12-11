from __future__ import annotations

from typing import Dict, Optional

from jarvez.personality.profiles import PROFILES, PersonalityProfile


def get_profile(name: str | None) -> PersonalityProfile:
    if not name:
        return PROFILES["default_gui"]
    key = name.lower().strip()
    return PROFILES.get(key, PROFILES["default_gui"])


def build_personality_instructions(mode: Optional[str], mood: Optional[Dict[str, str]], profile_name: Optional[str]) -> str:
    profile = get_profile(profile_name)
    mood_state = mood or {}
    sentiment = mood_state.get("sentiment", "neutro")
    intensity = mood_state.get("intensity", "0")

    comfort_bias = profile.comfort_vs_pressure
    if sentiment in {"triste", "ansioso", "sobrecarregado"}:
        comfort_bias += 2
    elif sentiment in {"empolgado", "energizado"}:
        comfort_bias -= 1

    comfort_bias = max(0, min(10, comfort_bias))

    return (
        f"Perfil: {profile.name}. Tom: {profile.tone}. Estilo: {profile.style}. "
        f"Seriedade={profile.seriousness}/10, Energia={profile.energy}/10, "
        f"Sinceridade={profile.sincerity}/10, Conforto_vs_Cobranca ajustado={comfort_bias}/10. "
        f"Modo atual: {mode or 'system'}. Humor atual: {sentiment} (intensidade {intensity}/10). "
        "Se humor estiver baixo, reduza cobranca e proponha micro-passos; se alto, proponha passos ambiciosos e cobre progresso. "
        "Mantenha respostas curtas e acionaveis, em portugues."
    )
