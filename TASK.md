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

## Discovered During Work

- [x] Fix unsupported `TargetType.HEART_RATE_ZONE` constant in running warmup step.
- [x] Add AST-based test to lock MCP exposed tool list and avoid regressions.
