# Claude Code Integration Guide

cadence works great on its own, but adding Claude Code creates an AI-enhanced productivity loop.

## How It Works

cadence and Claude Code share state through **markdown files** — no API coupling:

```
You reply in Telegram → cadence writes to logs/YYYY-MM-DD.md
Claude Code reads logs/ → understands what you did today
Claude Code reads GOALS.md → knows your priorities
Claude Code helps plan → you execute → cadence tracks
```

## Setup

### 1. Enable Claude Code during setup

When running `python3 setup.py`, answer **yes** to "Use with Claude Code?"

This generates:
- `CLAUDE.md` — instructions Claude reads at every session start
- Ready for MCP server installation

### 2. Install the datetime MCP server

The MCP server gives Claude Code the ability to check the current date and time.

```bash
python3 mcp/install_mcp.py
```

This adds the datetime server to your `~/.mcp.json`. Restart Claude Code to activate.

**Requires:** The `mcp` Python package (`pip install mcp`). If not installed, Claude Code still works — it just won't have the datetime tool.

### 3. Start a Claude Code session

Open Claude Code in your cadence directory:

```bash
cd /path/to/your/cadence
claude
```

Claude will:
1. Read `CLAUDE.md` — understand the project structure
2. Read `GOALS.md` — check your weekly priorities
3. Read today's log — see what's been tracked
4. Brief you on status and help plan

## What Claude Code Does

- Reads your goals and priorities at session start
- Reviews your daily logs
- Helps plan your week during Sunday reviews
- Suggests priority adjustments based on progress
- Helps unblock tasks

## What Claude Code Doesn't Do

- Never sends Telegram messages (the bot handles that)
- Never modifies your config
- Doesn't need to be running for the bot to work

## Customizing CLAUDE.md

Edit `CLAUDE.md` to change what Claude does at session start. Common customizations:

- Add specific instructions for your workflow
- Define what files Claude should read first
- Set rules about what Claude should/shouldn't modify
