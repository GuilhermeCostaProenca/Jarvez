# Planner (v0.4)

## Capabilities
- Goal decomposition into actionable steps.
- Plan persistence in `data/planner.json`.
- Note creation for every plan (stores steps).
- Dynamic memory + RAG indexing for new plans.
- Follow-up summaries of open plans.

## Flow
1. User asks for a plan or gives a multi-step request.
2. Orchestrator routes to planner skill (or auto-detects multi-step) -> `planner.plan_goal`.
3. Plan saved to `planner.json`, note created, memory updated, and RAG indexed.
4. Follow-up (`follow up ...`) reads stored plans and summarizes.

## Commands
- `plan <goal>` / `plano <goal>` / `goal ...`
- `me ajuda a <objetivo>` (multi-step trigger)
- `follow up` / `seguir plano`

## Extensibility
- Add dependencies/dates per task.
- Add reminders and notifications.
- Add execution hooks to trigger other skills per step.
