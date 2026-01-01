# KitStream - Telegram File to Link Bot

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 Overview

KitStream is a Telegram bot that converts media files to instant direct download and streaming links.

### Features
- ⚡ Superfast download and stream links
- 📺 Multi-player streaming support (MX, VLC, PlayIt)
- 🔗 Permanent links (won't expire)
- 📣 Channel support - auto generate links
- 💎 Premium user system
- 🔒 Force subscribe feature
- 📊 MongoDB database support

---

## 📌 Environment Variables

<details><summary>Click to expand</summary>

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Get from @BotFather |
| `API_ID` | Get from https://my.telegram.org |
| `API_HASH` | Get from https://my.telegram.org |
| `ADMINS` | Admin user IDs (space separated) |
| `BOT_USERNAME` | Bot username without @ |
| `DATABASE_URI` | MongoDB URI |
| `BIN_CHANNEL` | File storage channel ID |
| `LOG_CHANNEL` | Log channel ID |
| `PREMIUM_LOGS` | Premium logs channel ID |
| `VERIFIED_LOG` | Verified users log channel ID |
| `FQDN` | Your domain (e.g., https://yourdomain.com/) |
| `PORT` | Web server port (default: 2626) |
| `NO_PORT` | Set True if not using port in URL |
| `HAS_SSL` | Set True if using HTTPS |

</details>

---

## 🛠️ Commands

<details><summary>User Commands</summary>

```
/start       - Check if bot is running
/help        - Show help menu
/about       - Show about info
/info        - Get your info
/files       - List your uploaded files
/del_files   - Delete your uploaded files
/plan        - Show premium plans
/myplan      - Show your current plan
/batch       - Batch mode for multiple files
```

</details>

<details><summary>Admin Commands</summary>

```
/ban             - Ban a user
/unban           - Unban a user
/broadcast       - Send broadcast message
/pin_broadcast   - Pin broadcast message
/restart         - Restart the bot
/stats           - Show bot statistics
/blocked         - List blocked users
/verified_users  - List verified users
/add_premium     - Grant premium access
/remove_premium  - Remove premium access
/premium_user    - List all premium users
```

</details>

---

## 🚀 Deployment

### Deploy on VPS (Ubuntu 24)

```bash
# Clone repository
git clone <your-repo-url> /opt/kitstream
cd /opt/kitstream

# Install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git -y

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
nano .env  # Add your environment variables

# Run bot
python3 bot.py
```

### Deploy with Docker

```bash
docker build -t kitstream .
docker run -d --name kitstream --env-file .env kitstream
```

### Deploy on Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

### Deploy on Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file.

---

## 📞 Support

For issues or questions, create an issue in this repository.
