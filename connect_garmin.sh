#!/bin/bash
# Reason: Use local key for Antigravity environment compatibility
ssh -q -i "/Users/carlescamarasabotella/Library/CloudStorage/GoogleDrive-carlescamarasa@gmail.com/La meva unitat/Altres/Obsidian/mcp-garmin/id_ed25519_local" -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 root@92.113.27.70 "docker exec -i garmin-mcp python /app/server.py" 2>/dev/null
