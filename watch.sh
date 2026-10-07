#!/data/data/com.termux/files/usr/bin/bash
cd ~/evoscanner

if [ -z "$1" ]; then
    echo "استفاده: watch.sh <file.py>"
    exit 1
fi

FILE="$1"
LAST=""

echo "👁 مانیتور $FILE (Ctrl+C برای توقف)"
echo "هر بار ذخیره کنی، پیشنهادها نمایش داده می‌شوند"
echo "───────────────────────────────────────────────"

while true; do
    if [ -f "$FILE" ]; then
        CUR=$(md5sum "$FILE" 2>/dev/null | cut -d' ' -f1)
        if [ "$CUR" != "$LAST" ]; then
            clear
            echo "📄 $FILE"
            echo "─────────────────────────────────────────────"
            ./esc suggest "$FILE"
            echo
            echo "─────────────────────────────────────────────"
            echo "آخرین بروزرسانی: $(date '+%H:%M:%S')"
            LAST="$CUR"
        fi
    fi
    sleep 1
done

