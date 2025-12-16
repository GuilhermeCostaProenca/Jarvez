# Architecture notes (v0.9)

## High-level
```
CLI/Voice/API/Orb -> Agent -> Orchestrator -> { Skills | RAG | Memory | Automation | Vision | Mood | Personality | LLM }
                                           \
                                            -> Modes (tone + priorities) + Presence
```

## Modules
- core/agent.py: owns history and orchestrator wiring.
- core/orchestrator.py: builds prompts with memory + notes + RAG + mode, routes skills, captures memory, handles planner/multi-step, and exposes plan creation + mode switching.
- core/llm_client.py: OpenAI wrapper with offline stub fallback.
- core/memory.py: JSON-backed MemoryStore with static + dynamic sections, mode state, importance detection, profile answers.
- rag/embedder.py | vector_store.py | retriever.py: embeddings (dense/sparse), JSON vector store, retrieval for notes/memory/plans.
- skills/registry.py: routes to skills.
- skills/notes.py: note CRUD, search, summaries for context.
- skills/system.py: open URL/app plus guarded shell execution.
- skills/planner.py: goal decomposition, storage, notes integration.
- modes/*: mode definitions (tone, instructions, priority skills).
- interface/cli.py: text loop, mode selection, TTS, debug logs.
- interface/voice_cli.py: voice loop stub.
- voice/*: STT/TTS stubs with OpenAI hooks and microphone loop.
- api/server.py: FastAPI app exposing chat/plan/automation/status/events/push with API key.
- automation/*: actions, workflows, engine for safe local actions; config in config.py.
- home_assistant/*: webhook client + actions for HA.
- vision/*: capture_screen/camera/file/ocr, multimodal client, pipelines for screen/webcam/docs.
- personality/*: profiles and engine for prompt instructions.
- mood/*: detector + store for mood traces.
- skills/journal.py: journaling skill with mood tagging and RAG indexing.
- interface/remote_cli.py: CLI that talks to remote API with API key.
- desktop/*: orb widget + chat panel + awareness bridge to cloud.
- awareness/*: local context detection (apps/idle) and loop.
- mobile_client/*: wrappers for API/events/push.
- presence/*: maps presence/location events to mode suggestions.

## Data flow
1. CLI/Voice/API receives input and sends to Agent.
2. Agent passes message + history to Orchestrator.
3. Orchestrator captures important memory, checks mode switches, attempts skills (notes/system/planner), answers directly from memory when relevant.
4. If still unresolved: Orchestrator queries RAG (notes + static/dynamic memory + plans + vision-ingested docs), assembles messages with memory + notes + RAG, adds mode/system prompt, then calls LLM client.
5. Agent appends turns to history and returns the response; debug shows memory/note/RAG/vision/mood/personality usage.
6. External events (/events) can update memory and telemetry; HA actions can be triggered via automation run; presence suggests modes.
7. Desktop awareness loop can proactively call /chat with context and render in orb UI.

## Memory strategy
- Seed memory agora vive em SQLite (`jarvez.db:memories/settings`) com perfil, projetos, objetivos, preferencias, state.last_mode.
- detect_important() adiciona texto longo/keyword como dynamic facts; armazenado em SQLite e indexado no RAG.
- answer_from_memory() retorna perfil/projetos/objetivos direto quando perguntado.
- system_context() compoe perfil + objetivos + preferencias + memorias dinamicas + resumos de notas em cada chamada de LLM.
- relevant_facts() traz estaticos+dynamics recentes (ultimo N) para os prompts.

## RAG strategy
- Indexes: notes (full text), static facts, dynamic facts, and plans.
- Embeddings: OpenAI if available; sparse token fallback otherwise.
- Similarity: cosine for dense; jaccard for sparse.
- Retrieval: top_k chunks injected as system context before LLM.

## Mode strategy
- Modes define tone, system instructions, and priority skills.
- Mode can be changed by user command (`modo foco`, `mode study`) or via API payload, persisted in memory.state.last_mode, and reflected in system prompt. Suggestions surface workflows on switch.

## Planner strategy
- Planner skill produz passos, salva em SQLite (`jarvez.db:plans`) e cria uma nota.
- Plans sao indexados no RAG; metadados importantes viram dynamic memory.
- Multi-step detection in the orchestrator routes to planner when a pipeline is implied.
- API `/plan` also creates plans via the same path.

## Automation strategy
- AutomationEngine holds actions/workflows; most actions require `JARVEZ_ALLOW_AUTOMATION=1`.
- Orchestrator suggests workflows on mode switch; API `/automation/run` executes actions/workflows.
- Configurable paths/URLs live in `config.py`.

## Vision strategy
- Config-gated (`JARVEZ_VISION_ENABLED`, screen/camera toggles).
- Pipelines handle screen summary/errors, camera snapshot, PDF ingestion and study-plan creation.
- Outputs go to notes, memory (dynamic facts), and RAG for downstream QA and study flows.

## Personality strategy
- Profiles define tone/energy/comfort sliders; chosen via env.
- Personality + mood + mode merged into system prompt instructions.

## Mood strategy
- Heuristic detector per input; traces saved to SQLite (`jarvez.db:mood_trace`).
- Mood summary injected into prompts; exposed in API/CLI debug.
- Future: use traces for planner weighting and journaling insights.

## Journal strategy
- Journal entries saved in SQLite (`jarvez.db:journal_entries`), mood-tagged, indexed into RAG.
- Summaries (stub) for week/month; life_coach mode can encourage journaling when moods are strong.

## Extensibility targets
- Voice: swap stubs for Vosk/whisper.cpp capture and streaming TTS.
- RAG: replace JSON store with FAISS/SQLite/Chroma while keeping the retriever API.
- Automation: add agent tools for device control; expose orchestrator via FastAPI (now available), plug Home Assistant/external connectors.
