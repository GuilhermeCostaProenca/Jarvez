# Desktop Orb (v0.9)

## Requisitos
- PySide6, httpx, psutil (já em requirements.txt)
- Definir `JARVEZ_API_URL` e `JARVEZ_API_KEY` (cloud core)

## Rodar
- `python -m jarvez.desktop.app`
- Orb aparece no canto (sempre on top). Clique para abrir o chat panel.
- Envie mensagens; respostas vêm da API `/chat`.

## Futuro (voz)
- Espaço no chat/orb para adicionar botão de microfone futuramente.

## Inicializar com Windows
- Adicione um atalho do comando acima na pasta de inicialização do Windows (passo manual por enquanto).
