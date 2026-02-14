#!/bin/bash
ssh -q -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=QUIET -i "/Users/carlescamarasabotella/Library/CloudStorage/GoogleDrive-carlescamarasa@gmail.com/La meva unitat/Altres/Obsidian/mcp-garmin/id_ed25519_local" root@92.113.27.70 "docker exec -i garmin-mcp python3 -u /app/server.py"
