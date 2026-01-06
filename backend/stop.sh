#!/bin/bash
pkill -f "run.py" 2>/dev/null
fuser -k 8000/tcp 2>/dev/null
echo "Backend stopped"
