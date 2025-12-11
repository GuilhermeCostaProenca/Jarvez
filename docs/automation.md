# Automation Engine (v0.4)

## Concepts
- Action: unit step (open app/url, create note, play playlist).
- Workflow: sequence of actions with an id and description.
- Safe mode: automation blocked unless `JARVEZ_ALLOW_AUTOMATION=1`.

## Files
- `automation/base.py`: Action, Workflow, AutomationEngine.
- `automation/actions.py`: predefined safe actions using env/config.
- `automation/workflows.py`: predefined workflows (study_networks, focus_session, curriculum_boost).
- `automation/engine.py`: builds the singleton `ENGINE`.
- `config.py`: centralizes paths and URLs.

## Actions (ids)
- `open_vscode` (workspace folder)
- `open_browser_default`
- `open_workspace_folder`
- `create_session_note`
- `play_playlist`

## Workflows (ids)
- `study_networks`: browser -> session note -> playlist.
- `focus_session`: VSCode -> session note -> playlist.
- `curriculum_boost`: VSCode -> session note.

## How to run
- Via API: `POST /automation/run` with `action_id` or `workflow_id`.
- Via code: `from jarvez.automation.engine import ENGINE; ENGINE.run_action("open_vscode")`

## Safety
- Requires `JARVEZ_ALLOW_AUTOMATION=1` for actions marked `requires_allow`.
- Logs automation attempts/results.

## Extensibility
- Add actions to `build_actions` using env-configured paths.
- Add workflows to `build_workflows` referencing action ids.
- Future: integrate with Home Assistant / external connectors.
