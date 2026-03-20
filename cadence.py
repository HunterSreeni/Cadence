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
import importlib.util
from datetime import datetime, date, timedelta
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

    # Account balances (if configured)
    bal_summary = get_balance_summary(cfg)
    if bal_summary:
        msg += "\n\U0001f4b0 <b>Balances</b>\n" + bal_summary + "\n"

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

    # Habits (if enabled)
    habits_summary = get_habits_summary(cfg)
    if habits_summary:
        msg += "\n\n\U0001f3af <b>Habits</b>\n" + habits_summary

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

    bal_summary = get_balance_summary(cfg)
    if bal_summary:
        msg += "\n\U0001f4b0 <b>Balances</b>\n" + bal_summary + "\n"

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
    """Parse user reply and update relevant files.

    Multi-line messages are split and each line processed independently
    to avoid cross-contamination (e.g., spending line triggering work match).
    """
    cfg = load_config()
    text_lower = text.lower().strip()
    today_str = date.today().strftime("%Y-%m-%d")
    log_file = get_logs_dir() / f"{today_str}.md"

    # Skip command
    if text_lower in ("skip", "busy", "nothing"):
        append_to_log(log_file, "No update reported")
        return "\U0001f44d Logged. No update for today."

    # Status command
    if text_lower in ("status", "/status"):
        return build_status_message()

    # Split multi-line messages into individual lines
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]

    # Further split lines with multiple spending entries joined by "and"
    expanded = []
    for line in lines:
        parts = re.split(r'\s+(?:and|&|,)\s+(?=spent\s)', line, flags=re.IGNORECASE)
        expanded.extend(p.strip() for p in parts if p.strip())

    # Process each fragment independently
    all_responses = []
    for line in expanded:
        line_responses = _handle_single_line(cfg, line, log_file)
        all_responses.extend(line_responses)

    if not all_responses:
        append_to_log(log_file, f"Note: {text.strip()}")
        all_responses.append("\U0001f4dd Noted in today's log")

    return "\n".join(all_responses)


def _handle_single_line(cfg, line, log_file):
    """Process a single line of user input. Returns list of response strings."""
    line_lower = line.lower().strip()
    responses = []

    # --- Bank-aware spending ---
    # Supports: "spent 295 from BOB on groceries", "spent 200 groceries from IDFC",
    #           "spent 300 from BOB", "spent 500 food", "Spent - 295 from BOB on groceries"
    amount = None
    account = None
    category = None

    # Get configured account names for matching
    accounts_cfg = cfg.get("accounts", {})
    account_names = "|".join(re.escape(k.lower()) for k in accounts_cfg) if accounts_cfg else ""

    if account_names:
        # Pattern 1: "spent 295 from BOB on/for groceries"
        m = re.match(
            rf'(?:spent\s*[-\u2013]?\s*)(\d+)\s+from\s+({account_names})\s+(?:on|for)\s+(\w[\w\s]*?)$',
            line_lower)
        if m:
            amount, account, category = int(m.group(1)), m.group(2), m.group(3).strip()

        # Pattern 2: "spent 200 groceries from IDFC"
        if amount is None:
            m = re.match(
                rf'(?:spent\s*[-\u2013]?\s*)(\d+)\s+(\w[\w\s]*?)\s+from\s+({account_names})\s*$',
                line_lower)
            if m:
                amount, category, account = int(m.group(1)), m.group(2).strip(), m.group(3)

        # Pattern 3: "spent 295 from BOB" (no category)
        if amount is None:
            m = re.match(
                rf'(?:spent\s*[-\u2013]?\s*)(\d+)\s+from\s+({account_names})\s*$',
                line_lower)
            if m:
                amount, account, category = int(m.group(1)), m.group(2), "unspecified"

    # Pattern 4: "spent 500 food" (no account — always available)
    if amount is None:
        m = re.match(r'(?:spent\s*[-\u2013]?\s*)(\d+)\s+(\w[\w\s]*?)$', line_lower)
        if m:
            amount, category = int(m.group(1)), m.group(2).strip()

    if amount is not None:
        log_entry = f"Spending: {amount} on {category}"
        if account:
            log_entry += f" (from {account.upper()})"
        append_to_log(log_file, log_entry)

        response = f"\U0001f4b8 Recorded: {amount} {category}"

        # Auto-deduct from account balance if specified
        if account and accounts_cfg:
            new_bal = _deduct_balance(cfg, account, amount)
            if new_bal is not None:
                response += f"\n\U0001f3e6 {account.upper()} balance \u2192 {new_bal:,.0f}"

        responses.append(response)
        return responses  # Don't process spending lines as work

    # --- Earnings ---
    earn_match = re.match(
        r'earned?\s+\$?\u20b9?(\d+)\s*(?:usd|inr|dollars?)?\s*(\w+)?',
        line_lower)
    if earn_match:
        amt = earn_match.group(1)
        source = earn_match.group(2).strip() if earn_match.group(2) else "unknown"
        append_to_log(log_file, f"INCOME: {amt} from {source}")
        responses.append(f"\U0001f4b0 INCOME RECORDED: {amt} from {source}!")
        return responses

    # --- Task completion ---
    done_match = re.match(r'done\s+(.+?)$', line_lower)
    if done_match:
        item = done_match.group(1).strip()
        marked = mark_task_done(item)
        if marked:
            responses.append(f"\u2705 Marked done: {marked}")
        else:
            responses.append(f"\U0001f4dd Noted: {item} done")
            append_to_log(log_file, f"Completed: {item}")
        return responses

    # --- Balance update: "bob 1430 idfc 2101" ---
    if accounts_cfg and len(accounts_cfg) >= 2:
        acct_keys = list(accounts_cfg.keys())
        bal_pattern = rf'{re.escape(acct_keys[0].lower())}\s+(\d+[\d,.]*)\s*(?:{re.escape(acct_keys[1].lower())}|,)\s*(\d+[\d,.]*)'
        bal_match = re.search(bal_pattern, line_lower)
        if bal_match:
            _set_balance(cfg, acct_keys[0], bal_match.group(1))
            _set_balance(cfg, acct_keys[1], bal_match.group(2))
            balances = _load_balances(cfg)
            parts = [f"{k}: {v:,.0f}" for k, v in balances.items()]
            total = sum(balances.values())
            responses.append(f"\U0001f3e6 Balances updated! {' | '.join(parts)} | Total: {total:,.0f}")
            append_to_log(log_file, f"Balance update: {', '.join(parts)}")
            return responses

    # --- Keyword-only categories (work, blocker, tested, etc.) ---
    categories = cfg.get("tracking", {}).get("categories", [])
    for cat in categories:
        keyword = cat.get("keyword", "")
        pattern = cat.get("pattern")
        emoji = cat.get("emoji", "\U0001f4dd")
        label = cat.get("label", keyword.title())

        if not keyword or pattern:
            continue  # skip pattern-based categories (handled above)

        if keyword == "worked":
            work_keywords = cfg.get("tracking", {}).get("work_keywords", [])
            if any(wk in line_lower for wk in work_keywords):
                append_to_log(log_file, f"Work: {line.strip()}")
                responses.append(f"{emoji} Work logged: {line.strip()[:60]}")
                return responses

        elif keyword == "blocker":
            if keyword in line_lower or "blocked" in line_lower or "stuck" in line_lower:
                append_to_log(log_file, f"BLOCKER: {line.strip()}")
                responses.append(f"{emoji} Blocker noted")
                return responses

        elif keyword in line_lower:
            append_to_log(log_file, f"{label}: {line.strip()}")
            responses.append(f"{emoji} {label} logged")
            return responses

    # --- Habits module ---
    habit_resp = _handle_habit_line(cfg, line, log_file)
    if habit_resp:
        return habit_resp

    # --- Health module ---
    health_resp = _handle_health_line(cfg, line, log_file)
    if health_resp:
        return health_resp

    # --- Custom fields ---
    for field in cfg.get("tracking", {}).get("custom_fields", []):
        pattern = field.get("pattern")
        name = field.get("name", "field")
        label = field.get("label", name)
        if pattern:
            try:
                match = re.search(pattern, line_lower)
            except re.error:
                continue
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                append_to_log(log_file, f"{label}: {value}")
                responses.append(f"\U0001f4dd {label} updated: {value}")
                return responses

    return responses


# ============================================================
# BALANCE TRACKING
# ============================================================
def _load_balances(cfg):
    """Load balances from balances.json, seeding from config if needed."""
    base_dir = cfg.get("_base_path", Path(__file__).parent.resolve())
    bal_file = base_dir / "balances.json"
    accounts_cfg = cfg.get("accounts", {})

    if bal_file.exists():
        try:
            return json.loads(bal_file.read_text())
        except (json.JSONDecodeError, ValueError):
            pass

    # Seed from config
    balances = {}
    for name, info in accounts_cfg.items():
        if isinstance(info, dict):
            balances[name.upper()] = info.get("initial_balance", 0)
        else:
            balances[name.upper()] = float(info)
    if balances:
        _save_balances(cfg, balances)
    return balances


def _save_balances(cfg, balances):
    """Write balances to balances.json."""
    base_dir = cfg.get("_base_path", Path(__file__).parent.resolve())
    bal_file = base_dir / "balances.json"
    bal_file.write_text(json.dumps(balances, indent=2) + "\n")


def _deduct_balance(cfg, account_name, amount):
    """Deduct amount from an account. Returns new balance or None."""
    balances = _load_balances(cfg)
    key = account_name.upper()
    if key not in balances:
        # Try case-insensitive match
        for k in balances:
            if k.lower() == account_name.lower():
                key = k
                break
        else:
            return None
    balances[key] = balances.get(key, 0) - amount
    _save_balances(cfg, balances)
    return balances[key]


def _set_balance(cfg, account_name, amount_str):
    """Set an account balance explicitly."""
    balances = _load_balances(cfg)
    key = account_name.upper()
    try:
        balances[key] = float(amount_str.replace(",", ""))
    except (ValueError, TypeError):
        return
    _save_balances(cfg, balances)


def get_balance_summary(cfg=None):
    """Get a formatted balance summary for messages."""
    if cfg is None:
        cfg = load_config()
    accounts_cfg = cfg.get("accounts", {})
    if not accounts_cfg:
        return ""
    balances = _load_balances(cfg)
    if not balances:
        return ""
    parts = []
    total = 0
    for name, bal in balances.items():
        parts.append(f"\u2022 {name}: {bal:,.0f}")
        total += bal
    parts.append(f"\u2022 Total: {total:,.0f}")
    return "\n".join(parts)


# ============================================================
# HABITS MODULE
# ============================================================
def _load_habits(cfg):
    """Load habit streak data from habits.json."""
    base_dir = cfg.get("_base_path", Path(__file__).parent.resolve())
    hab_file = base_dir / "habits.json"
    if hab_file.exists():
        try:
            return json.loads(hab_file.read_text())
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


def _save_habits(cfg, data):
    """Write habit data to habits.json."""
    base_dir = cfg.get("_base_path", Path(__file__).parent.resolve())
    hab_file = base_dir / "habits.json"
    hab_file.write_text(json.dumps(data, indent=2) + "\n")


def _record_habit(cfg, habit_name):
    """Record a habit completion for today. Returns (streak, is_new_best)."""
    data = _load_habits(cfg)
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    if habit_name not in data:
        data[habit_name] = {"streak": 0, "best": 0, "last_date": ""}

    h = data[habit_name]
    if h["last_date"] == today:
        return h["streak"], False  # Already recorded today

    if h["last_date"] == yesterday:
        h["streak"] += 1
    else:
        h["streak"] = 1

    h["last_date"] = today
    is_new_best = h["streak"] > h["best"]
    if is_new_best:
        h["best"] = h["streak"]

    _save_habits(cfg, data)
    return h["streak"], is_new_best


def get_habits_summary(cfg=None):
    """Get a formatted habits summary for messages."""
    if cfg is None:
        cfg = load_config()
    modules = cfg.get("modules", {})
    habits_mod = modules.get("habits", {})
    if not habits_mod.get("enabled"):
        return ""
    habit_list = habits_mod.get("habits", [])
    if not habit_list:
        return ""
    data = _load_habits(cfg)
    today = date.today().isoformat()
    parts = []
    for h in habit_list:
        info = data.get(h, {"streak": 0, "best": 0, "last_date": ""})
        done = "\u2705" if info.get("last_date") == today else "\u2b1c"
        streak = info.get("streak", 0)
        best = info.get("best", 0)
        parts.append(f"{done} {h} (streak: {streak}, best: {best})")
    return "\n".join(parts)


def _handle_habit_line(cfg, line, log_file):
    """Handle habit tracking. Returns response list or empty."""
    modules = cfg.get("modules", {})
    habits_mod = modules.get("habits", {})
    if not habits_mod.get("enabled"):
        return []
    habit_list = [h.lower() for h in habits_mod.get("habits", [])]
    original_list = habits_mod.get("habits", [])
    line_lower = line.lower().strip()

    # Match "did exercise" or "exercise done" or just "exercise"
    for i, h in enumerate(habit_list):
        if h in line_lower:
            streak, is_best = _record_habit(cfg, original_list[i])
            append_to_log(log_file, f"Habit: {original_list[i]} (streak: {streak})")
            resp = f"\u2705 {original_list[i]} logged! Streak: {streak}"
            if is_best:
                resp += " \U0001f525 New best!"
            return [resp]
    return []


def _handle_health_line(cfg, line, log_file):
    """Handle health tracking. Returns response list or empty."""
    modules = cfg.get("modules", {})
    health_mod = modules.get("health", {})
    if not health_mod.get("enabled"):
        return []
    fields = health_mod.get("fields", [])
    line_lower = line.lower().strip()
    responses = []

    for field in fields:
        m = re.search(rf'{re.escape(field.lower())}\s+(\d+[\d.]*)', line_lower)
        if m:
            value = m.group(1)
            append_to_log(log_file, f"Health: {field} = {value}")
            responses.append(f"\U0001f3cb {field}: {value}")
    return responses


# ============================================================
# PLUGIN SYSTEM
# ============================================================
def _load_plugins():
    """Load command plugins from commands/ directory."""
    commands_dir = Path(__file__).parent.resolve() / "commands"
    if not commands_dir.exists():
        return {}
    plugins = {}
    for f in commands_dir.glob("*.py"):
        if f.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(f.stem, f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "register"):
                plugins.update(mod.register())
        except Exception as e:
            print(f"[cadence] Plugin {f.name} failed to load: {e}")
    return plugins


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
# HELPERS
# ============================================================
def _is_pid_running(pid):
    """Check if a process is running (cross-platform)."""
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, OverflowError):
        return False


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
        if _is_pid_running(old_pid):
            print(f"Listener already running (PID {old_pid}). Exiting.")
            sys.exit(0)
    pid_file.write_text(str(os.getpid()))

    chat_id = get_chat_id()
    plugins = _load_plugins()
    if plugins:
        print(f"[{datetime.now()}] Loaded plugins: {', '.join(plugins.keys())}")
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
                        elif cmd in plugins:
                            try:
                                cfg = load_config()
                                result = plugins[cmd](text, cfg)
                                if result:
                                    send_message(result)
                            except Exception as e:
                                send_message(f"Plugin error: {e}")
                        else:
                            plugin_cmds = "\n".join(
                                f"{c}" for c in plugins) if plugins else ""
                            extra = f"\n\n<b>Plugins:</b>\n{plugin_cmds}" if plugin_cmds else ""
                            send_message(
                                "Unknown command. Try /status, /morning, "
                                "/evening, or /weekly" + extra
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
