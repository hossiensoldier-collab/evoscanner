#!/bin/bash
pkill -f "webui" 2>/dev/null
pkill -f "graph_web" 2>/dev/null
pkill -f "api.py" 2>/dev/null
sleep 1
echo "✓ پورت‌ها آزاد"
