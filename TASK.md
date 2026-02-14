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

## Discovered During Work

- [x] Fix unsupported `TargetType.HEART_RATE_ZONE` constant in running warmup step.
- [x] Add AST-based test to lock MCP exposed tool list and avoid regressions.
