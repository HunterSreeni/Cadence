# Architecture

## Overview

cadence has three independent components that share state through markdown files:

```
┌──────────────┐     ┌────────────────┐     ┌──────────────────┐
│   Telegram    │◄───►│   cadence.py   │◄───►│  Markdown Files  │
│   (You)       │     │   (Bot)        │     │  GOALS.md        │
└──────────────┘     └────────────────┘     │  CURRENT_TASKS.md│
                                             │  logs/YYYY-MM-DD │
┌──────────────┐                             │  SCHEDULE.md     │
│  Claude Code  │◄──────────────────────────►│  CLAUDE.md       │
│  (Optional)   │     reads/writes           └──────────────────┘
└──────────────┘     same files
```

## Components

### 1. cadence.py (Telegram Bot)

Single-file Python bot using only stdlib. No external dependencies.

**Modes:**
- `morning` / `evening` / `weekly` — scheduled message senders
- `listen` — long-polling daemon that receives and parses your replies
- `status` / `test` — on-demand commands

**How it reads:**
- `GOALS.md` — parses `**Priority N:** [status]` lines
- `CURRENT_TASKS.md` — parses `URGENT` section
- `logs/YYYY-MM-DD.md` — parses for spending/work/blockers by keyword
- `config.json` — all runtime configuration

**How it writes:**
- `logs/YYYY-MM-DD.md` — appends timestamped entries
- `CURRENT_TASKS.md` — marks tasks `[x]` when you say "done X"

### 2. Markdown Files (Shared State)

Plain text files that both the bot and Claude Code read/write:

| File | Updated by | Read by |
|------|-----------|---------|
| `GOALS.md` | You (weekly) | Bot (priorities), Claude (planning) |
| `CURRENT_TASKS.md` | You + Bot | Bot (urgent), Claude (status) |
| `WEEKLY_SCHEDULE.md` | You (monthly) | Claude (context) |
| `logs/YYYY-MM-DD.md` | Bot (auto) | Bot (evening), Claude (review) |
| `CLAUDE.md` | You (once) | Claude (every session) |
| `config.json` | Setup wizard | Bot (runtime config) |

### 3. Claude Code (Optional AI Layer)

Claude Code reads the same files the bot reads. It adds:
- Intelligent goal review
- Task planning and prioritization
- Blocker resolution
- Weekly review analysis

Claude never talks to the bot directly. The only coupling is through files.

## Data Flow

### Morning
```
Scheduler triggers → cadence.py morning
  → reads config.json (schedule, goals, messages)
  → reads GOALS.md (priorities)
  → reads CURRENT_TASKS.md (urgent)
  → builds message
  → sends to Telegram
```

### User Reply
```
Telegram → cadence.py listen
  → receives message
  → matches against config.tracking.categories
  → writes to logs/YYYY-MM-DD.md
  → optionally marks task done in CURRENT_TASKS.md
  → sends confirmation to Telegram
```

### Evening
```
Scheduler triggers → cadence.py evening
  → reads logs/YYYY-MM-DD.md (today's entries)
  → builds summary of tracked activity
  → sends to Telegram
```

## Security Model

- Bot token: `.env` file (gitignored)
- Chat ID: `config.json` (no secret, just an identifier)
- Bot only responds to configured Chat ID
- All data stored locally as plain text files
- No cloud services, no databases, no external APIs (except Telegram)
