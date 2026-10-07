#!/bin/bash
tmux kill-session -t evo 2>/dev/null
tmux kill-session -t tunnel 2>/dev/null
pkill -9 -f "dashboard.py" 2>/dev/null
pkill -9 -f "webui.py" 2>/dev/null
pkill -f "ssh.*localhost.run" 2>/dev/null
echo "✓ همه‌چیز خاموش شد"
