#!/bin/bash
psql -U postgres -d video_app -c "SELECT id, title, status, created_at FROM videos WHERE status IN ('pending', 'processing', 'failed') ORDER BY created_at DESC LIMIT 10;"
