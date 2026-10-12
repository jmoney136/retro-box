#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
START_SCRIPT=$PROJECT_DIR/scripts/start_retrobox.sh
CONFIG_HOME=${XDG_CONFIG_HOME:-"$HOME/.config"}
AUTOSTART_DIR=$CONFIG_HOME/autostart
AUTOSTART_FILE=$AUTOSTART_DIR/retrobox.desktop

usage() {
    echo "Usage: sh scripts/configure_autostart.sh [install|remove]" >&2
}

case "${1:-install}" in
    install)
        if [ ! -f "$PROJECT_DIR/retrobox/__main__.py" ] || [ ! -f "$PROJECT_DIR/retrobox/systems.json" ]; then
            echo "RetroBox project files were not found at: $PROJECT_DIR" >&2
            exit 1
        fi
        if ! command -v python3 >/dev/null 2>&1; then
            echo "python3 is required but was not found on PATH." >&2
            exit 1
        fi

        mkdir -p "$AUTOSTART_DIR"
        desktop_exec=$(printf '%s' "$START_SCRIPT" | sed 's/\\/\\\\/g; s/"/\\"/g')
        cat > "$AUTOSTART_FILE" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=RetroBox
Comment=Launch the RetroBox game library
Exec=/bin/sh "$desktop_exec"
Path=$PROJECT_DIR
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
        echo "Installed RetroBox desktop autostart: $AUTOSTART_FILE"
        echo "It will open when this user logs into the Raspberry Pi desktop."
        ;;
    remove)
        if [ -f "$AUTOSTART_FILE" ]; then
            rm "$AUTOSTART_FILE"
            echo "Removed RetroBox desktop autostart: $AUTOSTART_FILE"
        else
            echo "No RetroBox desktop autostart entry found."
        fi
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        usage
        exit 2
        ;;
esac
