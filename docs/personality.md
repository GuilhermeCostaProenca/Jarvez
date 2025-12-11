# Personality (v0.6)

## Profiles
- Defined in `jarvez/personality/profiles.py` (default_gui, coach_firme, comfort_mode).
- Each profile sets seriousness, energy, sincerity, comfort_vs_pressure, tone, and style.
- Select via env: `JARVEZ_PERSONALITY_PROFILE` (default `default_gui`).

## Engine
- `jarvez/personality/engine.py` builds personality instructions combining profile + mode + mood.
- The orchestrator injects these instructions into the system prompt for every LLM call.

## Behavior
- If mood is low (triste/ansioso/sobrecarregado): increases comfort bias, reduces cobrança, suggests micro-passos.
- If mood is high (empolgado/energizado): reduces comfort bias slightly, nudges toward ambitious steps.
- Modes still influence tone (focus = objetivo; life_coach = acolhedor + coach).

## Extensibility
- Add profiles to `PROFILES`.
- Feed a custom personality profile name via env without code changes.
