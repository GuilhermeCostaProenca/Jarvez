from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from jarvez.modes import get_mode, list_modes
from jarvez.rag.embedder import Embedder
from jarvez.rag.retriever import Retriever
from jarvez.rag.vector_store import VectorStore
from jarvez.skills import journal, notes, planner
from jarvez.skills.registry import SkillRegistry, SkillResult
from jarvez.personality.engine import build_personality_instructions
from jarvez.mood import detector as mood_detector
from jarvez.mood.store import MoodStore
from jarvez.vision import pipelines as vision_pipelines
from jarvez.config import load_config
from jarvez.telemetry.logger import log_event
from jarvez.storage.db import JarvezDatabase

from .llm_client import LLMClient
from .memory import MemoryStore


@dataclass
class AgentResponse:
    text: str
    skill_used: Optional[str] = None
    memory_updates: List[str] = field(default_factory=list)
    memory_used: bool = False
    memory_context: List[str] = field(default_factory=list)
    note_context: List[str] = field(default_factory=list)
    rag_context: List[str] = field(default_factory=list)
    mode: str = "system"
    plan: Optional[Dict] = None
    vision_used: bool = False
    mood: Optional[Dict] = None
    personality_profile: Optional[str] = None
    journal_suggested: bool = False
    event_ids: List[str] = field(default_factory=list)


class Orchestrator:
    """Coordinates memory, skills, modes, planner, RAG, and LLM orchestration."""

    def __init__(
        self,
        llm_client: LLMClient,
        memory_store: MemoryStore,
        skill_registry: SkillRegistry,
        default_mode: Optional[str] = None,
    ):
        self.config = load_config()
        self.llm_client = llm_client
        self.memory_store = memory_store
        self.skill_registry = skill_registry
        self.db = JarvezDatabase()
        self.mood_store = MoodStore(self.db)

        self.current_mode = get_mode(default_mode or self.memory_store.get_last_mode())
        self.memory_store.set_last_mode(self.current_mode.name)

        self.retriever = Retriever(Embedder(), VectorStore(None, db=self.db))
        self._bootstrap_rag_index()

    def _bootstrap_rag_index(self) -> None:
        docs: List[Dict[str, str]] = []
        for fact in self.memory_store.get_memory().get("facts", []):
            if fact.get("text"):
                docs.append(
                    {"doc_id": fact.get("id", f"fact-{len(docs)}"), "text": fact["text"], "metadata": {"type": "fact"}}
                )
        for fact in self.memory_store.get_memory().get("dynamic_facts", []):
            if fact.get("text"):
                docs.append(
                    {
                        "doc_id": fact.get("id", f"dyn-{len(docs)}"),
                        "text": fact["text"],
                        "metadata": {"type": "dynamic_fact", "tags": fact.get("tags", [])},
                    }
                )
        for note in notes.DB.list_notes(limit=50):
            text = (note.get("content") or "").strip()
            if text:
                docs.append(
                    {
                        "doc_id": f"note-{note.get('id')}",
                        "text": text,
                        "metadata": {"type": "note", "title": note.get("title")},
                    }
                )
        if docs:
            self.retriever.index_bulk(docs)
            logging.debug("Bootstrapped RAG index with %s documents", len(docs))

    def build_system_prompt(
        self, memory_context: str, mode_instructions: str, personality_instructions: str, mood_summary: str
    ) -> str:
        return (
            "You are Jarvez, um assistente de estilo sistema operacional que conhece profundamente o Gui. "
            "Responda em portugues, curto e acionavel. Use ferramentas quando ajudar. "
            "Sempre considere a memoria do usuario antes de responder. "
            f"Modo atual: {self.current_mode.name}. Skills prioritarias: {', '.join(self.current_mode.priority_skills)}. "
            f"Instrucoes do modo: {mode_instructions}. "
            f"Personalidade: {personality_instructions}. "
            f"Humor recente: {mood_summary}. "
            f"Contexto do usuario e memoria: {memory_context}"
        )

    def compose_messages(
        self,
        user_input: str,
        history: List[Dict[str, str]],
        memories: List[str],
        note_context: List[str],
        rag_chunks: List[str],
    ) -> List[Dict[str, str]]:
        trimmed_history = history[-6:]
        messages: List[Dict[str, str]] = []

        if memories:
            memory_block = "Memoria relevante:\n" + "\n".join(f"- {m}" for m in memories)
            messages.append({"role": "system", "content": memory_block})
        if note_context:
            note_block = "Notas relevantes:\n" + "\n".join(f"- {n}" for n in note_context)
            messages.append({"role": "system", "content": note_block})
        if rag_chunks:
            rag_block = "Contexto RAG:\n" + "\n".join(f"- {c}" for c in rag_chunks)
            messages.append({"role": "system", "content": rag_block})

        messages.extend(trimmed_history)
        messages.append({"role": "user", "content": user_input})
        return messages

    def set_mode(self, mode_name: Optional[str]) -> str:
        self.current_mode = get_mode(mode_name) if mode_name else get_mode(self.memory_store.get_last_mode())
        self.memory_store.set_last_mode(self.current_mode.name)
        return self.current_mode.name

    def _handle_vision(self, user_input: str) -> Optional[AgentResponse]:
        lower = user_input.lower()
        if "vision screen" in lower or ("tela" in lower and ("olha" in lower or "ve" in lower or "veja" in lower)):
            if "erro" in lower or "error" in lower:
                result = vision_pipelines.analyze_screen_for_errors(self.memory_store, self.retriever, mode=self.current_mode.name)
                evt = log_event("vision.screen.errors", {"mode": self.current_mode.name})
                return AgentResponse(
                    text=result["message"],
                    memory_updates=result.get("memory_updates", []),
                    skill_used="vision.screen.errors",
                    mode=self.current_mode.name,
                    vision_used=True,
                    event_ids=[evt],
                )
            result = vision_pipelines.summarize_screen_content(self.memory_store, self.retriever, mode=self.current_mode.name)
            evt = log_event("vision.screen.summary", {"mode": self.current_mode.name})
            return AgentResponse(
                text=result["message"],
                memory_updates=result.get("memory_updates", []),
                skill_used="vision.screen.summary",
                mode=self.current_mode.name,
                vision_used=True,
                event_ids=[evt],
            )

        if "vision camera" in lower or "webcam" in lower or "camera" in lower:
            result = vision_pipelines.analyze_camera_snapshot(self.memory_store, self.retriever, mode=self.current_mode.name)
            evt = log_event("vision.camera", {"mode": self.current_mode.name})
            return AgentResponse(
                text=result["message"],
                memory_updates=result.get("memory_updates", []),
                skill_used="vision.camera",
                mode=self.current_mode.name,
                vision_used=True,
                event_ids=[evt],
            )

        if "vision pdf" in lower or "vision doc" in lower or (".pdf" in lower and ("vision" in lower or "analisa" in lower or "le" in lower)):
            parts = user_input.split()
            path = None
            for token in parts:
                if token.lower().endswith(".pdf"):
                    path = token
                    break
            if not path:
                return AgentResponse(
                    text="Forneca o caminho do PDF (ex: vision pdf caminho/arquivo.pdf).",
                    mode=self.current_mode.name,
                )
            result = vision_pipelines.summarize_pdf_to_notes(path, self.memory_store, self.retriever)
            evt = log_event("vision.pdf", {"mode": self.current_mode.name, "path": path})
            return AgentResponse(
                text=result["message"],
                memory_updates=result.get("memory_updates", []),
                skill_used="vision.pdf",
                mode=self.current_mode.name,
                vision_used=True,
                event_ids=[evt],
            )

        if "plano" in lower and ".pdf" in lower:
            parts = user_input.split()
            path = None
            for token in parts:
                if token.lower().endswith(".pdf"):
                    path = token
                    break
            if path:
                result = vision_pipelines.create_study_plan_from_pdf(path, self.memory_store, self.retriever)
                evt = log_event("vision.pdf.plan", {"mode": self.current_mode.name, "path": path})
                return AgentResponse(
                    text=result["message"],
                    memory_updates=result.get("memory_updates", []),
                    skill_used="vision.pdf.plan",
                    plan=result.get("plan"),
                    mode=self.current_mode.name,
                    vision_used=True,
                    event_ids=[evt],
                )
        return None

    def handle_home_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process external home events (e.g., Home Assistant)."""
        evt_id = log_event("home.event", {"mode": self.current_mode.name, **event})
        handled = False
        event_type = event.get("type", "")
        name = event.get("event", "")
        metadata = event.get("metadata", {})

        if event_type == "presence" and "arrived" in name:
            entry = {
                "id": f"home-{evt_id}",
                "content": f"Evento de chegada detectado: {name}",
                "source": "home_assistant",
                "type": "presence",
                "tags": ["home", "presence"],
            }
            self.memory_store.update_memory(entry, section="dynamic_facts")
            try:
                self.retriever.index_document(doc_id=entry["id"], text=entry["content"], metadata={"type": "home_event"})
            except Exception:
                logging.debug("Failed to index home event")
            handled = True
        return {"event_id": evt_id, "handled": handled, "mode": self.current_mode.name, "metadata": metadata}

    def _change_mode(self, user_input: str) -> Optional[AgentResponse]:
        lower = user_input.lower()
        if lower.startswith(("modo ", "mode ")):
            parts = lower.split()
            if len(parts) >= 2:
                mode_name = parts[1].replace("_", " ")
                self.set_mode(mode_name)
                suggestions = {
                    "study": "workflow sugerido: study_networks",
                    "focus": "workflow sugerido: focus_session",
                    "planner": "use /plan ou comando 'plan ...'",
                }
                suggestion = suggestions.get(self.current_mode.name, "")
                return AgentResponse(
                    text=f"Modo alterado para {self.current_mode.name} ({self.current_mode.description}). {suggestion}".strip(),
                    mode=self.current_mode.name,
                )
        if lower in {"listar modos", "list modes"}:
            modes = list_modes()
            listing = ", ".join(modes.keys())
            return AgentResponse(text=f"Modos disponiveis: {listing}", mode=self.current_mode.name)
        return None

    def create_plan(self, goal_text: str) -> AgentResponse:
        result = planner.plan_goal(goal_text)
        entry = {
            "id": result["plan"]["id"],
            "content": f"Plano criado: {result['plan']['goal']} -> {len(result['plan']['steps'])} passos",
            "source": "planner",
            "type": "plan",
            "tags": ["plan"],
        }
        saved = self.memory_store.update_memory(entry, section="dynamic_facts")
        try:
            self.retriever.index_document(
                doc_id=entry["id"], text=result["plan"]["goal"], metadata={"type": "plan", "steps": entry["content"]}
            )
        except Exception:
            logging.debug("Failed to index plan into RAG")
        evt = log_event("planner.plan", {"mode": self.current_mode.name, "goal": result["plan"]["goal"]})
        return AgentResponse(
            text=result["message"],
            skill_used="planner.plan",
            memory_updates=[saved.get("content", "")],
            plan=result["plan"],
            mode=self.current_mode.name,
            event_ids=[evt],
        )

    def _maybe_plan(self, user_input: str) -> Optional[AgentResponse]:
        lower = user_input.lower()
        triggers = ("plano", "plan", "passo a passo", "pipeline", "ate ", "ate")
        if any(t in lower for t in triggers):
            return self.create_plan(user_input)
        return None

    def handle(self, user_input: str, history: List[Dict[str, str]]) -> AgentResponse:
        event_ids: List[str] = []
        event_ids.append(
            log_event(
                "input",
                {
                    "mode": self.current_mode.name,
                    "text": user_input[:200],
                },
            )
        )

        new_memory_entries = self.memory_store.detect_important(user_input)
        memory_updates: List[str] = []
        for entry in new_memory_entries:
            section = entry.pop("_section", "dynamic_facts")
            saved = self.memory_store.update_memory(entry, section=section)
            memory_updates.append(saved.get("content", ""))
            try:
                self.retriever.index_document(
                    doc_id=saved.get("id", f"mem-{len(memory_updates)}"),
                    text=saved.get("content", ""),
                    metadata={"type": "memory", "tags": saved.get("tags", [])},
                )
            except Exception:
                logging.debug("Failed to index memory for RAG")

        mode_response = self._change_mode(user_input)
        if mode_response:
            mode_response.memory_updates = memory_updates
            mode_response.event_ids.extend(event_ids)
            return mode_response

        vision_response = self._handle_vision(user_input)
        if vision_response:
            vision_response.memory_updates.extend(memory_updates)
            vision_response.event_ids.extend(event_ids)
            return vision_response

        skill_result: SkillResult = self.skill_registry.dispatch(user_input)
        if skill_result.handled:
            if skill_result.name == "journal.create" and skill_result.metadata:
                content = skill_result.metadata.get("content", "")
                message = journal.create_entry(content, retriever=self.retriever, mood_store=self.mood_store)
                evt = log_event("journal.create", {"mode": self.current_mode.name})
                return AgentResponse(
                    text=message,
                    skill_used="journal.create",
                    memory_updates=memory_updates,
                    mode=self.current_mode.name,
                    event_ids=event_ids + [evt],
                )
            if skill_result.name == "planner.plan" and skill_result.metadata:
                try:
                    self.retriever.index_document(
                        doc_id=skill_result.metadata.get("id", skill_result.name),
                        text=skill_result.metadata.get("goal", ""),
                        metadata={"type": "plan", "steps": skill_result.metadata.get("steps", [])},
                    )
                except Exception:
                    logging.debug("Failed to index plan from skill")
                evt = log_event("planner.plan", {"mode": self.current_mode.name, "goal": skill_result.metadata.get("goal", "")})
            else:
                evt = log_event("skill", {"mode": self.current_mode.name, "name": skill_result.name})
            event_ids.append(evt)
            return AgentResponse(
                text=skill_result.message,
                skill_used=skill_result.name,
                memory_updates=memory_updates,
                mode=self.current_mode.name,
                event_ids=event_ids,
            )

        direct_memory = self.memory_store.answer_from_memory(user_input)
        if direct_memory:
            evt = log_event("memory.answer", {"mode": self.current_mode.name})
            event_ids.append(evt)
            return AgentResponse(
                text=direct_memory,
                memory_used=True,
                memory_updates=memory_updates,
                memory_context=[direct_memory],
                mode=self.current_mode.name,
                event_ids=event_ids,
            )

        plan_response = self._maybe_plan(user_input)
        if plan_response:
            plan_response.memory_updates.extend(memory_updates)
            plan_response.mode = self.current_mode.name
            plan_response.event_ids.extend(event_ids)
            return plan_response

        mood_state = None
        journal_suggested = False
        if self.config.mood_enabled:
            mood_state = mood_detector.detect_mood(user_input, mode=self.current_mode.name)
            self.mood_store.append(mood_state)
            event_ids.append(log_event("mood.detected", {"mode": self.current_mode.name, **mood_state}))
            try:
                intensity_val = int(mood_state.get("intensity", "0"))
                if intensity_val >= 7 and mood_state.get("sentiment") in {"triste", "ansioso", "sobrecarregado", "frustrado"}:
                    journal_suggested = True
                    event_ids.append(log_event("journal.suggested", {"mode": self.current_mode.name, **mood_state}))
            except Exception:
                pass

        note_summaries = notes.get_note_summaries(limit=3, snippet_chars=200)
        rag_chunks_structs = self.retriever.retrieve(user_input, top_k=3)
        rag_chunks = [f"{c.metadata.get('type')}: {c.text[:200]}" for c in rag_chunks_structs]
        memories = self.memory_store.relevant_facts()
        memory_context = self.memory_store.system_context(note_summaries=note_summaries)
        mode_instructions = self.current_mode.system_instructions
        personality_instructions = build_personality_instructions(
            mode=self.current_mode.name, mood=mood_state, profile_name=self.config.personality_profile
        )
        mood_summary = (
            f"{mood_state.get('sentiment')} ({mood_state.get('intensity')}/10)" if mood_state else "desconhecido"
        )
        messages = self.compose_messages(user_input, history, memories, note_summaries, rag_chunks)

        response_text = self.llm_client.generate(
            self.build_system_prompt(memory_context, mode_instructions, personality_instructions, mood_summary),
            messages,
        )

        return AgentResponse(
            text=response_text,
            memory_updates=memory_updates,
            memory_used=bool(memories or note_summaries),
            memory_context=memories,
            note_context=note_summaries,
            rag_context=rag_chunks,
            mode=self.current_mode.name,
            vision_used=False,
            mood=mood_state,
            personality_profile=self.config.personality_profile,
            journal_suggested=journal_suggested,
            event_ids=event_ids,
        )
