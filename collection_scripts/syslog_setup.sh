#!/bin/bash

# FINAL PRODUCTION SYSLOG SETUP SCRIPT
# Enables UDP reception + configures log forwarding (server + client)
# Blog reference: Austin Newton Tech (Medium)

CONFIG_FILE="/etc/rsyslog.conf"
FORWARD_FILE="/etc/rsyslog.d/99-forwarding.conf"
BACKUP_FILE="/etc/rsyslog.conf.bak_$(date +%F_%H-%M-%S)"

if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run this script with sudo."
    exit 1
fi

clear
echo "========================================="
echo "   SYSLOG SERVER + CLIENT SETUP SCRIPT"
echo "========================================="
echo ""

# Ask for port
read -p "➡ Enter the UDP port for syslog reception (default 5140): " PORT
PORT=${PORT:-5140}

echo "➡ Backing up rsyslog.conf → $BACKUP_FILE"
cp "$CONFIG_FILE" "$BACKUP_FILE"

echo "➡ Enabling UDP syslog listener on port $PORT..."

# Uncomment module(load="imudp")
sed -i 's/^#module(load="imudp")/module(load="imudp")/' "$CONFIG_FILE"

# Detect if input() exists
if grep -q 'input(type="imudp"' "$CONFIG_FILE"; then
    sed -i "s|input(type=\"imudp\" port=\"[0-9]*\")|input(type=\"imudp\" port=\"$PORT\")|" "$CONFIG_FILE"
else
    # Append under module(load="imudp")
    sed -i "/module(load=\"imudp\")/a input(type=\"imudp\" port=\"$PORT\")" "$CONFIG_FILE"
fi

echo "✔ UDP syslog reception configured"
echo ""

# Ask SIEM IP for forwarding
read -p "➡ Enter SIEM / Central Server IP for forwarding: " SERVER_IP

echo "➡ Creating forwarding rule: *.* @@$SERVER_IP:$PORT"
echo "*.* @@$SERVER_IP:$PORT" > "$FORWARD_FILE"

echo "➡ Restarting rsyslog..."
systemctl restart rsyslog

echo ""
echo "========================================="
echo "          ✔ SETUP COMPLETE ✔"
echo "========================================="
echo ""
echo "Your machine is now configured to:"
echo "  ✓ RECEIVE syslog via UDP on port $PORT"
echo "  ✓ FORWARD ALL logs → $SERVER_IP:$PORT"
echo ""
echo "Verify listener:"
echo "  sudo ss -tulnp | grep $PORT"
echo ""
echo "Test logging:"
echo "  logger \"Test message from syslog_setup.sh\""
echo ""
echo "========================================="