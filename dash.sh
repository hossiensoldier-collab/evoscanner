#!/bin/bash
pkill -9 -f "dashboard.py" 2>/dev/null
pkill -9 -f "webapp" 2>/dev/null
sleep 1
cd ~/evoscanner/webapp
nohup python dashboard.py > ~/evoscanner/dashboard.log 2>&1 &
sleep 2
IP=$(python -c "import socket; print(socket.gethostbyname(socket.gethostname()))" 2>/dev/null)
echo ""
echo "  ◆ EvoScanner Dashboard"
echo "  → http://localhost:8090"
echo "  → http://$IP:8090"
echo ""
