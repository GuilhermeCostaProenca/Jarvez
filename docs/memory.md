# Jarvez Memory (v0.2)

## Sources
- `data/memory.json`: user profile (nome, idioma, fuso, estilo), projetos, objetivos, preferencias, e `dynamic_facts` capturados em runtime.
- Notas em `data/notes/*.txt`: usadas como resumos curtos no system prompt e pesquisaveis via `note search <term>`.

## Flow
1. CLI recebe input e envia ao Agent.
2. MemoryStore.detect_important() marca texto longo ou com gatilhos (remember/important/goal/projeto/decisao/mudanca/conquista) como fato dinamico.
3. Orchestrator tenta skill; se pergunta sobre "quem sou eu / projetos / objetivos", responde direto via MemoryStore.answer_from_memory().
4. Caso va ao LLM: Orchestrator monta system prompt com system_context() (perfil + projetos + objetivos + preferencias + memorias dinamicas + resumos de notas) e ainda injeta relevant_facts() + notas como mensagens de sistema auxiliares.
5. Resposta e devolvida; CLI em `--debug` imprime quando memorias/notas foram usadas.

## Extensibilidade
- `dynamic_facts` pode ser migrado para SQLite ou vetor DB mantendo a API (update_memory/relevant_facts/system_context).
- Note search hoje e textual; encaixa diretamente um backend de embeddings no futuro.
- Pode-se adicionar novos gatilhos de importancia ou um classificador leve sem mudar a interface do orchestrator.
