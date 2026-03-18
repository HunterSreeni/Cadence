# {{NAME}} — Project Instructions (Claude Code)

## What This Project Is

Personal productivity and goal tracking system managed with Cadence.
- Goals & priorities: `GOALS.md`
- Active tasks: `CURRENT_TASKS.md`
- Weekly schedule: `WEEKLY_SCHEDULE.md`
- Daily logs: `logs/YYYY-MM-DD.md`

---

## Startup Routine (every session)

1. Read `GOALS.md` — check this week's 3 priorities and report status
2. Read today's log if it exists: `logs/YYYY-MM-DD.md`
3. Read `CURRENT_TASKS.md` for the active task list
4. Brief {{NAME}} on: priority status + where we left off + what's planned today
5. Get confirmation before starting work

---

## End-of-Day Routine

1. Update today's log in `logs/YYYY-MM-DD.md`
2. Update `CURRENT_TASKS.md` — mark done items, add new ones
3. Set tomorrow's priorities at the bottom of today's log

---

## {{NAME}}'s Role (Human)

- Approve any real-world actions (payments, signups, publishing)
- Handle manual steps (OTPs, CAPTCHAs, phone verification)
- Final call on any decision that costs money or time
- Report daily progress for log updates

## Claude's Role

- Content writing, research, drafting
- Update logs, GOALS.md, CURRENT_TASKS.md
- Flag blockers immediately — don't wait
- At every session start: check GOALS.md first, report on weekly priority status
- Never take destructive actions without explicit approval

---

## Folder Map

```
{{PROJECT_DIR}}/
├── CLAUDE.md              ← you are here
├── GOALS.md               ← annual goal + weekly priorities
├── CURRENT_TASKS.md       ← live task list
├── WEEKLY_SCHEDULE.md     ← daily schedule + day types
├── logs/                  ← YYYY-MM-DD.md daily logs
└── config.json            ← cadence configuration
```
