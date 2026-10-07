#!/bin/bash
MODE="${1:-dash}"

echo ""
echo "  ◆ EvoScanner Online"
echo ""

# پاکسازی
tmux kill-session -t evo 2>/dev/null
tmux kill-session -t tunnel 2>/dev/null
pkill -9 -f "dashboard.py" 2>/dev/null
pkill -9 -f "cloudflared" 2>/dev/null
sleep 1

case "$MODE" in
  dash)
    PORT=8090
    tmux new -d -s evo "cd ~/evoscanner/webapp && python dashboard.py"
    ;;
  webui)
    PORT=8080
    tmux new -d -s evo "cd ~/evoscanner && python webui.py"
    ;;
  *)
    echo "  استفاده: online.sh [dash|webui]"
    exit 1
    ;;
esac

sleep 2
echo "  ✓ سرور روی :$PORT"
echo "  🌐 در حال ساخت تونل..."
echo ""

tmux new -d -s tunnel "ssh -o StrictHostKeyChecking=no -R 80:localhost:$PORT nokey@localhost.run 2>&1 | tee ~/evoscanner/tunnel.log"

# منتظر URL بمون
for i in {1..15}; do
  sleep 1
  URL=$(grep -o "https://[a-z0-9]*\.lhr\.life" ~/evoscanner/tunnel.log 2>/dev/null | tail -1)
  if [ -n "$URL" ]; then
    echo ""
    echo "  ╔══════════════════════════════════════════════╗"
    echo "  ║   ✅ آنلاین شد!                              ║"
    echo "  ╚══════════════════════════════════════════════╝"
    echo ""
    echo "  🌐 $URL"
    echo ""
    echo "  برای بستن:  evooff"
    echo ""
    exit 0
  fi
done

echo "  ⚠ URL پیدا نشد. لاگ:"
tail -10 ~/evoscanner/tunnel.log
