#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
LOG_DIR=${XDG_STATE_HOME:-"$HOME/.local/state"}/retrobox
LOG_FILE=$LOG_DIR/launcher.log

mkdir -p "$LOG_DIR"
if [ -n "${DISPLAY:-}" ] && command -v xrandr >/dev/null 2>&1; then
	xrandr --output HDMI-1 --mode 1920x1080 --rate 60.00 >/dev/null 2>&1 || true
fi
cd "$PROJECT_DIR"
exec python3 -m retrobox >> "$LOG_FILE" 2>&1
