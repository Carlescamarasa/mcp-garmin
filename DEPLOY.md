# Deployment Guide

## Prerequisites
- VPS with Docker and Docker Compose installed.
- SSH access to VPS.
- Valid `session.json` generated locally via `login_once.py`.

## 1. Setup on VPS
1.  **Clone Repository**:
    ```bash
    git clone <your-repo-url> secretaria-garmin-mcp
    cd secretaria-garmin-mcp
    ```
2.  **Transfer Secrets**:
    Copy your local `session.json` to the VPS securely.
    **CRITICAL**: `session.json` is NOT in the repository. You must copy it manually.
    ```bash
    scp -r session.json user@your-vps:/path/to/secretaria-garmin-mcp/session.json
    ```

## 2. Docker Deployment
You can run the container directly or use Docker Compose.

### Option A: Docker Run
```bash
# Build image
docker build -t garmin-mcp .

# Run container (mounting session.json)
docker run -d \
  --name garmin-mcp \
  -v $(pwd)/session.json:/app/session.json \
  --restart unless-stopped \
  garmin-mcp
```

### Option B: Docker Compose (Recommended)
Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  app:
    build: .
    volumes:
      - ./session.json:/app/session.json
    restart: unless-stopped
```
Run:
```bash
docker-compose up -d --build
```

## 3. Session Management
The session token (`session.json`) may expire.
- If it expires, the service will fail to authenticate.
- **To refresh**:
    1.  Run `python login_once.py` LOCALLY to generate a new valid `session.json` (requires MFA/login).
    2.  `scp` the new `session.json` to replace the one on the VPS.
    3.  Restart the container: `docker restart garmin-mcp`.
