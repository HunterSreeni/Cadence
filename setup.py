#!/usr/bin/env python3
"""
Cadence — Interactive Setup Wizard
Generates your personal productivity system from templates.
stdlib only. No third-party dependencies.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"
DEFAULT_OUTPUT_DIR = Path.cwd()

HEADER = r"""
   ___          _
  / __\__ _  __| | ___ _ __   ___ ___
 / /  / _` |/ _` |/ _ \ '_ \ / __/ _ \
/ /__| (_| | (_| |  __/ | | | (_|  __/
\____/\__,_|\__,_|\___|_| |_|\___\___|

        Setup Wizard v1.0
"""

MODES = {
    "personal": "Personal goals, side projects, life tracking",
    "work": "Sprint-based work, team projects, OKRs",
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ask(prompt: str, default: str = "") -> str:
    """Prompt user for input with an optional default."""
    suffix = f" [{default}]" if default else ""
    answer = input(f"  {prompt}{suffix}: ").strip()
    return answer if answer else default


def ask_yes(prompt: str, default: bool = True) -> bool:
    """Yes/no prompt."""
    hint = "Y/n" if default else "y/N"
    answer = input(f"  {prompt} [{hint}]: ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def ask_choice(prompt: str, options: dict, default: str = "") -> str:
    """Let user pick from numbered options."""
    keys = list(options.keys())
    print()
    for i, key in enumerate(keys, 1):
        marker = " (default)" if key == default else ""
        print(f"    {i}. {key} — {options[key]}{marker}")
    print()
    while True:
        answer = input(f"  {prompt} [1-{len(keys)}]: ").strip()
        if not answer and default:
            return default
        try:
            idx = int(answer) - 1
            if 0 <= idx < len(keys):
                return keys[idx]
        except (ValueError, IndexError):
            pass
        print(f"    Please enter a number between 1 and {len(keys)}.")


def render_template(template_path: Path, replacements: dict) -> str:
    """Read a template file and replace {{PLACEHOLDERS}}."""
    content = template_path.read_text()
    for key, value in replacements.items():
        content = content.replace("{{" + key + "}}", str(value))
    return content


def section(title: str):
    """Print a section header."""
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


# ---------------------------------------------------------------------------
# Setup Steps
# ---------------------------------------------------------------------------

def step_mode() -> str:
    section("Step 1: Mode")
    print("  How will you use Cadence?")
    return ask_choice("Pick a mode", MODES, default="personal")


def step_identity(mode: str) -> dict:
    section("Step 2: Identity")
    name = ask("Your name (or alias)", "User")
    year = ask("Year", str(datetime.now().year))

    if mode == "personal":
        primary_goal = ask("Your #1 goal this year", "Ship something meaningful")
        review_day = ask("Weekly review day", "Sunday")
        income_target = ask("Monthly income target (leave blank to skip)", "")
        debt_total = ask("Total debt (leave blank to skip)", "")
        return {
            "NAME": name,
            "YEAR": year,
            "PRIMARY_GOAL": primary_goal,
            "REVIEW_DAY": review_day,
            "INCOME_TARGET": income_target if income_target else "N/A",
            "DEBT_TOTAL": debt_total if debt_total else "N/A",
            "WEEK_START": "___",
        }
    else:
        primary_goal = ask("Current sprint goal", "Deliver the MVP")
        sprint_name = ask("Sprint name", "Sprint 1")
        sprint_start = ask("Sprint start date", datetime.now().strftime("%Y-%m-%d"))
        sprint_end = ask("Sprint end date", "")
        standup_time = ask("Daily standup time", "9:30 AM")
        return {
            "NAME": name,
            "YEAR": year,
            "PRIMARY_GOAL": primary_goal,
            "SPRINT_NAME": sprint_name,
            "SPRINT_START": sprint_start,
            "SPRINT_END": sprint_end if sprint_end else "TBD",
            "STANDUP_TIME": standup_time,
        }


def step_telegram() -> dict:
    section("Step 3: Notifications (Telegram)")
    print("  Cadence can send you reminders via Telegram bot.")
    print("  You can set this up later if you prefer.\n")
    use_telegram = ask_yes("Set up Telegram notifications?", default=False)
    if use_telegram:
        bot_token = ask("Telegram Bot Token (from @BotFather)", "")
        chat_id = ask("Your Telegram Chat ID", "")
        return {"bot_token": bot_token, "chat_id": chat_id}
    return {}


def step_schedule(mode: str, replacements: dict) -> dict:
    section("Step 4: Schedule")
    if mode == "personal":
        review_day = replacements.get("REVIEW_DAY", "Sunday")
        print(f"  Review day: {review_day}")
        morning = ask("Morning check-in time (HH:MM, 24h)", "09:00")
        evening = ask("Evening check-in time (HH:MM, 24h)", "21:45")
        weekly_time = ask("Weekly review time (HH:MM, 24h)", "19:00")
        return {
            "morning_time": morning,
            "evening_time": evening,
            "weekly_review_day": review_day.lower(),
            "weekly_review_time": weekly_time,
        }
    else:
        standup = replacements.get("STANDUP_TIME", "9:30 AM")
        print(f"  Standup: {standup}")
        eod = ask("End-of-day log time (HH:MM, 24h)", "17:30")
        review_day = ask("Weekly review day", "Friday")
        weekly_time = ask("Weekly review time (HH:MM, 24h)", "17:00")
        return {
            "morning_time": standup,
            "evening_time": eod,
            "weekly_review_day": review_day.lower(),
            "weekly_review_time": weekly_time,
        }


def step_goals(mode: str, replacements: dict):
    section("Step 5: Goals")
    if mode == "personal":
        print(f"  Primary goal: {replacements['PRIMARY_GOAL']}")
        print(f"  Review day: {replacements['REVIEW_DAY']}")
    else:
        print(f"  Sprint goal: {replacements['PRIMARY_GOAL']}")
        print(f"  Sprint: {replacements.get('SPRINT_NAME', 'Sprint 1')}")

    print("\n  You can define your 3 weekly priorities now or later in GOALS.md.")
    define_now = ask_yes("Define priorities now?", default=False)
    priorities = []
    if define_now:
        for i in range(1, 4):
            p = ask(f"Priority {i}", f"Priority {i} — define later")
            priorities.append(p)
    return priorities


def step_claude(mode: str) -> bool:
    section("Step 6: Claude Code Integration")
    print("  Cadence can generate a CLAUDE.md file so Claude Code")
    print("  knows how to work with your project automatically.")
    return ask_yes("Generate CLAUDE.md for this project?", default=True)


# ---------------------------------------------------------------------------
# File Generation
# ---------------------------------------------------------------------------

def generate_files(
    output_dir: Path,
    mode: str,
    replacements: dict,
    schedule_config: dict,
    telegram_config: dict,
    priorities: list,
    enable_claude: bool,
):
    """Generate all output files from templates."""
    template_dir = TEMPLATES_DIR / mode
    output_dir.mkdir(parents=True, exist_ok=True)

    # Add PROJECT_DIR to replacements
    replacements["PROJECT_DIR"] = str(output_dir)

    # --- config.json ---
    config = {
        "mode": mode,
        "name": replacements["NAME"],
        "year": replacements["YEAR"],
        "primary_goal": replacements["PRIMARY_GOAL"],
        "schedule": schedule_config,
        "telegram": {"chat_id": telegram_config.get("chat_id")},
        "claude_enabled": enable_claude,
        "created": datetime.now().isoformat(),
    }
    if mode == "personal":
        config["review_day"] = replacements.get("REVIEW_DAY", "Sunday")
        if replacements.get("INCOME_TARGET") and replacements["INCOME_TARGET"] != "N/A":
            config["income_target"] = replacements["INCOME_TARGET"]
        if replacements.get("DEBT_TOTAL") and replacements["DEBT_TOTAL"] != "N/A":
            config["debt_total"] = replacements["DEBT_TOTAL"]
    else:
        config["sprint"] = {
            "name": replacements.get("SPRINT_NAME", "Sprint 1"),
            "start": replacements.get("SPRINT_START", ""),
            "end": replacements.get("SPRINT_END", "TBD"),
        }

    config_path = output_dir / "config.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    print(f"  [+] config.json")

    # --- .env ---
    env_lines = [
        "# Cadence environment variables",
        f"# Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]
    if telegram_config.get("bot_token"):
        env_lines.append(f"BOT_TOKEN={telegram_config['bot_token']}")
    else:
        env_lines.append("# BOT_TOKEN=your_bot_token_here")

    env_path = output_dir / ".env"
    env_path.write_text("\n".join(env_lines) + "\n")
    print(f"  [+] .env")

    # --- GOALS.md ---
    goals_content = render_template(template_dir / "GOALS.md", replacements)

    # Strip income/debt lines if not set
    if mode == "personal":
        if replacements.get("INCOME_TARGET") == "N/A":
            goals_content = "\n".join(
                line for line in goals_content.split("\n")
                if "INCOME_TARGET" not in line and "Income target" not in line
                or replacements.get("INCOME_TARGET") not in ("N/A",)
            )
            # Simpler approach: just remove lines containing N/A for these fields
            lines = goals_content.split("\n")
            lines = [l for l in lines if not ("income target" in l.lower() and "N/A" in l)]
            lines = [l for l in lines if not ("debt total" in l.lower() and "N/A" in l)]
            # Remove the HTML comment if both are gone
            lines = [l for l in lines if "Remove these lines if not applicable" not in l]
            goals_content = "\n".join(lines)

    # Inject priorities if user defined them
    if priorities:
        for i, p in enumerate(priorities):
            goals_content = goals_content.replace(
                f"_Define your {'first' if i == 0 else 'second' if i == 1 else 'third'} priority_",
                p,
            )

    goals_path = output_dir / "GOALS.md"
    goals_path.write_text(goals_content)
    print(f"  [+] GOALS.md")

    # --- CURRENT_TASKS.md ---
    tasks_content = render_template(template_dir / "CURRENT_TASKS.md", replacements)
    tasks_path = output_dir / "CURRENT_TASKS.md"
    tasks_path.write_text(tasks_content)
    print(f"  [+] CURRENT_TASKS.md")

    # --- WEEKLY_SCHEDULE.md ---
    schedule_content = render_template(template_dir / "WEEKLY_SCHEDULE.md", replacements)
    schedule_path = output_dir / "WEEKLY_SCHEDULE.md"
    schedule_path.write_text(schedule_content)
    print(f"  [+] WEEKLY_SCHEDULE.md")

    # --- logs/ directory ---
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    gitkeep = logs_dir / ".gitkeep"
    gitkeep.touch()
    print(f"  [+] logs/")

    # --- CLAUDE.md (optional) ---
    if enable_claude:
        claude_content = render_template(template_dir / "CLAUDE.md", replacements)
        claude_path = output_dir / "CLAUDE.md"
        claude_path.write_text(claude_content)
        print(f"  [+] CLAUDE.md")


# ---------------------------------------------------------------------------
# Scheduler Installer
# ---------------------------------------------------------------------------

def install_scheduler():
    """Detect OS and install the appropriate scheduler."""
    section("Installing Scheduler")

    system = platform.system().lower()
    print(f"  Detected OS: {platform.system()} ({platform.machine()})")

    schedulers_dir = SCRIPT_DIR / "schedulers"

    if system == "linux":
        # Check for systemd
        has_systemd = shutil.which("systemctl") is not None
        if has_systemd:
            installer = schedulers_dir / "install_systemd.sh"
            if installer.exists():
                print("  Using systemd scheduler...")
                subprocess.run(["bash", str(installer)], check=True)
            else:
                print(f"  Scheduler installer not found: {installer}")
                print("  You can set up cron jobs manually. See docs/.")
        else:
            # Fallback to cron
            installer = schedulers_dir / "install_cron.sh"
            if installer.exists():
                print("  Using cron scheduler...")
                subprocess.run(["bash", str(installer)], check=True)
            else:
                print(f"  Scheduler installer not found: {installer}")
                print("  Set up cron manually:")
                print("    crontab -e")
                print("    # Add your cadence check-in times")

    elif system == "darwin":
        installer = schedulers_dir / "install_launchd.sh"
        if installer.exists():
            print("  Using launchd scheduler...")
            subprocess.run(["bash", str(installer)], check=True)
        else:
            print(f"  Scheduler installer not found: {installer}")
            print("  You can set up launchd plist manually. See docs/.")

    elif system == "windows":
        installer = schedulers_dir / "install-windows.ps1"
        if installer.exists():
            print("  Using Windows Task Scheduler...")
            subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(installer)],
                check=True,
            )
        else:
            print(f"  Scheduler installer not found: {installer}")
            print("  You can set up Task Scheduler manually. See docs/.")
    else:
        print(f"  Unsupported OS: {system}")
        print("  Set up scheduled tasks manually for your platform.")

    print("\n  Done. Scheduler installed.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Handle subcommands
    if len(sys.argv) > 1:
        if sys.argv[1] == "install-scheduler":
            install_scheduler()
            return
        elif sys.argv[1] in ("-h", "--help"):
            print("Usage:")
            print("  python setup.py                  Run interactive setup wizard")
            print("  python setup.py install-scheduler Install OS-specific scheduler")
            return
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python setup.py [install-scheduler]")
            sys.exit(1)

    # --- Wizard ---
    print(HEADER)
    print("  Let's set up your productivity system.")
    print("  Press Enter to accept defaults (shown in brackets).\n")

    # Step 1: Mode
    mode = step_mode()

    # Step 2: Identity
    replacements = step_identity(mode)

    # Step 3: Telegram
    telegram_config = step_telegram()

    # Step 4: Schedule
    schedule_config = step_schedule(mode, replacements)

    # Step 5: Goals
    priorities = step_goals(mode, replacements)

    # Step 6: Claude Code
    enable_claude = step_claude(mode)

    # --- Output ---
    section("Generating Files")

    output_dir = Path(ask("Output directory", str(DEFAULT_OUTPUT_DIR)))
    output_dir = output_dir.resolve()

    print(f"\n  Writing to: {output_dir}\n")

    generate_files(
        output_dir=output_dir,
        mode=mode,
        replacements=replacements,
        schedule_config=schedule_config,
        telegram_config=telegram_config,
        priorities=priorities,
        enable_claude=enable_claude,
    )

    # --- Next Steps ---
    section("Setup Complete!")
    print(f"""
  Your Cadence system is ready at:
    {output_dir}

  Next steps:
    1. Open GOALS.md and set your 3 priorities for this week
    2. Customize WEEKLY_SCHEDULE.md to match your real schedule
    3. Start your first daily log:
         logs/{datetime.now().strftime('%Y-%m-%d')}.md
""")

    if enable_claude:
        print("    4. CLAUDE.md is ready — Claude Code will pick it up automatically")
        print("       when you open this folder as a project.\n")

    if not telegram_config.get("bot_token"):
        print("    Telegram not configured. To add later:")
        print("      - Edit .env with your bot token and chat ID")
        print("      - Run: python setup.py install-scheduler\n")
    else:
        print("    To install scheduled reminders:")
        print("      python setup.py install-scheduler\n")

    print("  Happy building.\n")


if __name__ == "__main__":
    main()
