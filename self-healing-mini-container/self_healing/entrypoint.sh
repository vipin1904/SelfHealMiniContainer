#!/usr/bin/env bash
# entrypoint.sh - start app and agent
set -e

# If your app binary exists at /app/app/start.sh or similar, start it in background.
# Adjust according to your mini container runtime structure.

if [ -x /app/app/start.sh ]; then
  /app/app/start.sh &              # start app in background (child process)
else
  echo "No app start script found - running only agent"
fi

# Start agent (runs in foreground)
python /app/agent.py
# If agent exits, container exits. That provides a single control point.
