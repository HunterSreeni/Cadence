# Cloud Deployment

Run cadence 24/7 for free. Your bot responds even when your laptop is off.

Two free-forever options are available. **Google Cloud is recommended** for most users due to easier signup.

---

## Google Cloud Free Tier

Google Cloud's Always Free tier includes an `e2-micro` VM that runs cadence perfectly. Signup is straightforward and works with most card types.

### Why Google Cloud?

- **Free forever** — Always Free `e2-micro` (1 vCPU, 1 GB RAM, 30 GB disk)
- **Smooth signup** — works with most debit/credit cards worldwide
- **Your data stays on your VM** — just files on disk
- **SSH via browser** — no local SSH key setup required

### GCP Step 1: Sign Up

1. Go to [cloud.google.com](https://cloud.google.com) and click **Get started for free**
2. Sign in with your Google account
3. Add a credit/debit card for verification — **you are never charged** for Always Free resources
4. You also get **$300 free credits** for 90 days to try other services

### GCP Step 2: Create a VM Instance

1. Go to **Compute Engine → VM Instances → Create Instance**
2. Name: `cadence-bot`
3. Region: pick one closest to you (e.g., `asia-south1` for India, `us-central1` for US)
4. Machine type: **e2-micro** (this is the Always Free eligible type)
5. Boot disk: **Ubuntu 22.04 LTS** — click **Change**, select Ubuntu, set size to **30 GB** (free limit)
6. Firewall: check **Allow HTTP traffic** if you want a web dashboard later
7. Click **Create**

Wait 1-2 minutes. Note the **External IP** shown in the instance list.

### GCP Step 3: SSH In

**Option A — Browser SSH (easiest):**
Click the **SSH** button next to your instance in the Google Cloud Console. A terminal opens in your browser.

**Option B — Local terminal:**
```bash
# Install gcloud CLI first: https://cloud.google.com/sdk/docs/install
gcloud compute ssh cadence-bot --zone=YOUR_ZONE
```

**Option C — Standard SSH:**
```bash
ssh -i ~/.ssh/google_compute_engine YOUR_USERNAME@EXTERNAL_IP
```

### GCP Step 4: Install Cadence

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python (usually pre-installed on Ubuntu)
sudo apt install -y python3 git

# Clone your cadence repo
git clone https://github.com/YOUR_USERNAME/cadence.git
cd cadence

# Run the setup wizard — creates config.json, .env (with bot token), GOALS.md, etc.
python3 setup.py
```

The setup wizard handles everything: mode selection, Telegram bot token + chat ID, schedule times, goals, and Claude Code integration. No need to manually create `config.json` or `.env`.

### GCP Step 5: Test, Install Service & Cron

```bash
# Test — sends a message to your Telegram
python3 cadence.py test

# Install systemd service (24/7 listener with auto-restart)
bash schedulers/install_systemd.sh

# Install cron jobs (morning/evening/weekly messages)
bash schedulers/install_cron.sh

# Verify
sudo systemctl status cadence
crontab -l
```

### GCP Always Free Limits

| Resource | Limit |
|----------|-------|
| VM | 1x `e2-micro` (1 vCPU, 1 GB RAM) |
| Boot disk | 30 GB standard persistent disk |
| Outbound data | 1 GB/month (US regions get 200 GB to select destinations) |
| Snapshots | 5 GB |

This is more than enough to run cadence.

### GCP Firewall (if needed)

Google Cloud's default firewall allows SSH (port 22). If you need additional ports:

1. Go to **VPC Network → Firewall → Create Firewall Rule**
2. Direction: Ingress, Targets: All instances, Source: `0.0.0.0/0`
3. Protocols and ports: `tcp:80,443` (or whatever you need)

---

## Oracle Cloud Free Tier

Oracle's Always Free tier is more generous (4 CPU, 24 GB RAM) but **signup can be problematic**. Many users report account creation failures due to card type restrictions, address verification issues, or region capacity limits.

> **If you can't sign up for Oracle Cloud, use [Google Cloud](#google-cloud-free-tier) instead.** It has a smoother signup process and is equally free forever.

### Common Oracle signup issues:
- **Card rejected** — RuPay cards don't work; use Visa/Mastercard
- **Address mismatch** — billing address must exactly match your card's registered address
- **Account creation stuck** — try a different email, different browser, or incognito mode
- **Region at capacity** — try a less popular region (e.g., `ap-hyderabad-1` instead of `ap-mumbai-1`)

### Why Oracle Cloud?

- **Free forever** — Always Free tier includes 1 ARM VM (4 CPU, 24 GB RAM)
- **Your data stays on your VM** — no third-party database, just files on disk
- **SSH-only access** — you control who can reach the machine
- **Encrypted at rest** — disk encryption by default

---

### Oracle Step 1: Sign Up

1. Go to [cloud.oracle.com](https://cloud.oracle.com) and create a free account
2. You'll need a credit card for verification — **you are never charged** for Always Free resources
3. Select your home region (closest to you for lowest latency)

---

### Oracle Step 2: Create an Instance

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

### Oracle Step 3: SSH In

```bash
ssh ubuntu@YOUR_PUBLIC_IP
```

If using a custom key:
```bash
ssh -i ~/.ssh/your_key ubuntu@YOUR_PUBLIC_IP
```

---

### Oracle Step 4: Install Cadence

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and git (usually pre-installed on Ubuntu)
sudo apt install -y python3 git

# Clone your cadence repo
git clone https://github.com/YOUR_USERNAME/cadence.git
cd cadence

# Run the setup wizard — creates config.json, .env (with bot token), GOALS.md, etc.
python3 setup.py
```

The setup wizard handles everything: mode selection, Telegram bot token + chat ID, schedule times, goals, and Claude Code integration. No need to manually create `config.json` or `.env`.

---

### Oracle Step 5: Test

```bash
python3 cadence.py test
```

You should see a test message in Telegram.

---

### Oracle Step 6: Install systemd Service

This keeps the listener running 24/7 and auto-restarts on crash or reboot.

```bash
bash schedulers/install_systemd.sh
```

Verify it's running:
```bash
sudo systemctl status cadence
```

---

### Oracle Step 7: Set Up Cron (Morning/Evening/Weekly)

```bash
bash schedulers/install_cron.sh
```

This installs scheduled messages based on your `config.json` times.

---

### Oracle Step 8: Verify Everything

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
| "Connection refused" on SSH | Check firewall rules (GCP: VPC Firewall, Oracle: Security List) — add ingress for port 22 |
| Morning message not sending | `crontab -l` — check cron entries exist |
| Bot token invalid | Check `.env` file has correct token |
| Oracle instance won't create | Try a different availability domain or region |
| Oracle signup rejected | Use Google Cloud instead — see [GCP section](#google-cloud-free-tier) |
| GCP instance won't create | Make sure you selected `e2-micro` and a region with Always Free availability |

---

## Cost Comparison

| Provider | VM | RAM | Disk | Outbound | Cost |
|----------|----|-----|------|----------|------|
| **Google Cloud** | 1 vCPU (`e2-micro`) | 1 GB | 30 GB | 1 GB/month | **$0** (Always Free) |
| **Oracle Cloud** | 4 OCPU (ARM) | 24 GB | 200 GB | 10 TB/month | **$0** (Always Free) |

Both are more than enough to run cadence forever. Google Cloud is easier to sign up for; Oracle Cloud gives you more resources if you can get an account.

---

*Guide last updated: 2026-03-20*
