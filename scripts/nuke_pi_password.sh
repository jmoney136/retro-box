#!/bin/sh
set -eu

USER=pi

if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root (sudo)." >&2
    exit 1
fi

# Set empty password for user pi
passwd -d $USER

# Lock or unlock account password if needed (commented out here)
# passwd -l $USER  # Lock password (disable login with password)
# passwd -u $USER  # Unlock password

echo "Password for user '$USER' has been nuked (removed)."
exit 0
