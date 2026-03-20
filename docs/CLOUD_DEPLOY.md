# Cloud Deployment — Oracle Cloud Free Tier

Run cadence 24/7 for free. Your bot responds even when your laptop is off.

---

## Why Oracle Cloud?

- **Free forever** — Always Free tier includes 1 ARM VM (4 CPU, 24 GB RAM)
- **Your data stays on your VM** — no third-party database, just files on disk
- **SSH-only access** — you control who can reach the machine
- **Encrypted at rest** — disk encryption by default

---

## Step 1: Sign Up

1. Go to [cloud.oracle.com](https://cloud.oracle.com) and create a free account
2. You'll need a credit card for verification — **you are never charged** for Always Free resources
3. Select your home region (closest to you for lowest latency)

---

## Step 2: Create an Instance

1. Go to **Compute → Instances → Create Instance**
2. Name: `cadence-bot`
3. Image: **Ubuntu 22.04 Minimal** (or latest Ubuntu)
4. Shape: **VM.Standard.A1.Flex** (ARM) — this is the Always Free shape
   - OCPU: 1 (can use up to 4 for free)
   - Memory: 6 GB (can use up to 24 GB for free)
5. **Add SSH key**: Upload your public key (`~/.ssh/id_rsa.pub`) or generate one
6. Click **Create**

Wait 1-2 minutes for the instance to start. Note the **Public IP Address**.

---

## Step 3: SSH In

```bash
ssh ubuntu@YOUR_PUBLIC_IP
```

If using a custom key:
```bash
ssh -i ~/.ssh/your_key ubuntu@YOUR_PUBLIC_IP
```

---

## Step 4: Install Cadence

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python (usually pre-installed on Ubuntu)
sudo apt install -y python3

# Clone your cadence repo
git clone https://github.com/YOUR_USERNAME/cadence.git
cd cadence

# Create your config
cp config.example.json config.json
nano config.json   # Edit with your settings

# Create .env with your bot token
echo "BOT_TOKEN=your_bot_token_here" > .env

# Copy your markdown files (GOALS.md, CURRENT_TASKS.md, etc.)
# Option A: scp from your laptop
# Option B: create fresh ones from templates
```

---

## Step 5: Test

```bash
python3 cadence.py test
```

You should see a test message in Telegram.

---

## Step 6: Install systemd Service

This keeps the listener running 24/7 and auto-restarts on crash or reboot.

```bash
bash schedulers/install_systemd.sh
```

Verify it's running:
```bash
sudo systemctl status cadence
```

---

## Step 7: Set Up Cron (Morning/Evening/Weekly)

```bash
bash schedulers/install_cron.sh
```

This installs scheduled messages based on your `config.json` times.

---

## Step 8: Verify Everything

```bash
# Check listener is running
sudo systemctl status cadence

# Check cron jobs
crontab -l

# Watch live logs
sudo journalctl -u cadence -f

# Send a test message from Telegram
# The bot should respond
```

---

## File Sync

Your markdown files (GOALS.md, CURRENT_TASKS.md, etc.) live on the VM now. To keep them in sync with your laptop:

### Option A: Git (Recommended)

```bash
# On your laptop — push changes
cd ~/cadence
git add GOALS.md CURRENT_TASKS.md
git commit -m "Update goals"
git push

# On the VM — pull changes
cd ~/cadence
git pull
```

### Option B: rsync

```bash
# Push from laptop to VM
rsync -avz --exclude='.env' --exclude='logs/' \
  ~/cadence/ ubuntu@YOUR_IP:~/cadence/

# Pull from VM to laptop
rsync -avz --exclude='.env' --exclude='logs/' \
  ubuntu@YOUR_IP:~/cadence/ ~/cadence/
```

### Option C: Simple scp

```bash
# Copy specific file to VM
scp GOALS.md ubuntu@YOUR_IP:~/cadence/

# Copy specific file from VM
scp ubuntu@YOUR_IP:~/cadence/GOALS.md ./
```

---

## Monitoring

```bash
# Service status
sudo systemctl status cadence

# Live logs
sudo journalctl -u cadence -f

# Last 50 log lines
sudo journalctl -u cadence -n 50

# Restart after config changes
sudo systemctl restart cadence
```

---

## Security Hardening (Optional)

```bash
# Disable password auth (SSH key only)
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Install fail2ban
sudo apt install -y fail2ban
sudo systemctl enable fail2ban

# Firewall — only allow SSH
sudo apt install -y ufw
sudo ufw allow 22/tcp
sudo ufw enable
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Bot doesn't respond | `sudo systemctl status cadence` — check if running |
| "Connection refused" on SSH | Check security list in Oracle Console → add ingress rule for port 22 |
| Morning message not sending | `crontab -l` — check cron entries exist |
| Bot token invalid | Check `.env` file has correct token |
| Instance won't create | Try a different availability domain in Oracle Console |

---

## Cost

**$0.** Always Free tier includes:
- 4 ARM OCPU + 24 GB RAM (can split across up to 4 VMs)
- 200 GB block storage
- 10 TB/month outbound data

This is more than enough to run cadence forever.

---

*Guide last updated: 2026-03-19*
