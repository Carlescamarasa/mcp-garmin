# Tasks

- [x] Implement custom workouts script `create_user_workouts.py`
    - [x] Monday: Força A
    - [x] Wednesday: Força B
    - [x] Friday: Força C
    - [x] Saturday: Running

- [x] Simplify MCP tool surface and remove redundant tools
    - [x] Keep only core health/training/activity/profile/workout tools
    - [x] Remove `create_running_workout` from exposed tools
    - [x] Add explicit and informative tool descriptions/docstrings

- [x] Clean-cut migration to 3 MCP tools (Mode B)
    - [x] Replace tool surface with `garmin_health_report`, `garmin_manage_workout`, `garmin_activity_query`
    - [x] Add local scheduled workout index for robust CRUD by date range
    - [x] Keep weekly plan support via `garmin_manage_workout(action="apply_week_plan")`
    - [x] Make tool docstrings explicit about inputs and output fields
    - [x] Add tests for tool surface and scheduled index behavior
    - [x] Fix `create` action so Força A/B/C use structured templates (repeat groups/circuits) instead of basic 3-step blocks
    - [x] Add strict HIIT create attempts (id180/id33) with explicit error when Garmin persists null sport type
    - [x] Revert HIIT strict failure to stable cardio fallback with explicit warning (`requestedSportType` vs `appliedSportType`)

- [x] Add structured workout steps support to `garmin_manage_workout`
    - [x] Extend MCP schema with optional `steps` argument in `create` action
    - [x] Map `steps` (reps/time/rest/repeat groups) to Garmin workout JSON payload
    - [x] Add unit tests for expected, edge, and invalid step payloads
    - [x] Update README docs for the new structured steps workflow

- [x] Extend structured steps behavior to `update` action
    - [x] Apply `steps` payload to PUT update so existing workouts can change internal structure
    - [x] Add regression test for update with structured steps
    - [x] Update docs to state `update` also supports `steps`

## Discovered During Work

- [x] Fix unsupported `TargetType.HEART_RATE_ZONE` constant in running warmup step.
- [x] Add AST-based test to lock MCP exposed tool list and avoid regressions.
- [x] Garmin may return `sportType = null` for HIIT custom templates; force `cardio_training` in MCP payload for compatibility.
