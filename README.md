# mcp-garmin

MCP server (Python) to query Garmin Connect data and manage workouts from AI clients.

## Current tool surface (clean cut)

This server now exposes only **3 MCP tools**:

1. `garmin_health_report`
   - Aggregates health and performance data for one date.
   - Supports `mode=summary` (fewer API calls) and `mode=full` (maximum coverage).
   - Returns a stable `summary` object plus `availableSections`, `unavailableSections`, and `errors`.

2. `garmin_manage_workout`
    - Single entry-point for workout management actions:
      - `create`
      - `list_scheduled`
      - `list_library`
      - `update`
      - `delete`
      - `apply_week_plan`
    - `create` and `update` support structured `steps` payloads (`workout_step` and `repeat_group`) so Garmin devices can guide reps/time/rest directly instead of only showing a free-text note.
    - `create` auto-detects `Força A/B/C` names and uses structured templates (circuits/repeat groups) instead of a generic 3-step workout.
    - When requesting `sport_type=HIIT`, Garmin may not persist custom HIIT workout types. The server applies `cardio_training` for reliability and returns explicit metadata (`requestedSportType`, `appliedSportType`, `warning`).
    - Keeps an internal local index for scheduled sessions in `scheduled_workouts_index.json`.

3. `garmin_activity_query`
   - `action=list` for activities by date range.
   - `action=detail` for one activity by id.

## Why a local scheduled index is required

Garmin Connect public/private endpoints are stable for workout CRUD but not reliable for listing
scheduled sessions by date range in this MCP scenario. To keep granular CRUD robust, the server
stores MCP-managed scheduled sessions in `scheduled_workouts_index.json`.

## Configuration

- `GARMIN_SESSION_PATH` (default: `session.json`)
- `GARMIN_WORKOUT_INDEX_PATH` (default: `scheduled_workouts_index.json`)

## Run locally

```bash
python3 server.py
```

## Tests

```bash
python3 -m unittest -v tests/test_server_tool_surface.py tests/test_scheduled_workouts_store.py
```
