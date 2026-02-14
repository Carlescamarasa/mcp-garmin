
import sys
import subprocess
import os
import logging

logging.basicConfig(filename="/tmp/garmin_mcp_bridge.log", level=logging.DEBUG)
logging.debug("Bridge started")

key_path = "/Users/carlescamarasabotella/Library/CloudStorage/GoogleDrive-carlescamarasa@gmail.com/La meva unitat/Altres/Obsidian/mcp-garmin/id_ed25519_local"
vps_host = "root@92.113.27.70"
cmd = "docker exec -i garmin-mcp python3 -u /app/server.py"

ssh_cmd = [
    "ssh", "-q", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
    "-o", "UserKnownHostsFile=/dev/null", "-o", "LogLevel=QUIET",
    "-i", key_path, vps_host, cmd
]

logging.debug(f"Running command: {' '.join(ssh_cmd)}")

try:
    # Use Popen to bridge stdin/stdout/stderr
    proc = subprocess.Popen(ssh_cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
    exit_code = proc.wait()
    logging.debug(f"Process exited with code: {exit_code}")
    sys.exit(exit_code)
except Exception as e:
    logging.error(f"Error in bridge: {e}")
    sys.exit(1)
