# 🔒 Filvora Secure Remote Access & Deployment Guide

This guide details how to securely access Filvora outside your local Wi-Fi network without exposing development ports insecurely.

---

## 1. Local Network Access (Same Wi-Fi)

To stream from your phone, tablet, or smart TV on the same Wi-Fi network:

1. Find your machine's local IPv4 address:
   - **Windows PowerShell**: `ipconfig` (e.g. `192.168.1.50`)
2. Run the development server bound to all interfaces:
   ```powershell
   .\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
   ```
3. Open `http://192.168.1.50:8000` on your mobile browser.

---

## 2. Remote Access via Tailscale (Recommended & Private)

**Tailscale** provides encrypted peer-to-peer WireGuard networking without opening router ports or exposing your instance to the public internet:

1. Install **Tailscale** on your host PC and your mobile phone / laptop.
2. Sign in to both with the same account.
3. Access Filvora from anywhere on cellular data or outside networks via your host machine's 100.x.x.x Tailscale IP:
   `http://<tailscale-ip>:8000`

---

## 3. Remote Access via Cloudflare Tunnel (Free HTTPS Domain)

**Cloudflare Tunnels** expose Filvora with automatic SSL termination and DDoS protection without opening inbound router firewall ports:

1. Install `cloudflared`:
   ```powershell
   winget install Cloudflare.cloudflared
   ```
2. Start quick tunnel:
   ```powershell
   cloudflared tunnel --url http://localhost:8000
   ```
3. Add the generated `https://xxxx.trycloudflare.com` URL to `CSRF_TRUSTED_ORIGINS` in `.env`:
   ```env
   CSRF_TRUSTED_ORIGINS=https://xxxx.trycloudflare.com
   ```

---

## 4. Production Docker + Caddy Stack

For dedicated 24/7 home server deployment with automatic SSL certificate issuance:

```bash
cd deploy
docker compose up -d --build
```
Caddy automatically handles HTTPS renewals, Gzip compression, and proxies upstream traffic to Gunicorn.
