#!/data/data/com.termux/files/usr/bin/bash
cd ~/evoscanner
pkill -f auto.sh 2>/dev/null
sleep 2
rm -f auto.pid
termux-wake-lock
nohup ./auto.sh > /dev/null 2>&1 &
echo $! > auto.pid
echo "daemon: $(cat auto.pid)"

