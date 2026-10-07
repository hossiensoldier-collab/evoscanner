#!/bin/bash
FILE="$1"
[ -z "$FILE" ] && { echo "Usage: safe_edit.sh <file>"; exit 1; }
[ ! -f "$FILE" ] && { echo "Not found: $FILE"; exit 1; }
TS=$(date +%Y%m%d_%H%M%S)
mkdir -p ~/evoscanner/BACKUPS
DEST=~/evoscanner/BACKUPS/$(basename $FILE).$TS
cp "$FILE" "$DEST"
echo "✓ Backup: $DEST"
${EDITOR:-nano} "$FILE"
