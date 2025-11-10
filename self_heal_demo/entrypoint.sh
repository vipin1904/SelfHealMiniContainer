#!/bin/sh

python3 /app/app.py & echo $! > /app/app.pid
python3 /app/agent.py
