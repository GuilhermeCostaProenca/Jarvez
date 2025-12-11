from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jarvez.config import load_config
from jarvez.rag.retriever import Retriever
from jarvez.skills import notes, planner
from jarvez.vision.capture_camera import capture_frame
from jarvez.vision.capture_file import load_file
from jarvez.vision.capture_screen import capture_screen
from jarvez.vision.multimodal import analyze_image
from jarvez.core.memory import MemoryStore


def _now_id(prefix: str) -> str:
    return f"{prefix}-{int(datetime.utcnow().timestamp())}"


def _persist(memory_store: MemoryStore, retriever: Retriever, entries: List[Dict], rag_docs: List[Dict]) -> List[str]:
    updates: List[str] = []
    for entry in entries:
        section = entry.pop("_section", "dynamic_facts")
        saved = memory_store.update_memory(entry, section=section)
        updates.append(saved.get("content", ""))
    for doc in rag_docs:
        try:
            retriever.index_document(doc_id=doc["doc_id"], text=doc["text"], metadata=doc.get("metadata", {}))
        except Exception as exc:
            logging.debug("Failed to index vision doc: %s", exc)
    return updates


def summarize_screen_content(memory_store: MemoryStore, retriever: Retriever, mode: Optional[str] = None) -> Dict:
    cfg = load_config()
    img_bytes, _ = capture_screen(save=False)
    if not img_bytes:
        return {"message": "Visao de tela indisponivel ou desabilitada.", "memory_updates": []}

    summary = analyze_image(img_bytes, "Resuma o conteudo da tela. Destaque erros, status e passos proximos.", mode=mode)
    note_msg = notes.create_note("Visao tela", summary)
    entry = {
        "id": _now_id("screen"),
        "content": f"Resumo de tela: {summary}",
        "source": "vision-screen",
        "type": "observation",
        "tags": ["vision", "screen"],
    }
    rag_doc = {"doc_id": entry["id"], "text": summary, "metadata": {"type": "vision_screen"}}
    memory_updates = _persist(memory_store, retriever, [entry], [rag_doc])
    return {"message": f"Resumo da tela: {summary}\n{note_msg}", "memory_updates": memory_updates, "note": note_msg}


def analyze_screen_for_errors(memory_store: MemoryStore, retriever: Retriever, mode: Optional[str] = None) -> Dict:
    img_bytes, _ = capture_screen(save=False)
    if not img_bytes:
        return {"message": "Visao de tela indisponivel ou desabilitada.", "memory_updates": []}

    summary = analyze_image(img_bytes, "Identifique erros/avisos na tela e sugira 3 acoes curtas.", mode=mode)
    entry = {
        "id": _now_id("screen"),
        "content": f"Erros na tela: {summary}",
        "source": "vision-screen",
        "type": "observation",
        "tags": ["vision", "screen", "errors"],
    }
    rag_doc = {"doc_id": entry["id"], "text": summary, "metadata": {"type": "vision_screen_error"}}
    memory_updates = _persist(memory_store, retriever, [entry], [rag_doc])
    return {"message": summary, "memory_updates": memory_updates}


def analyze_camera_snapshot(memory_store: MemoryStore, retriever: Retriever, mode: Optional[str] = None) -> Dict:
    img_bytes, _ = capture_frame()
    if not img_bytes:
        return {"message": "Visao da camera indisponivel ou desabilitada.", "memory_updates": []}

    summary = analyze_image(img_bytes, "Descreva o ambiente e itens relevantes. Seja conciso.", mode=mode)
    entry = {
        "id": _now_id("camera"),
        "content": f"Snapshot camera: {summary}",
        "source": "vision-camera",
        "type": "observation",
        "tags": ["vision", "camera"],
    }
    rag_doc = {"doc_id": entry["id"], "text": summary, "metadata": {"type": "vision_camera"}}
    memory_updates = _persist(memory_store, retriever, [entry], [rag_doc])
    return {"message": summary, "memory_updates": memory_updates}


def summarize_pdf_to_notes(path: str | Path, memory_store: MemoryStore, retriever: Retriever) -> Dict:
    text = load_file(path)
    if not text:
        return {"message": "Arquivo nao lido. Caminho invalido ou OCR indisponivel.", "memory_updates": []}

    snippet = text[:1200]
    note_title = f"Material - {Path(path).stem}"
    note_msg = notes.create_note(note_title, snippet)
    entry = {
        "id": _now_id("doc"),
        "content": f"Resumo bruto do arquivo {Path(path).name}: {snippet[:200]}...",
        "source": "vision-doc",
        "type": "document",
        "tags": ["vision", "doc"],
    }
    rag_doc = {"doc_id": entry["id"], "text": snippet, "metadata": {"type": "vision_doc", "path": str(path)}}
    memory_updates = _persist(memory_store, retriever, [entry], [rag_doc])
    return {"message": f"Conteudo capturado e salvo em nota: {note_msg}", "memory_updates": memory_updates, "note": note_msg}


def create_study_plan_from_pdf(path: str | Path, memory_store: MemoryStore, retriever: Retriever) -> Dict:
    base = summarize_pdf_to_notes(path, memory_store, retriever)
    goal = f"Estudar material {Path(path).name}"
    plan_result = planner.plan_goal(goal)
    entry = {
        "id": plan_result["plan"]["id"],
        "content": f"Plano de estudo criado para {Path(path).name}",
        "source": "vision-doc",
        "type": "plan",
        "tags": ["vision", "doc", "plan"],
    }
    rag_doc = {"doc_id": entry["id"], "text": plan_result["plan"]["goal"], "metadata": {"type": "plan", "source": "vision"}}
    memory_updates = _persist(memory_store, retriever, [entry], [rag_doc])
    return {
        "message": f"{base.get('message', '')}\nPlano criado: {plan_result['message']}",
        "memory_updates": base.get("memory_updates", []) + memory_updates,
        "plan": plan_result["plan"],
    }
