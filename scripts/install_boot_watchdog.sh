#!/data/data/com.termux/files/usr/bin/sh
# Filvora & Vishwaguru Unified 24/7 Boot Watchdog Installer
# Usage: bash scripts/install_boot_watchdog.sh [TTYD_USER] [TTYD_PASS] [TUNNEL_NAME]

TTYD_USER="${1}"
TTYD_PASS="${2}"
TUNNEL_NAME="${3:-phone-server}"

if [ -z "$TTYD_USER" ]; then
    printf "Enter Web Terminal (ttyd) username: "
    read -r TTYD_USER
fi
if [ -z "$TTYD_PASS" ]; then
    printf "Enter Web Terminal (ttyd) password: "
    read -r TTYD_PASS
fi

if [ -z "$TTYD_USER" ] || [ -z "$TTYD_PASS" ]; then
    echo "Error: ttyd username and password are required."
    echo "Usage: bash scripts/install_boot_watchdog.sh <USER> <PASS> [TUNNEL_NAME]"
    exit 1
fi

echo "==> 1. Backing up existing boot scripts to ~/.termux/boot_backup..."
mkdir -p "$HOME/.termux/boot" "$HOME/.termux/boot_backup"
for f in "$HOME/.termux/boot/"*.sh; do
    [ -e "$f" ] && mv "$f" "$HOME/.termux/boot_backup/"
done

echo "==> 2. Stopping old watchdog processes..."
pkill -f "[s]tart-filvora\.sh" 2>/dev/null
pkill -f "[s]tart-services\.sh" 2>/dev/null

echo "==> 3. Writing unified watchdog to ~/.termux/boot/start-services.sh..."
cat << EOF > "$HOME/.termux/boot/start-services.sh"
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock

if ! ip addr show wlan0 2>/dev/null | grep -q "inet "; then
    sleep 8
fi

echo "[\$(date)] Unified Fleet Watchdog Started" >> ~/services.log

while true; do
    # 1. OpenSSH (Port 8022)
    if ! pgrep -x "sshd" > /dev/null; then
        sshd 2>/dev/null
    fi

    # 2. Filvora (Port 8000)
    if ! pgrep -f "runserver.*8000" > /dev/null; then
        echo "[\$(date)] Filvora (8000) down. Restarting..." >> ~/filvora.log
        pkill -9 -f "runserver.*8000" 2>/dev/null
        sleep 1
        if [ -d "\$HOME/Filvora" ]; then
            cd "\$HOME/Filvora" && nohup python manage.py runserver 0.0.0.0:8000 >> ~/filvora.log 2>&1 < /dev/null &
        fi
        sleep 2
    fi

    # 3. Vishwaguru Billing (Port 8080)
    if ! pgrep -f "runserver.*8080" > /dev/null; then
        echo "[\$(date)] Vishwaguru (8080) down. Restarting..." >> ~/billing.log
        pkill -9 -f "runserver.*8080" 2>/dev/null
        sleep 1
        BILLING_DIR="\$HOME/vishwaguru-billing"
        [ ! -d "\$BILLING_DIR" ] && [ -d "\$HOME/Vishwaguru-Billing" ] && BILLING_DIR="\$HOME/Vishwaguru-Billing"
        [ ! -d "\$BILLING_DIR" ] && [ -d "\$HOME/billing" ] && BILLING_DIR="\$HOME/billing"
        if [ -d "\$BILLING_DIR" ]; then
            cd "\$BILLING_DIR" && nohup python manage.py runserver 0.0.0.0:8080 >> ~/billing.log 2>&1 < /dev/null &
        fi
        sleep 2
    fi

    # 4. Web Terminal ttyd (Port 7681)
    if ! pgrep -x "ttyd" > /dev/null && ! pgrep -f "ttyd.*7681" > /dev/null; then
        echo "[\$(date)] Web Terminal (7681) down. Restarting..." >> ~/services.log
        nohup ttyd -p 7681 -c "$TTYD_USER:$TTYD_PASS" -W login > /dev/null 2>&1 < /dev/null &
        sleep 1
    fi

    # 5. Cloudflare Permanent Tunnel
    if ! pgrep -f "cloudflared tunnel run" > /dev/null; then
        echo "[\$(date)] Cloudflare Tunnel ($TUNNEL_NAME) down. Restarting..." >> ~/services.log
        nohup cloudflared tunnel run "$TUNNEL_NAME" >> ~/terminal.log 2>&1 < /dev/null &
        sleep 2
    fi

    # 6. Rotate logs if larger than 2MB
    for log in ~/filvora.log ~/billing.log ~/terminal.log ~/services.log; do
        if [ -f "\$log" ] && [ "\$(wc -c < "\$log")" -gt 2097152 ]; then
            tail -n 500 "\$log" > "\${log}.tmp" && mv "\${log}.tmp" "\$log"
        fi
    done

    sleep 30
done
EOF

chmod +x "$HOME/.termux/boot/start-services.sh"

echo "==> 4. Starting unified watchdog in background..."
nohup "$HOME/.termux/boot/start-services.sh" > /dev/null 2>&1 < /dev/null &
sleep 3
echo "✅ Unified Watchdog installed and running!"
