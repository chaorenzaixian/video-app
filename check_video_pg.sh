#!/bin/bash
PGPASSWORD='VideoApp2024!' psql -h 127.0.0.1 -U video_app -d video_app -c "SELECT id, title, pay_type, coin_price, vip_coin_price, vip_free_level, free_preview_seconds FROM videos WHERE id = 218;"
