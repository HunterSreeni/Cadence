#!/usr/bin/env bash
# cadence — macOS launchd installer
# Usage:
#   ./install_launchd.sh [path/to/config.json]
#   ./install_launchd.sh --uninstall

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CADENCE_PY="$(cd "$SCRIPT_DIR/.." && pwd)/cadence.py"
LAUNCH_DIR="$HOME/Library/LaunchAgents"

PLIST_PREFIX="com.cadence"
PLISTS=(morning evening weekly listener)

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

day_name_to_num() {
    case "$(echo "$1" | tr '[:upper:]' '[:lower:]')" in
        sunday|sun)    echo 1 ;;
        monday|mon)    echo 2 ;;
        tuesday|tue)   echo 3 ;;
        wednesday|wed) echo 4 ;;
        thursday|thu)  echo 5 ;;
        friday|fri)    echo 6 ;;
        saturday|sat)  echo 7 ;;
        *) die "Unknown day: $1" ;;
    esac
}

plist_path() {
    echo "$LAUNCH_DIR/${PLIST_PREFIX}.${1}.plist"
}

# ---------- uninstall ----------

do_uninstall() {
    info "Removing cadence launchd agents..."
    for name in "${PLISTS[@]}"; do
        local label="${PLIST_PREFIX}.${name}"
        local pfile
        pfile="$(plist_path "$name")"
        if [[ -f "$pfile" ]]; then
            launchctl unload "$pfile" 2>/dev/null || true
            rm -f "$pfile"
            info "  Removed $label"
        fi
    done
    info "Done."
    exit 0
}

# ---------- plist generators ----------

write_calendar_plist() {
    local label="$1" command="$2" hour="$3" minute="$4" pfile="$5"
    local weekday="${6:-}"

    local weekday_block=""
    if [[ -n "$weekday" ]]; then
        weekday_block="            <key>Weekday</key>
            <integer>$weekday</integer>"
    fi

    cat > "$pfile" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$label</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$CADENCE_PY</string>
        <string>$command</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
$weekday_block
        <key>Hour</key>
        <integer>$hour</integer>
        <key>Minute</key>
        <integer>$minute</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/tmp/cadence-$command.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/cadence-$command.err</string>
</dict>
</plist>
PLIST
}

write_listener_plist() {
    local pfile="$1"
    cat > "$pfile" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_PREFIX}.listener</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$CADENCE_PY</string>
        <string>listen</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/tmp/cadence-listener.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/cadence-listener.err</string>
</dict>
</plist>
PLIST
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
PYTHON="$(command -v python3)"

# Ensure LaunchAgents dir exists
mkdir -p "$LAUNCH_DIR"

# Read schedule from config
MORNING_TIME="$(read_config_field "$CONFIG" morning_time)"
EVENING_TIME="$(read_config_field "$CONFIG" evening_time)"
WEEKLY_DAY="$(read_config_field "$CONFIG" weekly_review_day)"
WEEKLY_TIME="$(read_config_field "$CONFIG" weekly_review_time)"

[[ -n "$MORNING_TIME" ]] || die "morning_time not set in config"
[[ -n "$EVENING_TIME" ]] || die "evening_time not set in config"
[[ -n "$WEEKLY_DAY" ]]   || die "weekly_review_day not set in config"
[[ -n "$WEEKLY_TIME" ]]  || die "weekly_review_time not set in config"

# Parse times (strip leading zeros for plist integers)
M_HOUR="$((10#$(echo "$MORNING_TIME" | cut -d: -f1)))"
M_MIN="$((10#$(echo "$MORNING_TIME" | cut -d: -f2)))"
E_HOUR="$((10#$(echo "$EVENING_TIME" | cut -d: -f1)))"
E_MIN="$((10#$(echo "$EVENING_TIME" | cut -d: -f2)))"
W_HOUR="$((10#$(echo "$WEEKLY_TIME" | cut -d: -f1)))"
W_MIN="$((10#$(echo "$WEEKLY_TIME" | cut -d: -f2)))"
W_DOW="$(day_name_to_num "$WEEKLY_DAY")"

echo ""
echo "=== Cadence LaunchAgents ==="
echo ""
echo "  cadence.py : $CADENCE_PY"
echo "  config     : $CONFIG"
echo "  python     : $PYTHON"
echo "  plist dir  : $LAUNCH_DIR"
echo ""
echo "  Morning  : daily at ${MORNING_TIME}"
echo "  Evening  : daily at ${EVENING_TIME}"
echo "  Weekly   : ${WEEKLY_DAY} at ${WEEKLY_TIME}"
echo "  Listener : runs at login, kept alive"
echo ""

read -rp "Install these launch agents? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    info "Aborted."
    exit 0
fi

# Unload existing agents first
for name in "${PLISTS[@]}"; do
    pfile="$(plist_path "$name")"
    if [[ -f "$pfile" ]]; then
        launchctl unload "$pfile" 2>/dev/null || true
    fi
done

# Generate plists
write_calendar_plist "${PLIST_PREFIX}.morning" "morning" "$M_HOUR" "$M_MIN" "$(plist_path morning)"
info "Wrote $(plist_path morning)"

write_calendar_plist "${PLIST_PREFIX}.evening" "evening" "$E_HOUR" "$E_MIN" "$(plist_path evening)"
info "Wrote $(plist_path evening)"

write_calendar_plist "${PLIST_PREFIX}.weekly" "weekly" "$W_HOUR" "$W_MIN" "$(plist_path weekly)" "$W_DOW"
info "Wrote $(plist_path weekly)"

write_listener_plist "$(plist_path listener)"
info "Wrote $(plist_path listener)"

# Load all
for name in "${PLISTS[@]}"; do
    pfile="$(plist_path "$name")"
    launchctl load "$pfile"
    info "Loaded ${PLIST_PREFIX}.${name}"
done

echo ""
info "All agents installed. List with: launchctl list | grep cadence"
