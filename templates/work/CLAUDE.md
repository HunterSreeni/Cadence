# {{NAME}} — Work Project Instructions (Claude Code)

## Project Context

Work project managed with Cadence. Sprint-based workflow.
- Sprint goals & OKRs: `GOALS.md`
- Sprint tasks: `CURRENT_TASKS.md`
- Schedule: `WEEKLY_SCHEDULE.md`
- Daily logs: `logs/YYYY-MM-DD.md`

---

## Startup Routine (every session)

1. Read `GOALS.md` — check sprint goal and current priorities
2. Read `CURRENT_TASKS.md` — what's in progress, what's blocked
3. Read today's log if it exists: `logs/YYYY-MM-DD.md`
4. Brief {{NAME}} on: sprint status + blockers + today's plan
5. Get confirmation before starting work

---

## End-of-Day Routine

1. Update today's log in `logs/YYYY-MM-DD.md`
2. Update `CURRENT_TASKS.md` — move items between sections
3. Note any blockers that need attention tomorrow

---

## What Claude Should Do

- Write code, tests, documentation
- Research solutions and present options
- Update logs and task tracking files
- Flag blockers and risks immediately
- Keep sprint goals visible — don't let scope creep in

## What Claude Should NOT Do

- Push to production or deploy without explicit approval
- Make architectural decisions unilaterally — present options, let the human decide
- Commit directly to main/master without review
- Skip tests to move faster
- Add scope beyond what's in the sprint backlog

---

## Folder Map

```
{{PROJECT_DIR}}/
├── CLAUDE.md              ← you are here
├── GOALS.md               ← sprint goals + OKRs
├── CURRENT_TASKS.md       ← sprint task board
├── WEEKLY_SCHEDULE.md     ← meeting + focus schedule
├── logs/                  ← YYYY-MM-DD.md daily logs
└── config.json            ← cadence configuration
```
