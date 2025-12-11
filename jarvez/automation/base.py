from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from jarvez.config import JarvezConfig


@dataclass
class Action:
    id: str
    description: str
    execute: Callable[[], str]
    requires_allow: bool = True


@dataclass
class Workflow:
    id: str
    description: str
    actions: List[str] = field(default_factory=list)


class AutomationEngine:
    def __init__(self, config: JarvezConfig, actions: Dict[str, Action], workflows: Dict[str, Workflow]):
        self.config = config
        self.actions = actions
        self.workflows = workflows

    def run_action(self, action_id: str) -> str:
        action = self.actions.get(action_id)
        if not action:
            return f"ACTION_NOT_FOUND: {action_id}"
        if action.requires_allow and not self.config.allow_automation:
            return f"SAFE_MODE: automation disabled for {action_id}"
        try:
            result = action.execute()
            logging.info("Automation action executed: %s -> %s", action_id, result)
            return result
        except Exception as exc:
            logging.error("Automation action failed: %s (%s)", action_id, exc)
            return f"ACTION_ERROR: {exc}"

    def run_workflow(self, workflow_id: str) -> List[str]:
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return [f"WORKFLOW_NOT_FOUND: {workflow_id}"]
        results = []
        for action_id in workflow.actions:
            results.append(self.run_action(action_id))
        logging.info("Automation workflow executed: %s", workflow_id)
        return results
