#!/data/data/com.termux/files/usr/bin/bash
cd ~/evoscanner
LOG=auto.log
log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
log "=== start ==="
while true; do
    python evoscanner_v2.py reset-health >> "$LOG" 2>&1
    python evoscanner_v2.py run 2 >> "$LOG" 2>&1
    python evoscanner_v2.py enrich 30 >> "$LOG" 2>&1
    python evoscanner_v2.py rebuild >> "$LOG" 2>&1
    python evoscanner_v2.py agents >> "$LOG" 2>&1
    python evoscanner_v2.py learn >> "$LOG" 2>&1
    python evoscanner_v2.py export >> "$LOG" 2>&1
    log "done — 6h"
    sleep 21600
done

