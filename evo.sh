#!/bin/bash
cd ~/evoscanner
clear
echo ""
echo "  ◆ EvoScanner"
~/evoscanner/pre_run.sh
echo ""
python selfrun.py
sleep 1
python panel.py
