# Telegram Bot Setup Guide

## Step 1: Create a Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name (e.g., "My Cadence Tracker")
4. Choose a username (must end in `bot`, e.g., `my_cadence_bot`)
5. BotFather gives you a **token** like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
6. Save this token — you'll need it during setup

## Step 2: Get Your Chat ID

1. Send any message to your new bot
2. Open this URL in your browser (replace `YOUR_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
3. Find `"chat":{"id":123456789}` in the response
4. That number is your **Chat ID**

### Alternative: Use @userinfobot

1. Search for **@userinfobot** on Telegram
2. Send `/start`
3. It replies with your user ID — that's your Chat ID

## Step 3: Run Setup

```bash
python3 setup.py
```

Enter your bot token and chat ID when prompted.

## Step 4: Test

```bash
python3 cadence.py test
```

You should receive a test message in Telegram. If not:
- Check your bot token is correct
- Check your chat ID is correct
- Make sure you sent at least one message to the bot first

## Security Notes

- Your bot token is stored in `.env` which is gitignored
- Never commit `.env` to version control
- If your token leaks, revoke it via @BotFather with `/revokenewtoken`
- The bot only responds to messages from your Chat ID
