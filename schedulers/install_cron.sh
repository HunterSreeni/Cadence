#!/usr/bin/env bash
# cadence — Linux cron installer
# Usage:
#   ./install_cron.sh [path/to/config.json]
#   ./install_cron.sh --uninstall

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CADENCE_PY="$(cd "$SCRIPT_DIR/.." && pwd)/cadence.py"
CRON_TAG="# cadence-managed"

# ---------- helpers ----------

die()  { echo "ERROR: $1" >&2; exit 1; }
info() { echo ":: $1"; }

read_config_field() {
    local config_path="$1" field="$2"
    python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    c = json.load(f)
s = c.get('schedule', {})
print(s.get(sys.argv[2], ''))
" "$config_path" "$field"
}

time_to_cron() {
    # "09:00" -> "0 9"  (minute hour)
    local t="$1"
    local hour minute
    hour="$(echo "$t" | cut -d: -f1 | sed 's/^0//')"
    minute="$(echo "$t" | cut -d: -f2 | sed 's/^0//' | sed 's/^$/0/')"
    echo "$minute $hour"
}

day_name_to_num() {
    case "$(echo "$1" | tr '[:upper:]' '[:lower:]')" in
        sunday|sun)    echo 0 ;;
        monday|mon)    echo 1 ;;
        tuesday|tue)   echo 2 ;;
        wednesday|wed) echo 3 ;;
        thursday|thu)  echo 4 ;;
        friday|fri)    echo 5 ;;
        saturday|sat)  echo 6 ;;
        *) die "Unknown day: $1" ;;
    esac
}

# ---------- uninstall ----------

do_uninstall() {
    info "Removing cadence cron entries..."
    local tmp
    tmp="$(mktemp)"
    crontab -l 2>/dev/null | grep -v "$CRON_TAG" > "$tmp" || true
    crontab "$tmp"
    rm -f "$tmp"
    info "Done. All cadence cron entries removed."
    exit 0
}

# ---------- main ----------

if [[ "${1:-}" == "--uninstall" ]]; then
    do_uninstall
fi

CONFIG="${1:-$SCRIPT_DIR/../config.json}"
CONFIG="$(cd "$(dirname "$CONFIG")" && pwd)/$(basename "$CONFIG")"

[[ -f "$CONFIG" ]]     || die "Config not found: $CONFIG"
[[ -f "$CADENCE_PY" ]] || die "cadence.py not found: $CADENCE_PY"

command -v python3 >/dev/null 2>&1 || die "python3 not found"
command -v crontab >/dev/null 2>&1 || die "crontab not found"

# Read schedule from config
MORNING_TIME="$(read_config_field "$CONFIG" morning_time)"
EVENING_TIME="$(read_config_field "$CONFIG" evening_time)"
WEEKLY_DAY="$(read_config_field "$CONFIG" weekly_review_day)"
WEEKLY_TIME="$(read_config_field "$CONFIG" weekly_review_time)"

[[ -n "$MORNING_TIME" ]] || die "morning_time not set in config"
[[ -n "$EVENING_TIME" ]] || die "evening_time not set in config"
[[ -n "$WEEKLY_DAY" ]]   || die "weekly_review_day not set in config"
[[ -n "$WEEKLY_TIME" ]]  || die "weekly_review_time not set in config"

MORNING_CRON="$(time_to_cron "$MORNING_TIME")"
EVENING_CRON="$(time_to_cron "$EVENING_TIME")"
WEEKLY_CRON="$(time_to_cron "$WEEKLY_TIME")"
WEEKLY_DOW="$(day_name_to_num "$WEEKLY_DAY")"

PYTHON="$(command -v python3)"

# Build cron lines
ENTRIES=(
    "$MORNING_CRON * * * $PYTHON $CADENCE_PY morning $CRON_TAG"
    "$EVENING_CRON * * * $PYTHON $CADENCE_PY evening $CRON_TAG"
    "$WEEKLY_CRON * * $WEEKLY_DOW $PYTHON $CADENCE_PY weekly $CRON_TAG"
    "@reboot $PYTHON $CADENCE_PY listen $CRON_TAG"
)

echo ""
echo "=== Cadence Cron Entries ==="
echo ""
echo "  cadence.py : $CADENCE_PY"
echo "  config     : $CONFIG"
echo "  python     : $PYTHON"
echo ""
for entry in "${ENTRIES[@]}"; do
    echo "  $entry"
done
echo ""

read -rp "Install these cron entries? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    info "Aborted."
    exit 0
fi

# Backup existing crontab
BACKUP="/tmp/crontab-backup-$(date +%Y%m%d-%H%M%S)"
crontab -l > "$BACKUP" 2>/dev/null || true
info "Existing crontab backed up to $BACKUP"

# Remove old cadence entries, then append new ones
CLEANED="$(crontab -l 2>/dev/null | grep -v "$CRON_TAG" || true)"

{
    echo "$CLEANED"
    echo ""
    echo "# --- cadence scheduled tasks ---"
    for entry in "${ENTRIES[@]}"; do
        echo "$entry"
    done
} | crontab -

info "Cron entries installed. Verify with: crontab -l"
