from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from jarvez.automation.engine import ENGINE
from jarvez.core.agent import Agent
from jarvez.skills import planner
from jarvez.config import load_config
from jarvez.telemetry.logger import log_event
from jarvez.home_assistant import actions as ha_actions
from jarvez.presence.context import handle_presence_event
from jarvez.mobile_client import push as mobile_push
from jarvez.storage.db import JarvezDatabase

app = FastAPI(title="Jarvez API", version="0.9.0")

agent = Agent()
CONFIG = load_config()
DB = JarvezDatabase()


class ChatRequest(BaseModel):
    message: str
    mode: Optional[str] = None
    debug: bool = False


class ChatResponse(BaseModel):
    reply: str
    mode: str
    skill_used: Optional[str] = None
    memory_used: bool = False
    vision_used: bool = False
    memory_updates: List[str] = []
    note_context: List[str] = []
    rag_context: List[str] = []
    plan: Optional[Dict[str, Any]] = None
    debug_data: Optional[Dict[str, Any]] = None
    mood: Optional[Dict[str, Any]] = None
    personality_profile: Optional[str] = None
    journal_suggested: bool = False


class PlanRequest(BaseModel):
    goal: str = Field(..., description="Goal or objective to plan")


class PlanResponse(BaseModel):
    message: str
    plan: Dict[str, Any]
    memory_updates: List[str] = []


class AutomationRequest(BaseModel):
    action_id: Optional[str] = None
    workflow_id: Optional[str] = None


class AutomationResponse(BaseModel):
    results: List[str]


class StatusResponse(BaseModel):
    mode: str
    last_input: Optional[str]
    last_output: Optional[str]
    plans_count: int
    automation_safe_mode: bool
    vision_enabled: bool
    mood_enabled: bool
    personality_profile: Optional[str]
    journal_count: int
    mood_entries: int
    env: str


def require_api_key(x_api_key: str = Header(default=None)) -> None:
    if not CONFIG.api_key:
        return
    valid_keys = [k.strip() for k in CONFIG.api_key.split(",") if k.strip()]
    if not x_api_key or x_api_key not in valid_keys:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")


class EventPayload(BaseModel):
    source: str
    type: str
    event: str
    metadata: Dict[str, Any] = {}


class PushPayload(BaseModel):
    token: str
    title: str
    body: str
    data: Dict[str, str] = {}


class ForgetRequest(BaseModel):
    query: Optional[str] = None
    ids: List[str] = []
    confirm: bool = False


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_api_key)])
def chat(req: ChatRequest) -> ChatResponse:
    if req.mode:
        agent.set_mode(req.mode)
    result = agent.handle(req.message)
    debug_data = None
    if req.debug:
        debug_data = {
            "memory_context": result.memory_context,
            "note_context": result.note_context,
            "rag_context": result.rag_context,
        }
    return ChatResponse(
        reply=result.text,
        mode=result.mode,
        skill_used=result.skill_used,
        memory_used=result.memory_used,
        vision_used=result.vision_used,
        memory_updates=result.memory_updates,
        note_context=result.note_context,
        rag_context=result.rag_context,
        plan=result.plan,
        debug_data=debug_data,
        mood=result.mood,
        personality_profile=result.personality_profile,
        journal_suggested=result.journal_suggested,
    )


@app.post("/plan", response_model=PlanResponse, dependencies=[Depends(require_api_key)])
def create_plan(req: PlanRequest) -> PlanResponse:
    if not req.goal.strip():
        raise HTTPException(status_code=400, detail="goal is required")
    result = agent.orchestrator.create_plan(req.goal)
    return PlanResponse(message=result.text, plan=result.plan or {}, memory_updates=result.memory_updates)


@app.post("/automation/run", response_model=AutomationResponse, dependencies=[Depends(require_api_key)])
def run_automation(req: AutomationRequest) -> AutomationResponse:
    if not req.action_id and not req.workflow_id:
        raise HTTPException(status_code=400, detail="action_id or workflow_id is required")
    results: List[str] = []
    if req.action_id:
        if req.action_id.startswith("ha."):
            name = req.action_id.split("ha.", 1)[1]
            ha_map = {
                "ac_on": ha_actions.ac_on,
                "relax_lights": ha_actions.relax_lights,
                "goodnight": ha_actions.goodnight,
            }
            func = ha_map.get(name)
            if not func:
                raise HTTPException(status_code=404, detail="ha action not found")
            results.append(asyncio.run(func()))
        else:
            results.append(ENGINE.run_action(req.action_id))
    if req.workflow_id:
        results.extend(ENGINE.run_workflow(req.workflow_id))
    return AutomationResponse(results=results)


@app.post("/events", dependencies=[Depends(require_api_key)])
def receive_event(payload: EventPayload) -> Dict[str, Any]:
    event_id = log_event("external.event", {"source": payload.source, "type": payload.type, "event": payload.event, "metadata": payload.metadata})
    handled = agent.orchestrator.handle_home_event(payload.dict())
    presence = handle_presence_event(payload.dict(), agent.orchestrator.current_mode.name)
    return {"status": "ok", "event_id": event_id, "handled": handled, "presence": presence}


@app.post("/push/send", dependencies=[Depends(require_api_key)])
def send_push(payload: PushPayload) -> Dict[str, Any]:
    result = mobile_push.send_push(payload.token, payload.title, payload.body, payload.data)
    log_event("push.send", {"token": payload.token[:8] + "...", "title": payload.title})
    return {"status": "ok", "result": result}


@app.post("/forget", dependencies=[Depends(require_api_key)])
def forget(req: ForgetRequest) -> Dict[str, Any]:
    if not req.confirm:
        raise HTTPException(status_code=400, detail="confirmation required to forget")
    stats = DB.forget(query=req.query, ids=req.ids)
    return {"status": "ok", "stats": stats}


@app.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    plans = planner.get_plans()
    journal_entries = DB.list_journal_entries(limit=1000)
    return StatusResponse(
        mode=agent.orchestrator.current_mode.name,
        last_input=agent.last_input,
        last_output=agent.last_output,
        plans_count=len(plans),
        automation_safe_mode=not ENGINE.config.allow_automation,
        vision_enabled=CONFIG.vision_enabled,
        mood_enabled=CONFIG.mood_enabled,
        personality_profile=CONFIG.personality_profile,
        journal_count=len(journal_entries),
        mood_entries=len(DB.recent_mood(9999)),
        env=CONFIG.env,
    )
