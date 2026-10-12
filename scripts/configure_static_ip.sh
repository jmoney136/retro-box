#!/bin/sh
set -eu

# Script to configure a static IP on Raspberry Pi

INTERFACE=${1:-eth0}
STATIC_IP=192.168.175.199
ROUTER=192.168.175.1
DNS=192.168.175.1
NETMASK=255.255.255.0

DHCPCD_CONF=/etc/dhcpcd.conf
BACKUP_CONF=/etc/dhcpcd.conf.bak

if [ ! -f "$DHCPCD_CONF" ]; then
    echo "$DHCPCD_CONF not found. Is dhcpcd installed?" >&2
    exit 1
fi

if [ ! -w "$DHCPCD_CONF" ]; then
    echo "You need to run this script as root to modify $DHCPCD_CONF" >&2
    exit 1
fi

# Backup original config
if [ ! -f "$BACKUP_CONF" ]; then
    cp "$DHCPCD_CONF" "$BACKUP_CONF"
    echo "Backed up original dhcpcd.conf to $BACKUP_CONF"
fi

# Remove existing static IP config for the interface
sed -i "/^interface $INTERFACE$/,/^$/d" "$DHCPCD_CONF"

# Append static IP config
cat >> "$DHCPCD_CONF" <<EOF
interface $INTERFACE
static ip_address=$STATIC_IP/24
static routers=$ROUTER
static domain_name_servers=$DNS

EOF

echo "Static IP $STATIC_IP configured on interface $INTERFACE."
echo "Please reboot or restart dhcpcd.service for changes to take effect."

exit 0
