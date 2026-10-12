#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
START_SCRIPT=$SCRIPT_DIR/start_retrobox.sh
LOG_DIR=${XDG_STATE_HOME:-"$HOME/.local/state"}/retrobox
LOG_FILE=$LOG_DIR/launcher.log

mkdir -p "$LOG_DIR"

if [ -z "${DISPLAY:-}" ]; then
 	# if [ -n "${SSH_CONNECTION:-}" ]; then
 	# 	echo "Run RetroBox from the Pi's local console, not over SSH." >&2
 	# 	exit 1
 	# fi
 	if ! command -v startx >/dev/null 2>&1 || ! command -v openbox-session >/dev/null 2>&1; then
 		echo "startx and openbox-session are required to start RetroBox without a desktop." >&2
 		exit 1
 	fi
 	exec startx /bin/sh -c 'openbox-session & exec "$1"' retrobox "$START_SCRIPT"
fi

if command -v xrandr >/dev/null 2>&1; then
	if ! xrandr --query >/dev/null 2>&1; then
		for auth_file in /tmp/serverauth.*; do
			[ -r "$auth_file" ] || continue
			if DISPLAY="$DISPLAY" XAUTHORITY="$auth_file" xrandr --query >/dev/null 2>&1; then
				XAUTHORITY=$auth_file
				export XAUTHORITY
				break
			fi
		done
	fi
	xrandr --output HDMI-1 --mode 1920x1080 --rate 60.00 >/dev/null 2>&1 || true
fi
cd "$PROJECT_DIR"
pkill -f retroarch || true
exec python3 -m retrobox >> "$LOG_FILE" 2>&1
