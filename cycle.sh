#!/data/data/com.termux/files/usr/bin/bash
cd ~/evoscanner
LOG=cycle.log

log() {
    echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"
}

log "========== cycle start =========="

python evoscanner_v2.py reset-health  >> "$LOG" 2>&1
python evoscanner_v2.py run 2         >> "$LOG" 2>&1
python evoscanner_v2.py enrich 100     >> "$LOG" 2>&1
python evoscanner_v2.py rebuild       >> "$LOG" 2>&1
python evoscanner_v2.py agents        >> "$LOG" 2>&1
python evoscanner_v2.py learn         >> "$LOG" 2>&1
python evoscanner_v2.py export        >> "$LOG" 2>&1

log "========== cycle done =========="
log "منابع:"
python -c "
import sqlite3
c = sqlite3.connect('knowledge.db')
n = c.execute('SELECT COUNT(*) FROM resources').fetchone()[0]
print(f'  کل: {n}')
" | tee -a "$LOG"

