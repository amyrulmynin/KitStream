# Panduan Setup VPS Ubuntu 24 untuk KitStream

Panduan lengkap untuk deploy KitStream Bot di VPS Ubuntu 24.04.

---

## 📋 Prerequisite

- VPS dengan Ubuntu 24.04 LTS
- Minimum 1GB RAM, 1 vCPU
- SSH access ke VPS
- Domain (optional, untuk SSL)

---

## 🚀 Langkah Setup

### Langkah 1: Connect ke VPS

```bash
ssh root@YOUR_VPS_IP
```

### Langkah 2: Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git screen -y
```

### Langkah 3: Clone Repository

```bash
cd /opt
git clone <your-repo-url> kitstream
cd kitstream
```

### Langkah 4: Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Langkah 5: Configure Environment Variables

Cipta fail `.env` dengan variable yang diperlukan:

```bash
nano .env
```

Isi dengan:

```env
# Telegram API Credentials
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token

# Admin Configuration
ADMINS=your_telegram_user_id
BOT_USERNAME=your_bot_username
OWNER_USERNAME=your_username

# Channel Configuration
BIN_CHANNEL=-100xxxxxxxxxx
LOG_CHANNEL=-100xxxxxxxxxx
PREMIUM_LOGS=-100xxxxxxxxxx
VERIFIED_LOG=-100xxxxxxxxxx
SUPPORT_GROUP=-100xxxxxxxxxx

# Auth Channels (optional, space separated)
AUTH_CHANNEL=-100xxxxxxxxxx -100xxxxxxxxxx

# MongoDB
DATABASE_URI=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=kitstream

# Domain Configuration
FQDN=your-domain.com
PORT=2626
NO_PORT=True
HAS_SSL=True

# Feature Toggles
VERIFY=False
FSUB=True
ENABLE_LIMIT=False
MAINTENANCE_MODE=False
PROTECT_CONTENT=False

# Images (optional)
PICS=https://your-image-url.jpg
```

Tekan `Ctrl+X`, kemudian `Y` untuk save.

### Langkah 6: Test Run Bot

```bash
source venv/bin/activate
python3 bot.py
```

Jika bot berjalan dengan jayanya, teruskan ke Langkah 7.

### Langkah 7: Setup Systemd Service

Cipta service file:

```bash
sudo nano /etc/systemd/system/kitstream.service
```

Paste content berikut:

```ini
[Unit]
Description=KitStream Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kitstream
Environment="PATH=/opt/kitstream/venv/bin"
ExecStart=/opt/kitstream/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable dan start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable kitstream
sudo systemctl start kitstream
```

Check status:

```bash
sudo systemctl status kitstream
```

### Langkah 8: Setup Nginx (Optional - untuk domain)

Install Nginx:

```bash
sudo apt install nginx -y
```

Cipta config:

```bash
sudo nano /etc/nginx/sites-available/kitstream
```

Paste:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:2626;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/kitstream /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Langkah 9: Setup SSL dengan Certbot (Optional)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

## 🔧 Command Berguna

### Lihat Log Bot

```bash
sudo journalctl -u kitstream -f
```

### Restart Bot

```bash
sudo systemctl restart kitstream
```

### Stop Bot

```bash
sudo systemctl stop kitstream
```

### Update Bot

```bash
cd /opt/kitstream
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart kitstream
```

---

## 📝 MongoDB Setup

### Option A: MongoDB Atlas (Recommended)

1. Pergi ke https://cloud.mongodb.com
2. Create free cluster
3. Create database user
4. Whitelist IP (0.0.0.0/0 untuk semua)
5. Get connection string
6. Replace `DATABASE_URI` dalam `.env`

### Option B: Install MongoDB Locally

```bash
# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod

# Connection URI untuk local MongoDB
DATABASE_URI=mongodb://localhost:27017/kitstream
```

---

## ✅ Troubleshooting

| Masalah | Penyelesaian |
|---------|--------------|
| Bot tidak start | Check log: `sudo journalctl -u kitstream -f` |
| MongoDB connection error | Verify DATABASE_URI dan whitelist IP |
| Port already in use | Tukar PORT dalam .env atau kill process |
| Permission denied | Run dengan `sudo` atau check file permissions |

---

## 🔐 Firewall Setup

```bash
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 2626  # Bot port (jika guna direct)
sudo ufw enable
```
