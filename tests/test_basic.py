from pathlib import Path

from jarvez.core.memory import MemoryStore
from jarvez.mood import detector as mood_detector
from jarvez.mood.store import MoodStore
from jarvez.rag.embedder import Embedder
from jarvez.rag.retriever import Retriever
from jarvez.rag.vector_store import VectorStore
from jarvez.skills import planner
from jarvez.skills import journal as journal_skill


def test_memory_basic(tmp_path: Path):
    mem_path = tmp_path / "memory.json"
    store = MemoryStore(path=mem_path)
    entry = {"id": "t1", "content": "Teste de memoria", "source": "test"}
    store.update_memory(entry, section="dynamic_facts")
    assert "Teste de memoria" in store.relevant_facts(limit=1)[0]


def test_rag_index_and_retrieve(tmp_path: Path):
    store = VectorStore(tmp_path / "rag.json")
    retriever = Retriever(Embedder(), store)
    retriever.index_document("doc1", "guilherme gosta de IA aplicada", {"type": "fact"})
    results = retriever.retrieve("IA aplicada", top_k=1)
    assert results
    assert "guilherme" in results[0].text.lower()


def test_planner_create(tmp_path: Path, monkeypatch):
    temp_planner = tmp_path / "planner.json"
    monkeypatch.setattr(planner, "PLANNER_PATH", temp_planner)
    res = planner.plan_goal("Testar planner")
    assert res["plan"]["goal"]
    assert temp_planner.exists()


def test_mood_detection_and_store(tmp_path: Path):
    mood = mood_detector.detect_mood("estou ansioso com o trabalho", mode="focus")
    assert mood["sentiment"] in {"ansioso", "frustrado", "sobrecarregado"}
    store = MoodStore(path=tmp_path / "mood.json")
    store.append(mood)
    assert store.recent()[0]["sentiment"] == mood["sentiment"]


def test_journal_create_and_summary(tmp_path: Path, monkeypatch):
    temp_dir = tmp_path / "journal"
    monkeypatch.setattr(journal_skill, "JOURNAL_DIR", temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    msg = journal_skill.create_entry("Hoje foi um dia produtivo", retriever=None, mood_store=None)
    assert "Journal registrado" in msg
    summary = journal_skill.summarize(period="week")
    assert "entradas" in summary or "Nenhum journal" in summary
