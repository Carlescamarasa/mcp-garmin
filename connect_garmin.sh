#!/bin/bash
# Reason: Ensure SSH works in restricted/fresh environments
ssh -q -i /Users/carlescamarasabotella/.ssh/id_ed25519 -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 root@92.113.27.70 "docker exec -i garmin-mcp python /app/server.py" 2>/dev/null
