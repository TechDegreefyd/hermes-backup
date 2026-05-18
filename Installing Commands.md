# Hermes Agent — Complete Command Reference & Runbook 🔧
## For DegreeFYD Setup, Configuration & VPS Migration

> **Quick reference** of every command, path, port, and procedure — no stories, just actions. Use this when setting up a new machine or migrating to VPS.

---

# 📌 SECTION 1: KEY LOCATIONS & PORTS

## File Paths (Current Environment)

| What | Path |
|------|------|
| Workspace (host) | `/home/mohit/workspace/` |
| Workspace (Docker container) | `/workspace/` ← same files, different address |
| Hermes brain | `~/.hermes/` or `/home/mohit/.hermes/` |
| Config file | `~/.hermes/config.yaml` |
| Secrets file | `~/.hermes/.env` |
| Memories | `~/.hermes/memories/MEMORY.md` + `USER.md` |
| Skills | `~/.hermes/skills/` (929 files) |
| Cron jobs | `~/.hermes/cron/jobs.json` |
| Gateway logs | `~/.hermes/logs/gateway.log` |
| Sessions | `~/.hermes/sessions/` |
| Python venv | `/workspace/.venv/bin/python` |
| MCP server | `/workspace/mcp_server.py` |
| DB rules | `/workspace/db-rules/online_rules.md`, `regular_rules.md` |
| Config: Online targets | `/workspace/report_config.json` |
| Config: Regular targets | `/workspace/regular_report_config.json` |
| Reports: Online generator | `/workspace/run_online_v11.py` |
| Reports: Regular generator | `/workspace/run_regular_v11.py` |
| Backups | `/workspace/backup/` |

## Ports & Services

| Port | Service | URL |
|------|---------|-----|
| **3000** | Hermes Workspace V2 (modern UI) | http://localhost:3000 |
| **8090** | Dashboard (lightweight) | http://localhost:8090 |
| **8642** | Hermes Gateway (brain + API) | http://localhost:8642 |
| **8787** | Hermes WebUI (Docker) | http://localhost:8787 |
| **5001** | Admission Bot (FastAPI) | http://localhost:5001 |

## Databases

| Database | Host | Port | Purpose |
|----------|------|------|---------|
| `degreefyd_online_lms` | `storage.bhugoal.cloud` | 54321 | Online programs |
| `degreefyd_regular_lms` | `storage.bhugoal.cloud` | 54321 | Regular programs |
| `degreefyd_regular_cgc_lms` | `storage.bhugoal.cloud` | 54321 | CGC Landran |
| `degreefyd_regular_amity_lms` | `storage.bhugoal.cloud` | 54321 | Amity University |

## WhatsApp & Telegram

| Channel | ID / Token | Purpose |
|---------|-----------|---------|
| Telegram Bot | `@hermes_degreefyd_bot` | Primary input channel (talk to me) |
| WhatsApp Admin Group | `120363426619711887@g.us` | Outgoing reports & files |
| WHAPI Token | In `~/.hermes/.env` as `WHAPI_TOKEN` | WhatsApp API access |

---

# 📌 SECTION 2: HERMES INSTALLATION (FRESH SETUP)

## 2.1 Install WSL (Windows only)

```powershell
# Windows PowerShell (Admin):
wsl --install
# Restart, then Ubuntu opens — create username/password
```

## 2.2 Install Hermes Agent

```bash
# One-line install:
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Verify:
hermes doctor
```

## 2.3 Configure AI Provider

```bash
# Interactive setup wizard:
hermes setup

# Or set provider directly:
hermes config set model.default deepseek-v4-flash
hermes config set model.provider deepseek
```

## 2.4 Configure Telegram Gateway

```bash
# Step 1: Set up gateway
hermes gateway setup
# → Select Telegram
# → Enter bot token from @BotFather
# → Enter user ID (get from @userinfobot)

# Step 2: Stop WhatsApp from crashing gateway
sed -i 's/^WHATSAPP_ENABLED=true/# WHATSAPP_ENABLED=true/' ~/.hermes/.env
sed -i 's/^WHATSAPP_ALLOWED_USERS=.*/# &/' ~/.hermes/.env

# Step 3: Ensure Telegram credentials in .env
# Edit ~/.hermes/.env and add:
# TELEGRAM_BOT_TOKEN=8611628152:AAHfEKyDR5UgiCsO-zW9b3bQes8rMH3P82Q
# TELEGRAM_ALLOWED_USERS=925818478

# Step 4: Start gateway
hermes gateway run --replace

# Verify:
curl -X POST "https://api.telegram.org/bot8611628152:AAHfEKyDR5UgiCsO-zW9b3bQes8rMH3P82Q/sendMessage" \
  -d "chat_id=925818478&text=Test from cmd"

# Step 5: Install as service (auto-start)
hermes gateway install
systemctl --user enable hermes-gateway
systemctl --user start hermes-gateway

# Step 6: WSL auto-start (systemd)
echo -e "[boot]\nsystemd=true" | sudo tee -a /etc/wsl.conf
```

## 2.5 Set Up WhatsApp (Outgoing Only)

```bash
# Add to ~/.hermes/.env:
echo "WHAPI_TOKEN=WVEwEfgZcvJryDYn1Q8H3rW1rkIrobAM" >> ~/.hermes/.env
echo "WHATSAPP_GROUP=120363426619711887@g.us" >> ~/.hermes/.env
```

## 2.6 Set Up Hermes WebUI (Docker)

```bash
# Run container with direct workspace mount (no symlinks needed):
docker run -d \
  -v /home/mohit/.hermes:/home/hermeswebui/.hermes \
  -v /workspace:/home/hermeswebui/workspace \
  -e HERMES_WEBUI_STATE_DIR=/home/hermeswebui/.hermes/webui-mvp \
  -e HERMES_WEBUI_PASSWORD="degreefyd" \
  -e WANTED_UID=$(id -u) \
  -e WANTED_GID=$(id -g) \
  -p 8787:8787 \
  --name hermes-webui \
  --restart always \
  ghcr.io/nesquena/hermes-webui:latest

# Access at: http://localhost:8787
```

## 2.7 Install Workspace V2 (Modern UI)

```bash
# Prerequisites:
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo npm install -g pnpm

# Clone & install:
cd /workspace
git clone https://github.com/outsourc-e/hermes-workspace.git
cd hermes-workspace
cp .env.example .env
sed -i 's|HERMES_API_URL=.*|HERMES_API_URL=http://127.0.0.1:8642|' .env
echo "HERMES_API_KEY=degreefyd-secret-key" >> .env
pnpm install

# Start:
pnpm run dev --port 3000
# Access at: http://localhost:3000
```

## 2.8 Set Up Database Connection (MCP Server)

```bash
# Python venv with dependencies:
python3 -m venv /workspace/.venv
/workspace/.venv/bin/pip install fastmcp asyncpg httpx requests python-dotenv openpyxl pandas

# Verify MCP server runs:
/workspace/.venv/bin/python /workspace/mcp_server.py --transport stdio

# Configure in ~/.hermes/config.yaml:
# mcp_servers:
#   lms_db:
#     command: /workspace/.venv/bin/python
#     args:
#       - /workspace/mcp_server.py

# Add DB credentials to ~/.hermes/.env:
echo "ONLINE_LMS_DB_HOST=storage.bhugoal.cloud" >> ~/.hermes/.env
echo "ONLINE_LMS_DB_PORT=54321" >> ~/.hermes/.env
echo "ONLINE_LMS_DB_NAME=degreefyd_online_lms" >> ~/.hermes/.env
echo "ONLINE_LMS_DB_USER=postgres" >> ~/.hermes/.env
echo "ONLINE_LMS_DB_PASSWORD=<password>" >> ~/.hermes/.env

# Test:
hermes mcp test lms_db

# Restart gateway:
hermes gateway run --replace
```

---

# 📌 SECTION 3: VPS MIGRATION (LAPTOP → CLOUD)

## 3.1 Pre-Migration: Token Scrub (CRITICAL)

```bash
# Scan for all hardcoded tokens BEFORE backing up:
grep -roh --include='*.py' -E 'EAA[A-Za-z0-9_-]{20,}' /workspace | sort -u
grep -rn --include='*.py' -E "(TOKEN|API_KEY|SECRET)\s*=\s*['\"][A-Za-z0-9_-]{10,}" /workspace \
  | grep -v '.venv/' | grep -v '__pycache__'

# Fix each found token → replace with os.getenv():
sed -i 's|"EAAtoken..."|os.getenv("META_TOKEN","")|g' /workspace/script.py
```

## 3.2 Create Clean Backup

```bash
cd /

tar czf /workspace/hermes-vps-backup-$(date +%Y-%m-%d).tar.gz \
  workspace/*.py workspace/*.json workspace/*.js workspace/*.md \
  workspace/db-rules/ workspace/mcp_server.py \
  home/hermeswebui/.hermes/config.yaml \
  home/hermeswebui/.hermes/cron/ \
  home/hermeswebui/.hermes/skills/ \
  home/hermeswebui/.hermes/memories/ \
  --exclude='workspace/.env' \
  --exclude='workspace/fresh_token.json' \
  --exclude='.venv' --exclude='node_modules' \
  --exclude='__pycache__' --exclude='state.db*' \
  --exclude='*/cache/*' --exclude='*.jpg' --exclude='*.png'

# Verify backup:
tar tzf /workspace/hermes-vps-backup-*.tar.gz | wc -l
tar tzf /workspace/hermes-vps-backup-*.tar.gz | grep -E '(config\.yaml|cron/jobs|skills/|mcp_server|memories/)'
tar tzf /workspace/hermes-vps-backup-*.tar.gz | grep -E '(\.env$|auth\.json|google_token)' && echo "⚠️  SENSITIVE FOUND!" || echo "✅ Clean"
```

## 3.3 Transfer to VPS

```bash
# Option A: SCP (requires SSH access)
scp /workspace/hermes-vps-backup-*.tar.gz root@<VPS_IP>:/root/

# Option B: Gofile (no SSH needed)
SERVER=$(curl -s https://api.gofile.io/servers | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['servers'][0]['name'])")
curl -F "file=@/workspace/hermes-vps-backup-$(date +%Y-%m-%d).tar.gz" \
  "https://${SERVER}.gofile.io/contents/uploadfile"
```

## 3.4 VPS: Initial Setup

```bash
# SSH to VPS:
ssh root@<VPS_IP>

# Update system:
apt-get update && apt-get upgrade -y
apt-get install -y curl git docker.io docker-compose python3 python3-pip python3-venv nginx
sudo npm install -g pnpm
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Restore backup:
tar xzf /root/hermes-vps-backup-*.tar.gz -C /

# Install Hermes:
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

## 3.5 VPS: Recreate .env File

```bash
cat > /home/hermeswebui/.hermes/.env << 'EOF'
DEEPSEEK_API_KEY=your_key
WHAPI_TOKEN=WVEwEfgZcvJryDYn1Q8H3rW1rkIrobAM
WHATSAPP_GROUP=120363426619711887@g.us
ONLINE_LMS_DB_HOST=storage.bhugoal.cloud
ONLINE_LMS_DB_PORT=54321
ONLINE_LMS_DB_NAME=degreefyd_online_lms
ONLINE_LMS_DB_USER=postgres
ONLINE_LMS_DB_PASSWORD=<password>
REGULAR_LMS_DB_HOST=storage.bhugoal.cloud
REGULAR_LMS_DB_PORT=54321
REGULAR_LMS_DB_NAME=degreefyd_regular_lms
REGULAR_LMS_DB_USER=postgres
REGULAR_LMS_DB_PASSWORD=<password>
REGULAR_CGC_LMS_DB_NAME=degreefyd_regular_cgc_lms
REGULAR_AMITY_LMS_DB_NAME=degreefyd_regular_amity_lms
TELEGRAM_BOT_TOKEN=8611628152:AAHfEKyDR5UgiCsO-zW9b3bQes8rMH3P82Q
TELEGRAM_ALLOWED_USERS=925818478
EOF

# Also copy to the user home if needed:
cp /home/hermeswebui/.hermes/.env /root/.hermes/.env 2>/dev/null || true
```

## 3.6 VPS: Fix Paths (Old Laptop → New VPS)

```bash
# Bulk replace old paths in all Python files:
find /workspace -name '*.py' -exec sed -i 's|/home/mohit/workspace|/workspace|g' {} \;
find /workspace -name '*.json' -exec sed -i 's|/home/mohit/workspace|/workspace|g' {} \;

# Also fix in Hermes config if needed:
sed -i 's|/home/mohit/workspace|/workspace|g' /home/hermeswebui/.hermes/config.yaml 2>/dev/null || true
```

## 3.7 VPS: Recreate Python Virtual Environment

```bash
cd /workspace
python3 -m venv .venv
/workspace/.venv/bin/pip install fastmcp asyncpg httpx requests python-dotenv openpyxl pandas
```

## 3.8 VPS: Configure & Start MCP

```bash
# Set MCP config paths:
hermes config set mcp_servers.lms_db.command /workspace/.venv/bin/python
hermes config set mcp_servers.lms_db.args.0 /workspace/mcp_server.py

# Test:
hermes mcp test lms_db
```

## 3.9 VPS: Start All Services

```bash
# 1. Gateway (Telegram + API):
hermes gateway run --replace &

# 2. Enable API server for WebUI:
echo "API_SERVER_ENABLED=true" >> /root/.hermes/.env
hermes gateway run --replace &

# 3. Deploy WebUI Docker:
docker run -d \
  -v /root/.hermes:/home/hermeswebui/.hermes \
  -v /workspace:/home/hermeswebui/workspace \
  -e HERMES_WEBUI_PASSWORD="degreefyd" \
  -p 8787:8787 \
  --name hermes-webui \
  --restart always \
  ghcr.io/nesquena/hermes-webui:latest

# 4. Enable auto-start for gateway:
systemctl --user enable hermes-gateway

# 5. Make Docker survive reboots:
docker update --restart always hermes-webui
```

## 3.10 VPS: Verify Everything

```bash
# Test database:
hermes mcp test lms_db
# Test skills:
hermes skills list | grep -E "(lms-reporting|reconciliation)"
# Test gateway:
hermes gateway status
# Test cron:
hermes cron list
# Test a query:
hermes chat -q "How many leads came yesterday in online lms?"
# Test Telegram: send a message to @hermes_degreefyd_bot
# Test WhatsApp: the next cron job should auto-deliver
```

## 3.11 VPS: Restore/Recreate Cron Jobs

```bash
# List current:
hermes cron list

# If missing, recreate:
hermes cron create "0 15 * * *" \
  --name "Daily Online LMS Report" \
  --prompt "Generate and send the Daily Online LMS Report for today" \
  --skills "online-lms-reporting,whatsapp-file-sending" \
  --workdir /workspace

hermes cron create "0 15 * * *" \
  --name "Daily Regular LMS Report" \
  --prompt "Generate and send the Daily Regular LMS Report for today" \
  --skills "regular-lms-reporting,whatsapp-file-sending" \
  --workdir /workspace

hermes cron create "0 9 * * *" \
  --name "Daily Branded Recon Report" \
  --prompt "Generate and send the Regular API Recon Report with branded campaign filter" \
  --skills "regular-lms-reconciliation-reporting" \
  --workdir /workspace

hermes cron create "0 3 * * *" \
  --name "Meta Ad Details" \
  --prompt "Fetch Meta ad details for all 3 ad accounts and report performance" \
  --skills "degreefyd-meta-lms-attribution" \
  --workdir /workspace
```

---

# 📌 SECTION 4: COMMON FIXES & TROUBLESHOOTING

## Launch the Gateway

```bash
hermes gateway run --replace
```

> Use `--replace` to kill any existing gateway instance before starting fresh.

## Fix Python Symlink (Broken venv)

```bash
# WSL (host):
ln -sf /usr/local/bin/python3 /workspace/.venv/bin/python3

# Docker container:
docker exec -u root hermes-webui bash -c "cd /workspace/.venv/bin && rm -f python3 python3.12 && ln -sf /usr/local/bin/python3 python3 && ln -s python3 python3.12"
```

## Fix Docker Container After Restart (Full Fix)

```bash
docker exec -u root hermes-webui bash -c "
  ln -sf /workspace /home/mohit/workspace
  cd /workspace/.venv/bin
  rm -f python3 python3.12
  ln -sf /usr/local/bin/python3 python3
  ln -s python3 python3.12
  mkdir -p /root/.hermes
  ln -sf /home/hermeswebui/.hermes/config.yaml /root/.hermes/config.yaml
"
```

## Kill Zombie Processes

```bash
pkill -9 -f hermes-gateway
pkill -9 -f bridge.js
pkill -9 -f mcp_server
fuser -k 8642/tcp
fuser -k 8787/tcp
```

## View Gateway Logs

```bash
tail -f ~/.hermes/logs/gateway.log
grep -i "error" ~/.hermes/logs/gateway.log | tail -20
```

## Check MCP Server Directly

```bash
/workspace/.venv/bin/python /workspace/mcp_server.py --transport stdio 2>&1
```

## Check Service Status

```bash
hermes gateway status
hermes doctor
systemctl --user status hermes-gateway
docker logs hermes-webui 2>&1 | tail -15
curl -s http://localhost:8787/health
curl -s http://localhost:8642/health
```

## Update Hermes

```bash
# Update to latest version:
hermes update

# Or manual clean update:
cd ~/.hermes/hermes-agent
git pull
rm -rf build/ hermes_agent.egg-info/
./venv/bin/pip install -e ".[all]"
```

## Fix the Gateway Service (after crash loop)

```bash
systemctl --user reset-failed hermes-gateway
systemctl --user restart hermes-gateway
```

## Token Scrub (Find & Replace Hardcoded Meta Tokens)

```bash
cd /workspace

# Find them:
grep -roh --include='*.py' -E 'EAA[A-Za-z0-9_-]{20,}' . | grep -v '.venv/' | sort -u

# Replace all (for each token found, substitute with env var):
for t in $(grep -roh --include='*.py' -E 'EAA[A-Za-z0-9_-]{20,}' . 2>/dev/null | grep -v '.venv/' | sort -u); do
  find . -name '*.py' -not -path './.venv/*' -exec sed -i "s|\"$t\"|\"\"|g" {} \;
done

# Fix broken double-quotes (if any):
find . -name '*.py' -exec grep -l '= """"' {} \; 2>/dev/null | while read f; do
  sed -i 's/= """"/= ""/g' "$f"
  echo "Fixed: $f"
done
```

---

# 📌 SECTION 5: USEFUL SHORTCUTS

## WSL Windows Desktop Shortcut (".bat" file)

Create a file on your Windows Desktop called `Start Hermes.bat`:

```batch
@echo off
wsl.exe -d Ubuntu -e bash -ic "cd /workspace/hermes-workspace && pnpm run dev --port 3000"
pause
```

## Bash Alias (add to ~/.bashrc)

```bash
alias workspace="cd /workspace/hermes-workspace && pnpm run dev --port 3000"
alias gwlog="tail -f ~/.hermes/logs/gateway.log"
alias gwrestart="hermes gateway run --replace"
```

## Quick Python Path Check

```bash
# Find actual python
which python3
ls -la /workspace/.venv/bin/python3
cat /workspace/.venv/pyvenv.cfg | grep -E "(home|executable)"
```

---

# 📌 SECTION 6: KEY TELEGRAM COMMANDS (IN-SESSION)

| Command | What It Does |
|---------|-------------|
| `/new` | Fresh conversation |
| `/help` | Show all commands |
| `/retry` | Resend last message |
| `/undo` | Remove last exchange |
| `/title [name]` | Name the current session |
| `/skill <name>` | Load a skill |
| `/model [name]` | Show or change AI model |
| `/memory` | View saved memories |
| `/platforms` | Show connection status |
| `/usage` | Show token usage & cost |
| `/stop` | Kill background processes |
| `/quit` | Exit CLI |
| `/yolo` | Skip dangerous command approval |
| `/resume [name]` | Resume a previous session |

---

> **Pro tip:** Bookmark this page. When migrating to VPS, follow Section 3 sequentially —
> it's the exact playbook used to move from laptop to 24/7 cloud.
>
> Last updated: May 18, 2026
