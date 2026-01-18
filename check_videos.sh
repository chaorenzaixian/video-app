#!/bin/bash
export PGPASSWORD='VideoApp2024!'
psql -U video_app -d video_app -h 127.0.0.1 -c "SELECT id, title, status, created_at FROM videos ORDER BY created_at DESC LIMIT 10;"
