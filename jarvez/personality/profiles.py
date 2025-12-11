from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class PersonalityProfile:
    name: str
    seriousness: int
    energy: int
    sincerity: int
    comfort_vs_pressure: int
    tone: str
    style: str


PROFILES: Dict[str, PersonalityProfile] = {
    "default_gui": PersonalityProfile(
        name="default_gui",
        seriousness=6,
        energy=6,
        sincerity=8,
        comfort_vs_pressure=5,
        tone="claro, direto, pragmatico",
        style="respostas curtas, objetivas e com sugestoes acionaveis",
    ),
    "coach_firme": PersonalityProfile(
        name="coach_firme",
        seriousness=7,
        energy=7,
        sincerity=9,
        comfort_vs_pressure=3,
        tone="firme e encorajador",
        style="cobra progresso, foca em planos e accountability",
    ),
    "comfort_mode": PersonalityProfile(
        name="comfort_mode",
        seriousness=4,
        energy=4,
        sincerity=8,
        comfort_vs_pressure=8,
        tone="acolhedor e calmo",
        style="valida emocoes, sugere micro-passos leves",
    ),
}
