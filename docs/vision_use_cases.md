# Vision Use Cases (v0.5)

## Debug de tela
- Command: `vision screen errors` or “olha minha tela e vê se tem erro”.
- Flow: captura tela -> analisa -> grava memória -> sugere ações.

## Resumo de slides/código
- Command: `vision screen summarize`.
- Flow: captura tela -> resumo -> cria nota -> indexa RAG.

## Estudo com PDF
- Command: `vision pdf path/to/file.pdf`.
- Flow: lê/ocr -> cria nota com resumo bruto -> indexa RAG.

## Plano de estudo a partir de PDF
- Command: “cria um plano de estudo baseado nesse PDF X” (com caminho).
- Flow: captura texto -> nota -> cria plano -> memória/RAG.

## Análise de ambiente (webcam)
- Command: `vision camera` or “olha pela webcam”.
- Flow: captura frame -> resumo -> memória/RAG.

## Postura/organização (stub)
- Command: “analisa minha postura/mesa”.
- Flow: captura frame (quando habilitado) -> resumo -> ações futuras (planner/automation).
