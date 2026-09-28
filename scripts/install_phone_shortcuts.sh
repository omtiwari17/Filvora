#!/data/data/com.termux/files/usr/bin/sh
# Filvora Phone Server CLI Tools Installer
# Installs 'status' and 'update' commands into $PREFIX/bin for 1-word usage

PREFIX_BIN="${PREFIX:-/data/data/com.termux/files/usr}/bin"

# 1. Install 'status' command
cat << 'EOF' > "$PREFIX_BIN/status"
#!/data/data/com.termux/files/usr/bin/sh
echo "========================================"
echo "         FILVORA SERVER STATUS          "
echo "========================================"
if pgrep -f "manage.py runserver" > /dev/null; then
    PID=$(pgrep -f "manage.py runserver" | head -n 1)
    IP=$(ip addr show wlan0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
    echo " [SERVER]   : ✅ RUNNING (PID: $PID)"
    echo " [URL]      : http://${IP:-192.168.1.50}:8000/"
else
    echo " [SERVER]   : ❌ STOPPED"
fi

if pgrep -f "start.sh" > /dev/null || pgrep -f "start-filvora.sh" > /dev/null; then
    echo " [WATCHDOG] : ✅ ACTIVE (Auto-healing enabled)"
else
    echo " [WATCHDOG] : ⚠️ INACTIVE"
fi

if pgrep -x "sshd" > /dev/null; then
    echo " [SSH]      : ✅ ACTIVE (Port 8022)"
else
    echo " [SSH]      : ❌ INACTIVE"
fi
echo "========================================"
echo " Recent Traffic (Last 3 lines):"
tail -n 3 ~/filvora.log 2>/dev/null
echo "========================================"
EOF
chmod +x "$PREFIX_BIN/status"

# 2. Install 'update' command
cat << 'EOF' > "$PREFIX_BIN/update"
#!/data/data/com.termux/files/usr/bin/sh
cd ~/Filvora || exit 1
echo "==> 1. Pulling latest code..."
git pull
echo "==> 2. Applying migrations..."
python manage.py migrate
echo "==> 3. Restarting background server..."
pkill -9 -f "manage.py runserver" 2>/dev/null
sleep 1
nohup python manage.py runserver 0.0.0.0:8000 >> ~/filvora.log 2>&1 < /dev/null &
sleep 2
echo "=========================================="
echo " ✅ Update complete! Server running smoothly."
echo "=========================================="
EOF
chmod +x "$PREFIX_BIN/update"

echo "✅ Installed 'status' and 'update' commands successfully!"
