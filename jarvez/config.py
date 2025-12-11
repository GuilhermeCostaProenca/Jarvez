from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PathsConfig:
    vscode_path: str
    browser_path: Optional[str]
    workspace_dir: str
    default_url: str
    playlist_url: str
    default_capture_dir: str


@dataclass
class JarvezConfig:
    allow_automation: bool
    paths: PathsConfig
    vision_enabled: bool
    vision_provider: Optional[str]
    vision_allow_screen: bool
    vision_allow_camera: bool
    personality_profile: str
    mood_enabled: bool
    api_key: Optional[str]
    env: str
    ha_base_url: Optional[str]
    ha_webhook_token: Optional[str]


def load_config() -> JarvezConfig:
    workspace_dir = os.environ.get("JARVEZ_WORKSPACE_DIR", str(Path.cwd()))
    return JarvezConfig(
        allow_automation=os.environ.get("JARVEZ_ALLOW_AUTOMATION") == "1",
        vision_enabled=os.environ.get("JARVEZ_VISION_ENABLED") == "1",
        vision_provider=os.environ.get("JARVEZ_VISION_PROVIDER"),
        vision_allow_screen=os.environ.get("JARVEZ_VISION_ALLOW_SCREEN") == "1",
        vision_allow_camera=os.environ.get("JARVEZ_VISION_ALLOW_CAMERA") == "1",
        personality_profile=os.environ.get("JARVEZ_PERSONALITY_PROFILE", "default_gui"),
        mood_enabled=os.environ.get("JARVEZ_MOOD_ENABLED", "1") == "1",
        api_key=os.environ.get("JARVEZ_API_KEY"),
        env=os.environ.get("JARVEZ_ENV", "local"),
        ha_base_url=os.environ.get("HA_BASE_URL"),
        ha_webhook_token=os.environ.get("HA_WEBHOOK_TOKEN"),
        paths=PathsConfig(
            vscode_path=os.environ.get("JARVEZ_VSCODE", "code"),
            browser_path=os.environ.get("JARVEZ_BROWSER"),
            workspace_dir=workspace_dir,
            default_url=os.environ.get("JARVEZ_DEFAULT_URL", "https://www.google.com"),
            playlist_url=os.environ.get("JARVEZ_PLAYLIST_URL", "https://music.youtube.com"),
            default_capture_dir=os.environ.get("JARVEZ_CAPTURE_DIR", str(Path(workspace_dir) / "data" / "captures")),
        ),
    )
