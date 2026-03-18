#!/usr/bin/env python3
"""
cadence -- Windows Task Scheduler installer.

Usage:
    python install_task_scheduler.py [path/to/config.json]
    python install_task_scheduler.py --uninstall
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

TASK_PREFIX = "Cadence"
TASK_NAMES = {
    "morning": f"{TASK_PREFIX} Morning",
    "evening": f"{TASK_PREFIX} Evening",
    "weekly": f"{TASK_PREFIX} Weekly",
    "listener": f"{TASK_PREFIX} Listener",
}

DAY_MAP = {
    "sunday": "SUN",
    "monday": "MON",
    "tuesday": "TUE",
    "wednesday": "WED",
    "thursday": "THU",
    "friday": "FRI",
    "saturday": "SAT",
}


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def run_schtasks(args, check=True):
    cmd = ["schtasks"] + args
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def task_exists(name: str) -> bool:
    result = run_schtasks(["/Query", "/TN", name], check=False)
    return result.returncode == 0


def delete_task(name: str) -> None:
    if task_exists(name):
        run_schtasks(["/Delete", "/TN", name, "/F"], check=False)
        print(f"  Removed: {name}")
    else:
        print(f"  Not found (skip): {name}")


def do_uninstall() -> None:
    print("Removing cadence scheduled tasks...")
    for name in TASK_NAMES.values():
        delete_task(name)
    print("Done.")


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_daily_task(name: str, command: str, time_str: str, python_exe: str, cadence_py: str) -> None:
    """Create a daily scheduled task."""
    # Remove existing task first
    if task_exists(name):
        run_schtasks(["/Delete", "/TN", name, "/F"], check=False)

    run_schtasks([
        "/Create",
        "/TN", name,
        "/TR", f'"{python_exe}" "{cadence_py}" {command}',
        "/SC", "DAILY",
        "/ST", time_str,
        "/F",
    ])
    print(f"  Created: {name} (daily at {time_str})")


def create_weekly_task(name: str, command: str, time_str: str, day: str, python_exe: str, cadence_py: str) -> None:
    """Create a weekly scheduled task."""
    if task_exists(name):
        run_schtasks(["/Delete", "/TN", name, "/F"], check=False)

    day_abbr = DAY_MAP.get(day.lower())
    if not day_abbr:
        die(f"Unknown day: {day}")

    run_schtasks([
        "/Create",
        "/TN", name,
        "/TR", f'"{python_exe}" "{cadence_py}" {command}',
        "/SC", "WEEKLY",
        "/D", day_abbr,
        "/ST", time_str,
        "/F",
    ])
    print(f"  Created: {name} (weekly on {day} at {time_str})")


def create_logon_task(name: str, command: str, python_exe: str, cadence_py: str) -> None:
    """Create a task that runs at logon."""
    if task_exists(name):
        run_schtasks(["/Delete", "/TN", name, "/F"], check=False)

    run_schtasks([
        "/Create",
        "/TN", name,
        "/TR", f'"{python_exe}" "{cadence_py}" {command}',
        "/SC", "ONLOGON",
        "/F",
    ])
    print(f"  Created: {name} (on logon)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Install cadence as Windows Scheduled Tasks")
    parser.add_argument("config", nargs="?", default=None, help="Path to config.json")
    parser.add_argument("--uninstall", action="store_true", help="Remove all cadence tasks")
    args = parser.parse_args()

    if args.uninstall:
        do_uninstall()
        return

    # Resolve paths
    script_dir = Path(__file__).resolve().parent
    cadence_py = str(script_dir.parent / "cadence.py")

    if args.config:
        config_path = str(Path(args.config).resolve())
    else:
        config_path = str(script_dir.parent / "config.json")

    if not os.path.isfile(cadence_py):
        die(f"cadence.py not found: {cadence_py}")
    if not os.path.isfile(config_path):
        die(f"Config not found: {config_path}")

    python_exe = sys.executable

    # Read config
    config = load_config(config_path)
    schedule = config.get("schedule", {})

    morning_time = schedule.get("morning_time", "")
    evening_time = schedule.get("evening_time", "")
    weekly_day = schedule.get("weekly_review_day", "")
    weekly_time = schedule.get("weekly_review_time", "")

    if not all([morning_time, evening_time, weekly_day, weekly_time]):
        die("Config is missing required schedule fields (morning_time, evening_time, weekly_review_day, weekly_review_time)")

    print()
    print("=== Cadence Task Scheduler ===")
    print()
    print(f"  cadence.py : {cadence_py}")
    print(f"  config     : {config_path}")
    print(f"  python     : {python_exe}")
    print()
    print(f"  Morning  : daily at {morning_time}")
    print(f"  Evening  : daily at {evening_time}")
    print(f"  Weekly   : {weekly_day} at {weekly_time}")
    print(f"  Listener : runs at logon")
    print()

    confirm = input("Install these tasks? [y/N] ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        return

    create_daily_task(TASK_NAMES["morning"], "morning", morning_time, python_exe, cadence_py)
    create_daily_task(TASK_NAMES["evening"], "evening", evening_time, python_exe, cadence_py)
    create_weekly_task(TASK_NAMES["weekly"], "weekly", weekly_time, weekly_day, python_exe, cadence_py)
    create_logon_task(TASK_NAMES["listener"], "listen", python_exe, cadence_py)

    print()
    print("All tasks installed. Verify with: schtasks /Query /TN \"Cadence*\"")


if __name__ == "__main__":
    main()
