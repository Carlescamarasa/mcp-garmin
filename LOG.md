# Project Log

## 2026-02-14
### AI Agent
- Initialized project structure (`PLANNING.md`, `TASK.md`, `LOG.md`).
- Verified `.gitignore` configuration for sensitive files (`session.json`, `.venv`).
- Validated Git initialization and GitHub sync.
- **GitHub Integration**: Confirmed remote `origin` is set and code is pushed to `main`.
- **VPS Deployment**: 
    - Created detailed `DEPLOY.md` guide.
    - Guided user through `scp -r` transfer of `session.json` directory.
    - Added `docker-compose.yml` and fixed restart loop by setting `command: tail -f /dev/null`.
- **Client Configuration**:
    - Guided user through SSH key setup.
    - Provided `mcp_config.json` snippet for SSH-based remote execution.
- **Status**: System is operational and responding to MCP requests from Antigravity.

### Developer
- Reworked `create_user_workouts.py` to generate structured sessions with real blocks (warmup, repeat groups, cooldown).
- Added explicit builders for Força A/B/C and Running Suau, aligned with weekly plan logic.
- Added `--dry-run` and `--from-date` options to preview the plan safely before uploading.
- Fixed Garmin compatibility issue by removing unsupported `TargetType.HEART_RATE_ZONE` usage.
- Added unit tests in `tests/test_create_user_workouts.py` for structure validation and weekday scheduling.

### Developer
- Simplified `server.py` to a lean tool surface (18 core tools) and removed redundant tool exposure.
- Confirmed `create_running_workout` is no longer exposed as an MCP tool.
- Improved docstrings for every exposed tool with clearer input/output details.
- Added `tests/test_server_tool_surface.py` to lock exposed tool list and prevent regressions.
- Deployed updated `server.py` to VPS and validated tool list + dry-run planning flow.

### Developer
- Applied clean-cut migration to 3 tools: `garmin_health_report`, `garmin_manage_workout`, and `garmin_activity_query`.
- Added local persistence module `scheduled_workouts_store.py` to support robust workout CRUD by date range.
- Refactored workout management into a single action-based API (`create`, `list_scheduled`, `list_library`, `update`, `delete`, `apply_week_plan`).
- Tightened tool docstrings with explicit input/output contracts and added regression tests for the new tool surface.
- Added `README.md` documenting the new minimal architecture and index-based scheduling behavior.

### Developer
- Fixed malformed strength sessions created via `garmin_manage_workout(action="create")`: Força A/B/C now map to structured workout templates with repeat groups.
- Added `workout_payload_utils.py` to centralize payload construction and template compatibility logic.
- Implemented sport-type compatibility fallback for HIIT template payloads to avoid Garmin returning `sportType = null`.
- Validated on VPS with real create/delete checks: Força A/B/C now preserve circuit/repeat structure and compatible sport type.

### Developer
- Added strict HIIT workflow in `garmin_manage_workout(action="create", sport_type="HIIT")`: tries Garmin ids 180 and 33.
- If Garmin persists HIIT as null/non-hiit, the temporary workouts are deleted and the tool now returns an explicit error (no silent downgrade to HIIT-null).
- Reverse-engineered user TEST entries: they are activities (not workouts) with activity ids `21870440239` (TEST FORÇA) and `21870435654` (TEST HIIT).

### Developer
- Cleaned Garmin workout library completely (remote account): all custom workouts deleted and local schedule index reset.
- Switched HIIT creation behavior back to stable cardio fallback with explicit response metadata.
- `garmin_manage_workout(action="create", sport_type="HIIT")` now returns `requestedSportType="hiit"`, `appliedSportType="cardio_training"`, and a warning message.
- Revalidated end-to-end on VPS: HIIT create succeeds, persists as `cardio_training`, and no orphan test workouts remain.

## 2026-02-15
### Developer
- Added `steps` support to `garmin_manage_workout` so structured reps/time/rest blocks are converted into Garmin workout step JSON.
- Implemented a new parser module (`structured_workout_steps.py`) with validation, alias mapping, repeat-group recursion, and duration estimation.
- Updated create flow so structured workouts can be created even without explicit `description` (fallback description is auto-applied).
- Added unit tests in `tests/test_structured_workout_steps.py` covering expected mapping, repeat-group edge case, and invalid payload errors.

### Developer
- Extended `garmin_manage_workout(action="update")` to accept `steps` and apply them to Garmin PUT payloads, enabling real restructuring of existing workouts.
- Added update-specific response metadata (`structuredStepsApplied`) and duration inference from existing workout data.
- Added regression coverage for update with structured steps in `tests/test_structured_workout_steps.py`.
