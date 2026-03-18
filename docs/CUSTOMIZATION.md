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
