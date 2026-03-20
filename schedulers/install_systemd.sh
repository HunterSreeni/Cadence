#!/usr/bin/env bash
# Cadence — systemd service installer
# Installs the listener as a systemd service that auto-starts on boot.
# Usage: bash schedulers/install_systemd.sh [--uninstall]

set -euo pipefail

SERVICE_NAME="cadence"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$(command -v python3 || echo /usr/bin/python3)"

# ── Uninstall ──────────────────────────────────────────────
if [[ "${1:-}" == "--uninstall" ]]; then
    echo "Removing cadence systemd service..."
    sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    sudo systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    sudo rm -f "$SERVICE_FILE"
    sudo systemctl daemon-reload
    echo "Done. Service removed."
    exit 0
fi

# ── Check requirements ────────────────────────────────────
if ! command -v systemctl &>/dev/null; then
    echo "Error: systemctl not found. This installer requires systemd."
    echo "For cron-based setup, use: bash schedulers/install_cron.sh"
    exit 1
fi

if [[ ! -f "$SCRIPT_DIR/cadence.py" ]]; then
    echo "Error: cadence.py not found in $SCRIPT_DIR"
    exit 1
fi

if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
    echo "Warning: .env file not found. Bot token may not be set."
fi

# ── Generate service file ─────────────────────────────────
echo "Installing cadence systemd service..."
echo "  Working directory: $SCRIPT_DIR"
echo "  Python: $PYTHON"
echo ""

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Cadence Telegram Bot Listener
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$SCRIPT_DIR
ExecStart=$PYTHON cadence.py listen
Restart=always
RestartSec=10
EnvironmentFile=$SCRIPT_DIR/.env
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# ── Enable and start ──────────────────────────────────────
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

echo ""
echo "✓ Cadence listener installed and started."
echo ""
echo "Useful commands:"
echo "  sudo systemctl status cadence    — check status"
echo "  sudo journalctl -u cadence -f    — follow logs"
echo "  sudo systemctl restart cadence   — restart"
echo "  bash schedulers/install_systemd.sh --uninstall  — remove"
echo ""
echo "The listener will auto-start on boot."
