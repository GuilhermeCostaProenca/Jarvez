# Awareness (v0.9)

## Componentes
- `awareness/detectors.py`: captura app/título ativo (psutil/pygetwindow se disponível), mapeia VSCode/browsers/YouTube e idle.
- `awareness/context.py`: estado atual (context_type, active_app, timestamps), detecção de idle.
- `awareness/loop.py`: loop periódico; emite context changes e idle via callback; registra telemetria.
- `desktop/awareness_bridge.py`: aplica regras e envia prompts proativos rate-limited para o Jarvez Cloud.

## Contextos detectados (simples)
- `coding_vs_code` (processo Code.exe)
- `study_college` (titulo com FIAP)
- `watching_video` (YouTube)
- `browsing`
- `idle`

## Anti-spam
- Bridge tem cooldown por contexto (padrão 5 min) antes de enviar nova proativa.

## Extensões
- Adicionar mais mapeamentos de apps/URLs em `detectors.py`.
- Ajustar mensagens proativas em `awareness_bridge.py`.
- Integrar com `/events` se quiser que o cloud também tenha ciência da presença.
