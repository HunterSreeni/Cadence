# Docker Deployment

Run cadence in a Docker container. Useful for self-hosting on any machine.

---

## Quick Start

```bash
# 1. Configure
cp config.example.json config.json
echo "BOT_TOKEN=your_token" > .env

# 2. Build and run
docker compose up -d

# 3. Check logs
docker compose logs -f
```

---

## What's Included

- `Dockerfile` — builds a minimal Python 3.12 image with cadence
- `docker-compose.yml` — runs the listener with volume mounts for persistence

---

## Volume Mounts

All your data persists on the host machine:

| Container Path | Host Path | Purpose |
|---|---|---|
| `/app/logs/` | `./logs/` | Daily log files |
| `/app/config.json` | `./config.json` | Configuration |
| `/app/.env` | `./.env` | Bot token |
| `/app/GOALS.md` | `./GOALS.md` | Goals file |
| `/app/CURRENT_TASKS.md` | `./CURRENT_TASKS.md` | Tasks file |
| `/app/balances.json` | `./balances.json` | Account balances |
| `/app/commands/` | `./commands/` | Plugins |

---

## Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart (after config changes)
docker compose restart

# View logs
docker compose logs -f

# Send a one-off command
docker compose exec cadence python3 cadence.py status
docker compose exec cadence python3 cadence.py morning
```

---

## Scheduled Messages (Cron on Host)

Docker runs the listener. For scheduled morning/evening messages, add cron jobs on the host:

```bash
# Edit crontab
crontab -e

# Add:
0 9 * * * cd /path/to/cadence && docker compose exec -T cadence python3 cadence.py morning
45 21 * * * cd /path/to/cadence && docker compose exec -T cadence python3 cadence.py evening
0 19 * * 0 cd /path/to/cadence && docker compose exec -T cadence python3 cadence.py weekly
```

---

*Docker is optional. cadence works perfectly without it.*
