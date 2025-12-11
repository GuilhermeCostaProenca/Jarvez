from __future__ import annotations

from jarvez.automation.actions import build_actions
from jarvez.automation.base import AutomationEngine
from jarvez.automation.workflows import build_workflows
from jarvez.config import load_config


def build_engine() -> AutomationEngine:
    config = load_config()
    actions = build_actions()
    workflows = build_workflows()
    return AutomationEngine(config=config, actions=actions, workflows=workflows)


# Singleton-style engine for convenience
ENGINE = build_engine()
