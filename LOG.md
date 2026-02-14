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
