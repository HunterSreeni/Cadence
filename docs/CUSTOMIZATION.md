# Customization Guide

## Adding Custom Tracking Categories

Edit `config.json` → `tracking.categories` to add new reply types:

```json
{
  "keyword": "exercise",
  "pattern": "exercise\\s+(\\d+)\\s*min",
  "emoji": "\ud83c\udfcb\ufe0f",
  "label": "Exercise"
}
```

Now typing `exercise 30 min` in Telegram gets parsed and logged.

## Adding Custom Fields

For tracking specific values (bank balances, metrics, etc.):

```json
"custom_fields": [
  {
    "name": "savings",
    "pattern": "savings\\s+(\\d[\\d,.]*)",
    "label": "Savings Balance"
  },
  {
    "name": "weight",
    "pattern": "weight\\s+(\\d+\\.?\\d*)",
    "label": "Weight (kg)"
  }
]
```

## Changing Day Types

Edit `config.json` → `schedule.day_types`. Each day (0=Monday through 6=Sunday):

```json
"day_types": {
  "0": { "type": "focus",  "label": "FOCUS DAY",  "focus": "Deep work, no meetings" },
  "1": { "type": "collab", "label": "COLLAB DAY", "focus": "Pair programming + reviews" },
  ...
}
```

Add matching emojis in `schedule.day_emojis`:

```json
"day_emojis": {
  "focus": "\ud83c\udfaf",
  "collab": "\ud83e\udd1d"
}
```

## Custom Daily Reminder

Set in `config.json` → `messages.daily_reminder`:

```json
"daily_reminder": "Ship one thing today."
```

Set to `null` to disable.

## Changing Schedule Times

Edit `config.json` → `schedule`:

```json
"morning_time": "07:30",
"evening_time": "22:00",
"weekly_review_day": "friday",
"weekly_review_time": "17:00"
```

Then re-run the scheduler installer:
```bash
python3 setup.py install-scheduler
```

## Custom Metrics in Briefings

Add to `config.json` → `goals.custom_metrics`:

```json
"custom_metrics": [
  { "name": "github_prs", "value": "3 this week" },
  { "name": "streak", "value": "12 days" }
]
```

These show up in morning briefings and status messages.

## Editing Templates

The generated markdown files (GOALS.md, CURRENT_TASKS.md, etc.) are yours to edit freely. cadence only reads specific patterns:

- `**Priority N:** [status]` lines in GOALS.md
- `URGENT` section heading in CURRENT_TASKS.md
- `[ ]`, `[x]`, `[~]`, `[!]` status markers

Everything else is freeform — add whatever sections you want.

---

## Bank-Aware Spending

Track spending per account with auto-deducting balances.

### 1. Configure accounts in `config.json`:

```json
"accounts": {
  "SAVINGS": { "initial_balance": 50000 },
  "CHECKING": { "initial_balance": 12000 }
}
```

### 2. Send spending with account name:

```
spent 500 from SAVINGS on rent
spent 200 groceries from CHECKING
spent 300 from SAVINGS
```

The bot deducts from the account and reports the new balance. Balances are stored in `balances.json` (auto-created).

### 3. Set balances explicitly:

```
savings 45000 checking 11000
```

### 4. View balances:

Balances appear in morning briefings and `/status` automatically when accounts are configured.

---

## Tracking Modules

Enable optional modules in `config.json` → `modules`:

### Habits Module

```json
"modules": {
  "habits": {
    "enabled": true,
    "habits": ["exercise", "reading", "meditation", "journaling"]
  }
}
```

**Usage:** Just type the habit name in Telegram:
- `exercise` → "Exercise logged! Streak: 5"
- `reading` → "Reading logged! Streak: 12 🔥 New best!"

Streaks are tracked in `habits.json`. Morning briefings show today's habit status.

### Health Module

```json
"modules": {
  "health": {
    "enabled": true,
    "fields": ["weight", "food", "exercise_min", "water_l"]
  }
}
```

**Usage:** Type the field name followed by a number:
- `weight 72.5` → "weight: 72.5"
- `exercise_min 45` → "exercise_min: 45"

---

## Multi-Line Messages

cadence splits multi-line Telegram messages and processes each line independently. This prevents cross-contamination:

```
spent 200 from SAVINGS on food
submitted PR for review
blocker: CI is broken
```

Each line gets its own response — spending doesn't trigger a work match.

Multiple spending in one line also works:

```
spent 200 from SAVINGS on food and spent 50 from CHECKING on coffee
```

---

## Plugin System

Add custom `/commands` without modifying cadence.py.

### 1. Create a file in `commands/`:

```python
# commands/mycommand.py
def register():
    return {"/mycommand": handle}

def handle(text, config):
    return "Hello from my custom command!"
```

### 2. Restart the listener

The bot auto-discovers plugins at startup and adds them to the command list.

### Handler signature:

```python
def handle(text: str, config: dict) -> str
```

- `text` — the full message text (e.g., "/mycommand arg1 arg2")
- `config` — the loaded config.json dict
- Return a string to send as a Telegram message

See `commands/example.py` for a working reference.
