#!/data/data/com.termux/files/usr/bin/sh
# Filvora & Vishwaguru Phone Server CLI Tools Installer
# Installs 'status', 'update', 'update1', 'update2', and 'share-filvora' into $PREFIX/bin

PREFIX_BIN="${PREFIX:-/data/data/com.termux/files/usr}/bin"

# 1. Install 'status' command (Dual-App & Fleet Aware)
cat << 'EOF' > "$PREFIX_BIN/status"
#!/data/data/com.termux/files/usr/bin/sh
echo "=================================================="
echo "          REDMI SERVER FLEET STATUS               "
echo "=================================================="
IP=$(ip addr show wlan0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
IP="${IP:-192.168.1.50}"

# Filvora (Port 8000)
if pgrep -f "runserver.*8000" > /dev/null || (pgrep -f "Filvora.*manage.py" > /dev/null && pgrep -f "8000" > /dev/null); then
    PID=$(pgrep -f "8000" | head -n 1)
    echo " [FILVORA (8000)]   : ✅ RUNNING (PID: $PID)"
    echo "   Local URL        : http://$IP:8000/"
elif pgrep -f "manage.py runserver" > /dev/null; then
    PID=$(pgrep -f "manage.py runserver" | head -n 1)
    echo " [FILVORA (8000)]   : ✅ RUNNING (PID: $PID)"
    echo "   Local URL        : http://$IP:8000/"
else
    echo " [FILVORA (8000)]   : ❌ STOPPED"
fi

# Vishwaguru Billing (Port 8080)
if pgrep -f "runserver.*8080" > /dev/null || (pgrep -f "vishwaguru.*manage.py" > /dev/null && pgrep -f "8080" > /dev/null); then
    PID=$(pgrep -f "8080" | head -n 1)
    echo " [BILLING (8080)]   : ✅ RUNNING (PID: $PID)"
    echo "   Local URL        : http://$IP:8080/"
else
    echo " [BILLING (8080)]   : ⚪ NOT RUNNING (Port 8080)"
fi

# Web Terminal (ttyd on Port 7681)
if pgrep -x "ttyd" > /dev/null || pgrep -f "ttyd.*7681" > /dev/null; then
    PID=$(pgrep -f "ttyd" | head -n 1)
    echo " [TERMINAL (7681)]  : ✅ ACTIVE (PID: $PID)"
    echo "   Web Shell        : Remote Web Terminal (Port 7681 / Cloudflare Tunnel)"
else
    echo " [TERMINAL (7681)]  : ❌ STOPPED"
fi

# Cloudflare Tunnel
if pgrep -f "cloudflared tunnel run" > /dev/null; then
    echo " [CF TUNNEL]        : ✅ ACTIVE (phone-server permanent tunnel)"
elif pgrep -f "cloudflared tunnel --url" > /dev/null; then
    echo " [CF TUNNEL]        : ⚡ ACTIVE (trycloudflare quick tunnel)"
else
    echo " [CF TUNNEL]        : ❌ INACTIVE"
fi

# Watchdog & SSH
if pgrep -f "start-services.sh" > /dev/null || pgrep -f "start-filvora.sh" > /dev/null || pgrep -f "start.sh" > /dev/null; then
    echo " [WATCHDOG]         : ✅ ACTIVE (Auto-healing enabled)"
else
    echo " [WATCHDOG]         : ⚠️ INACTIVE"
fi

if pgrep -x "sshd" > /dev/null; then
    echo " [SSH (8022)]       : ✅ ACTIVE (Port 8022)"
else
    echo " [SSH (8022)]       : ❌ INACTIVE"
fi
echo "=================================================="
echo " Recent Filvora Traffic (Last 3 lines):"
tail -n 3 ~/filvora.log 2>/dev/null
echo "=================================================="
EOF
chmod +x "$PREFIX_BIN/status"

# 2. Install Smart Unified 'update' command
cat << 'EOF' > "$PREFIX_BIN/update"
#!/data/data/com.termux/files/usr/bin/sh

update_filvora() {
    FILVORA_DIR=""
    if [ -d "$HOME/Filvora" ]; then
        FILVORA_DIR="$HOME/Filvora"
    elif [ -d "$HOME/filvora" ]; then
        FILVORA_DIR="$HOME/filvora"
    else
        echo "❌ [FILVORA] Directory not found in $HOME (checked ~/Filvora and ~/filvora)"
        return 1
    fi

    echo "=================================================="
    echo " 🎬 UPDATING FILVORA (Port 8000)..."
    echo "=================================================="
    cd "$FILVORA_DIR" || return 1
    echo "==> 1. Pulling latest code from GitHub..."
    git pull
    echo "==> 2. Applying Django database migrations..."
    python manage.py migrate
    echo "==> 3. Restarting Filvora server (Port 8000)..."
    pkill -9 -f "runserver.*8000" 2>/dev/null
    pkill -9 -f "Filvora.*manage.py runserver" 2>/dev/null
    sleep 1
    nohup python manage.py runserver 0.0.0.0:8000 >> ~/filvora.log 2>&1 < /dev/null &
    sleep 2
    echo "=================================================="
    echo " ✅ Filvora updated and running at Port 8000!"
    echo "    Local URL: http://192.168.1.50:8000/"
    echo "=================================================="
}

update_billing() {
    BILLING_DIR=""
    if [ -d "$HOME/vishwaguru-billing" ]; then
        BILLING_DIR="$HOME/vishwaguru-billing"
    elif [ -d "$HOME/Vishwaguru-Billing" ]; then
        BILLING_DIR="$HOME/Vishwaguru-Billing"
    elif [ -d "$HOME/billing" ]; then
        BILLING_DIR="$HOME/billing"
    elif [ -d "$HOME/vishwaguru" ]; then
        BILLING_DIR="$HOME/vishwaguru"
    else
        echo "❌ [BILLING] Directory not found in $HOME!"
        echo "   Checked: ~/vishwaguru-billing, ~/Vishwaguru-Billing, ~/billing, ~/vishwaguru"
        return 1
    fi

    echo "=================================================="
    echo " 💼 UPDATING VISHWAGURU BILLING (Port 8080)..."
    echo "=================================================="
    cd "$BILLING_DIR" || return 1
    echo "==> 1. Pulling latest code from GitHub..."
    git pull
    echo "==> 2. Applying Django database migrations..."
    python manage.py migrate
    echo "==> 3. Restarting Billing server (Port 8080)..."
    pkill -9 -f "runserver.*8080" 2>/dev/null
    pkill -9 -f "vishwaguru.*manage.py runserver" 2>/dev/null
    sleep 1
    nohup python manage.py runserver 0.0.0.0:8080 >> ~/billing.log 2>&1 < /dev/null &
    sleep 2
    echo "=================================================="
    echo " ✅ Vishwaguru Billing updated and running at Port 8080!"
    echo "    Local URL: http://192.168.1.50:8080/"
    echo "=================================================="
}

TARGET="$1"

if [ -z "$TARGET" ]; then
    if [ -t 0 ]; then
        echo "=================================================="
        echo "            FLEET UPDATE SELECTOR                 "
        echo "=================================================="
        echo " Which site do you want to update?"
        echo "  [1] Filvora (Port 8000)"
        echo "  [2] Vishwaguru Billing (Port 8080)"
        echo "  [3] Both Sites"
        echo "=================================================="
        printf " Select option (1-3, default [1]): "
        read -r choice
        TARGET="${choice:-1}"
    else
        TARGET="1"
    fi
fi

case "$TARGET" in
    1|filvora|Filvora)
        update_filvora
        ;;
    2|billing|Billing|vishwaguru|Vishwaguru)
        update_billing
        ;;
    3|all|All|both|Both)
        update_filvora
        echo ""
        update_billing
        ;;
    *)
        echo "⚠️ Unknown target: '$TARGET'"
        echo "Usage: update [1|2|3|filvora|billing|all]"
        echo "  - update 1 (or update filvora): Updates Filvora (Port 8000)"
        echo "  - update 2 (or update billing): Updates Vishwaguru Billing (Port 8080)"
        echo "  - update 3 (or update all):     Updates Both Sites"
        exit 1
        ;;
esac
EOF
chmod +x "$PREFIX_BIN/update"

# 3. Install 'update1' alias (Directly updates Filvora)
cat << 'EOF' > "$PREFIX_BIN/update1"
#!/data/data/com.termux/files/usr/bin/sh
exec "$PREFIX/bin/update" 1
EOF
chmod +x "$PREFIX_BIN/update1"

# 4. Install 'update2' alias (Directly updates Vishwaguru Billing)
cat << 'EOF' > "$PREFIX_BIN/update2"
#!/data/data/com.termux/files/usr/bin/sh
exec "$PREFIX/bin/update" 2
EOF
chmod +x "$PREFIX_BIN/update2"

# 5. Install 'share-filvora' command (Cloudflare Quick Tunnel for Filvora)
cat << 'EOF' > "$PREFIX_BIN/share-filvora"
#!/data/data/com.termux/files/usr/bin/sh
echo "==> Stopping any previous quick tunnel..."
pkill -9 -f "cloudflared tunnel --url http://localhost:8000" 2>/dev/null
sleep 1

echo "==> Creating secure anonymous Cloudflare Quick Tunnel for Filvora..."
nohup cloudflared tunnel --url http://localhost:8000 > ~/filvora-tunnel.log 2>&1 < /dev/null &

echo "==> Connecting to Cloudflare edge..."
for i in 1 2 3 4 5 6; do
    sleep 1
    URL=$(grep -o 'https://[-a-zA-Z0-9]*\.trycloudflare\.com' ~/filvora-tunnel.log | head -n 1)
    if [ -n "$URL" ]; then
        echo "=================================================="
        echo " 🎬 FILVORA PUBLIC STREAMING LINK IS READY!"
        echo " $URL"
        echo "=================================================="
        echo " Share this link with friends and family to stream!"
        echo " (No VPN or apps required)"
        echo "=================================================="
        exit 0
    fi
done

echo "Tunnel started in background. Check your URL with:"
echo "cat ~/filvora-tunnel.log | grep trycloudflare"
EOF
chmod +x "$PREFIX_BIN/share-filvora"

echo "✅ Installed 'status', 'update', 'update1', 'update2', and 'share-filvora' commands successfully!"
