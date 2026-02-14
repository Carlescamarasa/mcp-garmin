# Secretaria Garmin MCP

## Overview
This project is an MCP (Model Context Protocol) server written in Python to interface with Garmin Connect. It allows AI agents to retrieve data (activities, health metrics) and potentially upload workouts.

## Architecture
- **Language**: Python 3.10+
- **Core Library**: `garminconnect` (unofficial API)
- **Deployment**: Docker on VPS
- **Authentication**: `login_once.py` generates `session.json`. `server.py` uses this session.

## Security
- **CRITICAL**: `session.json` must NEVER be committed to version control.
- **CRITICAL**: `.env` and `.venv` must be ignored.

## File Structure
- `server.py`: Main MCP server logic.
- `login_once.py`: Authentication script.
- `Dockerfile` / `requirements.txt`: Deployment.
- `docs/`: Documentation (to be created).

## Roadmap
1.  Initialize Git with secure ignores.
2.  Connect to private GitHub repository.
3.  Deploy to VPS using Docker and secure volume mounting for `session.json`.
