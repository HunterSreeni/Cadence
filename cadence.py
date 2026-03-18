#!/usr/bin/env python3
"""
cadence — Your daily rhythm, tracked.

A Telegram bot + structured markdown system for tracking goals, daily habits,
and progress. Works standalone or supercharged with Claude Code AI.

Usage:
  python3 cadence.py morning     # Send morning briefing
  python3 cadence.py evening     # Send evening check-in
  python3 cadence.py weekly      # Send weekly review
  python3 cadence.py status      # Send instant status
  python3 cadence.py listen      # Long-poll for replies (run as daemon)
  python3 cadence.py test        # Send test message

https://github.com/YOUR_USERNAME/cadence
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, date
from pathlib import Path

# ============================================================
# CONFIG LOADER
# ============================================================
_config = None

def load_config():
    """Load config from config.json (or config.yaml if PyYAML available)."""
    global _config
    if _config is not None:
        return _config

    script_dir = Path(__file__).parent.resolve()

    # Try JSON first (stdlib, no deps)
    json_path = script_dir / "config.json"
    if json_path.exists():
        _config = json.loads(json_path.read_text())
        _config["_base_path"] = script_dir
        return _config

    # Try YAML if available
    yaml_path = script_dir / "config.yaml"
    if yaml_path.exists():
        try:
            import yaml
            _config = yaml.safe_load(yaml_path.read_text())
            _config["_base_path"] = script_dir
            return _config
        except ImportError:
            print("Error: config.yaml found but PyYAML not installed.")
            print("  Install: pip install pyyaml")
            print("  Or rename config.example.json to config.json")
            sys.exit(1)

    print("Error: No config.json or config.yaml found.")
    print("  Run: python3 setup.py")
    sys.exit(1)


def load_env():
    """Load .env file into os.environ (simple key=value parser, no deps)."""
    env_path = Path(__file__).parent.resolve() / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            value = value.strip()
            # Strip surrounding quotes (common .env convention)
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            os.environ.setdefault(key.strip(), value)


def get_bot_token():
    # Support both BOT_TOKEN and TELEGRAM_BOT_TOKEN
    return os.environ.get("BOT_TOKEN", "") or os.environ.get("TELEGRAM_BOT_TOKEN", "")


def get_chat_id():
    cid = load_config().get("telegram", {}).get("chat_id")
    if cid is not None:
        return int(cid)
    return None


def get_base_dir():
    cfg = load_config()
    base = cfg.get("paths", {}).get("base_dir", ".")
    if os.path.isabs(base):
        return Path(base)
    return cfg["_base_path"] / base


def get_logs_dir():
    cfg = load_config()
    logs = cfg.get("paths", {}).get("logs_dir", "./logs")
    if os.path.isabs(logs):
        return Path(logs)
    return cfg["_base_path"] / logs


# ============================================================
# TELEGRAM API
# ============================================================
def send_message(text, parse_mode="HTML"):
    """Send a message via Telegram Bot API."""
    token = get_bot_token()
    chat_id = get_chat_id()
    if not token or not chat_id:
        print(f"[cadence] Message (not sent — no token/chat_id):\n{text}")
        return

    chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        _send_chunk(chunk, parse_mode, token, chat_id)
        if len(chunks) > 1:
            time.sleep(0.5)


def _send_chunk(text, parse_mode, token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }).encode()
    req = urllib.request.Request(url, data=data,
                                headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
    except Exception:
        # Retry without parse mode
        data = json.dumps({"chat_id": chat_id, "text": text}).encode()
        req = urllib.request.Request(url, data=data,
                                    headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req)
        except Exception as e:
            print(f"[cadence] Error sending message: {e}")


def get_updates(offset=None):
    """Get new messages from Telegram."""
    token = get_bot_token()
    url = f"https://api.telegram.org/bot{token}/getUpdates?timeout=30"
    if offset:
        url += f"&offset={offset}"
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=35)
        return json.loads(resp.read())
    except Exception:
        return {"ok": False, "result": []}


# ============================================================
# FILE READERS
# ============================================================
def read_file(path):
    try:
        return Path(path).read_text()
    except FileNotFoundError:
        return ""


def get_day_type():
    """Get today's day type from config schedule."""
    cfg = load_config()
    day_types = cfg.get("schedule", {}).get("day_types", {})
    weekday = str(datetime.now().weekday())
    day_info = day_types.get(weekday, {"type": "rest", "label": "REST", "focus": ""})
    return day_info.get("label", day_info.get("type", "").upper()), day_info.get("focus", "")


def get_day_emoji():
    cfg = load_config()
    day_types = cfg.get("schedule", {}).get("day_types", {})
    day_emojis = cfg.get("schedule", {}).get("day_emojis", {})
    weekday = str(datetime.now().weekday())
    day_info = day_types.get(weekday, {"type": "rest"})
    return day_emojis.get(day_info.get("type", "rest"), "\U0001f4c5")


def get_weekly_priorities():
    """Extract this week's priorities from GOALS.md."""
    content = read_file(get_base_dir() / "GOALS.md")
    priorities = []
    for line in content.split("\n"):
        if "Priority" in line and ("[ ]" in line or "[x]" in line or "[~]" in line):
            status = "done" if "[x]" in line else "pending" if "[ ]" in line else "in progress"
            text = re.sub(r'\*\*Priority \d+:\*\*\s*\[.\]\s*', '', line).strip()
            priorities.append((status, text))
    return priorities


def get_urgent_tasks():
    """Extract urgent tasks from CURRENT_TASKS.md."""
    content = read_file(get_base_dir() / "CURRENT_TASKS.md")
    urgent = []
    in_urgent = False
    for line in content.split("\n"):
        if "URGENT" in line:
            in_urgent = True
            continue
        if in_urgent and line.startswith("- "):
            task = line.strip("- ").strip()
            if task:
                urgent.append(task)
        if in_urgent and line.startswith("##") and "URGENT" not in line:
            in_urgent = False
    return urgent[:5]


def get_custom_metrics():
    """Read custom metrics from config (replaces hardcoded debt/balance tracking)."""
    cfg = load_config()
    goals = cfg.get("goals", {})
    metrics = {}

    if goals.get("income_target"):
        currency = goals.get("income_currency", "$")
        metrics["income_target"] = f"{currency}{goals['income_target']:,}/month"

    if goals.get("debt_total"):
        currency = goals.get("income_currency", "$")
        metrics["debt_total"] = f"{currency}{goals['debt_total']:,}"

    for m in goals.get("custom_metrics", []):
        metrics[m["name"]] = m.get("value", "N/A")

    return metrics


def get_today_log():
    today = date.today().strftime("%Y-%m-%d")
    log_file = get_logs_dir() / f"{today}.md"
    if log_file.exists():
        return read_file(log_file)
    return None


# ============================================================
# MESSAGE BUILDERS
# ============================================================
def build_morning_message():
    cfg = load_config()
    msgs = cfg.get("messages", {})
    today = datetime.now()
    day_name = today.strftime("%A")
    date_str = today.strftime("%d %b %Y")
    day_type, day_focus = get_day_type()
    day_emoji = get_day_emoji()
    priorities = get_weekly_priorities()
    urgent = get_urgent_tasks()
    metrics = get_custom_metrics()
    user_name = cfg.get("user", {}).get("name", "")

    greeting = msgs.get("morning_greeting", "MORNING BRIEFING")
    msg = f"\u2600\ufe0f <b>{greeting} \u2014 {day_name}, {date_str}</b>\n"
    if user_name:
        msg += f"Hi {user_name}!\n"
    msg += f"\n{day_emoji} <b>Day Type: {day_type}</b>\n{day_focus}\n"

    # Custom metrics
    if metrics:
        msg += "\n\U0001f4ca <b>Metrics</b>\n"
        for label, value in metrics.items():
            display_label = label.replace("_", " ").title()
            msg += f"\u2022 {display_label}: {value}\n"

    # Weekly priorities
    msg += "\n\U0001f4cb <b>This Week's Priorities</b>"
    if priorities:
        for i, (status, text) in enumerate(priorities, 1):
            icon = "\u2705" if status == "done" else "\U0001f532" if status == "pending" else "\U0001f504"
            msg += f"\n{i}. {icon} {text}"
    else:
        msg += "\n(No priorities set \u2014 update GOALS.md!)"

    # Urgent tasks
    if urgent:
        msg += "\n\n\U0001f6a8 <b>Urgent</b>"
        for task in urgent[:3]:
            clean = re.sub(r'\*\*', '', task)
            clean = re.sub(r'`[^`]*`', '', clean)[:80]
            msg += f"\n\u2022 {clean}"

    # Daily reminder
    reminder = msgs.get("daily_reminder")
    if reminder:
        msg += f"\n\n\U0001f4dd <b>{reminder}</b>"

    msg += "\n\n<i>Reply with updates anytime. I'll track everything.</i>"
    return msg


def build_evening_message():
    cfg = load_config()
    msgs = cfg.get("messages", {})
    today = datetime.now()
    day_name = today.strftime("%A")
    metrics = get_custom_metrics()

    # Tomorrow info
    from datetime import timedelta
    tomorrow_name = (today + timedelta(days=1)).strftime("%A")
    day_types = cfg.get("schedule", {}).get("day_types", {})
    tomorrow_weekday = str((today.weekday() + 1) % 7)
    tomorrow_info = day_types.get(tomorrow_weekday, {"label": "", "focus": ""})

    greeting = msgs.get("evening_greeting", "END OF DAY")
    msg = f"\U0001f319 <b>{greeting} \u2014 {day_name}</b>\n"

    # Parse today's log for auto-detected progress
    today_log = get_today_log()
    has_data = False
    if today_log:
        sections = _parse_log_sections(today_log)
        for label, emoji, items in sections:
            if items:
                has_data = True
                msg += f"\n{emoji} <b>{label}:</b>\n"
                for item in items[:5]:
                    msg += f"  \u2022 {item[:80]}\n"

    # Metrics
    if metrics:
        msg += "\n\U0001f4ca <b>Metrics:</b> "
        msg += " | ".join(f"{k.replace('_', ' ').title()}: {v}" for k, v in metrics.items())
        msg += "\n"

    if has_data:
        msg += "\n\U0001f446 That's what I have so far."
        msg += "\n<b>Anything to add or correct?</b>"
        msg += '\n\u2022 More spending? (e.g., "spent 200 lunch")'
        msg += "\n\u2022 More work done?"
        msg += "\n\u2022 Or type <b>done</b> if that's everything."
    else:
        msg += "\n\U0001f4dd <b>Nothing tracked today yet!</b>"
        msg += "\n\nReply with:"
        msg += "\n1\ufe0f\u20e3 What you <b>spent</b> today"
        msg += "\n2\ufe0f\u20e3 What you <b>worked on</b>"
        msg += "\n3\ufe0f\u20e3 Any <b>blockers</b>"
        msg += "\n\nOr type <b>skip</b> if nothing to report."

    msg += f"\n\n\U0001f4c5 <b>Tomorrow: {tomorrow_name} \u2014 {tomorrow_info.get('label', '')}</b>"
    if tomorrow_info.get("focus"):
        msg += f"\n{tomorrow_info['focus']}"

    msg += "\n\n<i>Your reply updates the tracker automatically.</i>"
    return msg


def build_weekly_message():
    cfg = load_config()
    msgs = cfg.get("messages", {})
    priorities = get_weekly_priorities()
    metrics = get_custom_metrics()

    greeting = msgs.get("weekly_greeting", "WEEKLY REVIEW")
    msg = f"\U0001f4ca <b>{greeting}</b>\n"

    if metrics:
        for label, value in metrics.items():
            msg += f"\n\u2022 {label.replace('_', ' ').title()}: <b>{value}</b>"
        msg += "\n"

    msg += "\n\U0001f4cb <b>This Week's Priorities</b>"
    if priorities:
        for i, (status, text) in enumerate(priorities, 1):
            icon = "\u2705" if status == "done" else "\u274c"
            msg += f"\n{i}. {icon} {text}"

    msg += "\n\n<b>Reply with:</b>"
    msg += '\n1. Which priorities did you hit? (e.g., "done 1, missed 2 3")'
    msg += "\n2. Next week's 3 priorities"
    msg += "\n3. Any income/progress this week?"
    msg += "\n\n<i>I'll update GOALS.md with your answers.</i>"
    return msg


def build_status_message():
    cfg = load_config()
    priorities = get_weekly_priorities()
    metrics = get_custom_metrics()
    day_type, day_focus = get_day_type()
    now_str = datetime.now().strftime("%d %b %Y %H:%M")
    user_name = cfg.get("user", {}).get("name", "")

    msg = f"\U0001f4ca <b>STATUS \u2014 {now_str}</b>\n"
    if user_name:
        msg += f"User: {user_name}\n"
    msg += f"\U0001f4c5 Today: {day_type} \u2014 {day_focus}\n"

    if metrics:
        for label, value in metrics.items():
            msg += f"\n\u2022 {label.replace('_', ' ').title()}: {value}"
        msg += "\n"

    msg += "\n\U0001f4cb <b>Weekly Priorities</b>"
    for i, (status, text) in enumerate(priorities, 1):
        icon = "\u2705" if status == "done" else "\U0001f532"
        msg += f"\n{i}. {icon} {text}"

    return msg


# ============================================================
# LOG PARSING
# ============================================================
def _parse_log_sections(log_text):
    """Parse a daily log for spending, work, blockers, income."""
    cfg = load_config()
    categories = cfg.get("tracking", {}).get("categories", [])

    results = []
    for cat in categories:
        keyword = cat.get("keyword", "")
        emoji = cat.get("emoji", "\U0001f4dd")
        label = cat.get("label", keyword.title())
        items = []

        for line in log_text.split("\n"):
            line_lower = line.lower()
            if keyword in line_lower:
                clean = re.sub(r'^[-\s]*\[[\d:]+\]\s*', '', line).strip()
                clean = re.sub(rf'^{re.escape(keyword)}:\s*', '', clean, flags=re.IGNORECASE).strip()
                if clean and not clean.startswith('#') and not clean.startswith('>') and len(clean) > 3:
                    items.append(clean)

        if items:
            results.append((label, emoji, items))

    return results


# ============================================================
# REPLY HANDLER
# ============================================================
def handle_reply(text):
    """Parse user reply and update relevant files."""
    cfg = load_config()
    text_lower = text.lower().strip()
    today_str = date.today().strftime("%Y-%m-%d")
    log_file = get_logs_dir() / f"{today_str}.md"
    responses = []

    # Skip command
    if text_lower in ("skip", "busy", "nothing"):
        append_to_log(log_file, "No update reported")
        return "\U0001f44d Logged. No update for today."

    # Status command
    if text_lower in ("status", "/status"):
        return build_status_message()

    # Process tracking categories from config
    categories = cfg.get("tracking", {}).get("categories", [])

    for cat in categories:
        keyword = cat.get("keyword", "")
        pattern = cat.get("pattern")
        emoji = cat.get("emoji", "\U0001f4dd")
        label = cat.get("label", keyword.title())

        if not keyword:
            continue

        # Categories with regex patterns (spending, earnings, done)
        if pattern and keyword in text_lower:
            try:
                matches = re.findall(pattern, text_lower)
            except re.error:
                continue  # skip broken pattern
            if matches:
                if keyword == "spent":
                    total = 0
                    items = []
                    for match in matches:
                        if isinstance(match, tuple) and len(match) >= 2:
                            amt, desc = int(match[0]), match[1].strip()
                            total += amt
                            items.append(f"{amt} {desc}")
                    if items:
                        entry = f"Spending: {', '.join(items)} (total: {total})"
                        append_to_log(log_file, entry)
                        responses.append(f"{emoji} Recorded: {', '.join(items)} = {total}")

                elif keyword == "earned":
                    for match in matches:
                        if isinstance(match, tuple):
                            amt = match[0]
                            source = match[1].strip() if len(match) > 1 and match[1] else "unknown"
                        else:
                            amt, source = match, "unknown"
                        append_to_log(log_file, f"INCOME: {amt} from {source}")
                        responses.append(f"{emoji} INCOME RECORDED: {amt} from {source}!")

                elif keyword == "done":
                    for match in matches:
                        item = match.strip() if isinstance(match, str) else match[0].strip()
                        marked = mark_task_done(item)
                        if marked:
                            responses.append(f"{emoji} Marked done: {marked}")
                        else:
                            responses.append(f"\U0001f4dd Noted: {item} done")
                            append_to_log(log_file, f"Completed: {item}")

        # Categories without patterns — keyword matching (work, blocker)
        elif not pattern:
            if keyword == "worked":
                work_keywords = cfg.get("tracking", {}).get("work_keywords", [])
                if any(wk in text_lower for wk in work_keywords):
                    append_to_log(log_file, f"Work: {text.strip()}")
                    if "work" not in " ".join(responses).lower():
                        responses.append(f"{emoji} Work logged")

            elif keyword == "blocker":
                if keyword in text_lower or "blocked" in text_lower or "stuck" in text_lower:
                    append_to_log(log_file, f"BLOCKER: {text.strip()}")
                    responses.append(f"{emoji} Blocker noted")

    # Process custom fields
    for field in cfg.get("tracking", {}).get("custom_fields", []):
        pattern = field.get("pattern")
        name = field.get("name", "field")
        label = field.get("label", name)
        if pattern:
            try:
                match = re.search(pattern, text_lower)
            except re.error:
                continue
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                append_to_log(log_file, f"{label}: {value}")
                responses.append(f"\U0001f4dd {label} updated: {value}")

    # If nothing matched, log as general note
    if not responses:
        append_to_log(log_file, f"Note: {text.strip()}")
        responses.append("\U0001f4dd Noted in today's log")

    return "\n".join(responses)


# ============================================================
# FILE WRITERS
# ============================================================
def append_to_log(log_file, entry):
    """Append an entry to today's daily log."""
    timestamp = datetime.now().strftime("%H:%M")
    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    if not log_file.exists():
        today_str = date.today().strftime("%Y-%m-%d")
        day_name = datetime.now().strftime("%A")
        day_type, _ = get_day_type()
        content = f"""# Daily Log \u2014 {today_str} ({day_name})
> Day Type: {day_type}
> Auto-generated by cadence

---

## Updates

- [{timestamp}] {entry}
"""
        log_file.write_text(content)
    else:
        # Use append mode to avoid race condition with concurrent writes
        with open(log_file, "a") as f:
            f.write(f"\n- [{timestamp}] {entry}")


def mark_task_done(item):
    """Try to mark a task as done in CURRENT_TASKS.md."""
    tasks_file = get_base_dir() / "CURRENT_TASKS.md"
    content = read_file(tasks_file)
    if not content:
        return None

    lines = content.split("\n")
    item_lower = item.lower().strip()

    for i, line in enumerate(lines):
        if "[ ]" in line or "[~]" in line or "[!]" in line:
            line_lower = line.lower()
            if item_lower in line_lower or any(
                word in line_lower for word in item_lower.split() if len(word) > 3
            ):
                lines[i] = re.sub(r'\[[ ~!]\]', '[x]', line, count=1)
                tasks_file.write_text("\n".join(lines))
                task_name = re.sub(r'^[-*]\s*`?\[.\]`?\s*\*?\*?', '', line).strip()
                task_name = re.sub(r'\*\*', '', task_name)[:60]
                return task_name

    return None


# ============================================================
# LISTENER
# ============================================================
def listen():
    """Long-poll for Telegram replies and handle them."""
    base_dir = get_base_dir()
    pid_file = base_dir / ".bot_listener.pid"
    offset_file = base_dir / ".bot_offset"

    if pid_file.exists():
        old_pid = pid_file.read_text().strip()
        if os.path.exists(f"/proc/{old_pid}"):
            print(f"Listener already running (PID {old_pid}). Exiting.")
            sys.exit(0)
    pid_file.write_text(str(os.getpid()))

    chat_id = get_chat_id()
    print(f"[{datetime.now()}] cadence listener started (PID {os.getpid()}). "
          f"Waiting for messages...")

    offset = None
    if offset_file.exists():
        try:
            offset = int(offset_file.read_text().strip())
        except ValueError:
            offset = None

    while True:
        try:
            updates = get_updates(offset)
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    offset_file.write_text(str(offset))

                    msg_data = update.get("message", {})
                    text = msg_data.get("text", "")
                    from_id = msg_data.get("from", {}).get("id")

                    if from_id != chat_id or not text:
                        continue

                    # Handle commands
                    if text.startswith("/"):
                        cmd = text.lower().strip()
                        if cmd == "/start":
                            send_message(
                                "\U0001f916 cadence is running! "
                                "Send me updates anytime.\n\n"
                                "Commands:\n"
                                "/status \u2014 Current status\n"
                                "/morning \u2014 Morning briefing\n"
                                "/evening \u2014 Evening check-in\n"
                                "/weekly \u2014 Weekly review"
                            )
                        elif cmd == "/status":
                            send_message(build_status_message())
                        elif cmd == "/morning":
                            send_message(build_morning_message())
                        elif cmd == "/evening":
                            send_message(build_evening_message())
                        elif cmd == "/weekly":
                            send_message(build_weekly_message())
                        else:
                            send_message(
                                "Unknown command. Try /status, /morning, "
                                "/evening, or /weekly"
                            )
                        continue

                    # Handle regular replies
                    print(f"[{datetime.now()}] Received: {text[:50]}...")
                    response = handle_reply(text)
                    send_message(response)
                    print(f"[{datetime.now()}] Responded: {response[:50]}...")

        except KeyboardInterrupt:
            print("\nListener stopped.")
            break
        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")
            time.sleep(5)


# ============================================================
# MAIN
# ============================================================
def main():
    load_env()

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "morning":
        send_message(build_morning_message())
        print(f"[{datetime.now()}] Morning briefing sent.")

    elif command == "evening":
        send_message(build_evening_message())
        print(f"[{datetime.now()}] Evening check-in sent.")

    elif command == "weekly":
        send_message(build_weekly_message())
        print(f"[{datetime.now()}] Weekly review sent.")

    elif command == "status":
        send_message(build_status_message())
        print(f"[{datetime.now()}] Status sent.")

    elif command == "listen":
        listen()

    elif command == "test":
        cfg = load_config()
        name = cfg.get("user", {}).get("name", "there")
        send_message(f"\U0001f9ea <b>Test</b> \u2014 cadence is working, {name}!")
        print("Test message sent.")

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
