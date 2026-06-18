# 🚀 VPS DEPLOYMENT GUIDE - Smart Attendance System

**Complete step-by-step guide for deploying on VPS (Ubuntu/Debian)**

---

## 📋 PREREQUISITES

### VPS Requirements:
- **OS:** Ubuntu 20.04/22.04 or Debian 11/12
- **RAM:** Minimum 2GB (4GB recommended)
- **Storage:** Minimum 20GB
- **CPU:** 2 cores recommended
- **Python:** 3.8 or higher

### What You Need:
- VPS IP address
- SSH access (root or sudo user)
- Domain name (optional but recommended)

---

## 🔧 STEP 1: CONNECT TO VPS

```bash
# Connect via SSH
ssh root@your_vps_ip

# Or with username
ssh username@your_vps_ip
```

---

## 📦 STEP 2: UPDATE SYSTEM & INSTALL DEPENDENCIES

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and essential packages
sudo apt install python3 python3-pip python3-venv python3-dev -y

# Install system dependencies for face_recognition
sudo apt install build-essential cmake -y
sudo apt install libopenblas-dev liblapack-dev -y
sudo apt install libx11-dev libgtk-3-dev -y

# Install PostgreSQL (recommended for production)
sudo apt install postgresql postgresql-contrib -y

# Install Nginx (web server)
sudo apt install nginx -y

# Install supervisor (process manager)
sudo apt install supervisor -y

# Install git
sudo apt install git -y
```

---

## 📁 STEP 3: SETUP PROJECT

```bash
# Create project directory
sudo mkdir -p /var/www/attendance_system
cd /var/www/attendance_system

# Upload your project files
# Option 1: Using Git
git clone your_repository_url .

# Option 2: Using SCP from local machine
# Run this on your LOCAL machine:
scp -r /path/to/your/project/* username@your_vps_ip:/var/www/attendance_system/

# Set permissions
sudo chown -R $USER:$USER /var/www/attendance_system
```

---

## 🐍 STEP 4: SETUP PYTHON VIRTUAL ENVIRONMENT

```bash
cd /var/www/attendance_system

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install production server
pip install gunicorn
```

---

## 🗄️ STEP 5: SETUP DATABASE (PostgreSQL)

```bash
# Switch to postgres user
sudo -u postgres psql

# Inside PostgreSQL shell, run:
CREATE DATABASE attendance_db;
CREATE USER attendance_user WITH PASSWORD 'your_strong_password';
ALTER ROLE attendance_user SET client_encoding TO 'utf8';
ALTER ROLE attendance_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE attendance_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE attendance_db TO attendance_user;
\q

# Install PostgreSQL adapter
pip install psycopg2-binary
```

---

## ⚙️ STEP 6: CONFIGURE DJANGO SETTINGS

Create production settings file:

```bash
nano myproject/settings_production.py
```

Add this content:

```python
from .settings import *

# SECURITY
DEBUG = False
ALLOWED_HOSTS = ['your_domain.com', 'www.your_domain.com', 'your_vps_ip']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'attendance_db',
        'USER': 'attendance_user',
        'PASSWORD': 'your_strong_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Static files
STATIC_ROOT = '/var/www/attendance_system/staticfiles/'
MEDIA_ROOT = '/var/www/attendance_system/media/'

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Generate new secret key
SECRET_KEY = 'your-new-secret-key-here-generate-random-50-chars'
```

---

## 🔄 STEP 7: RUN MIGRATIONS & COLLECT STATIC

```bash
# Set production settings
export DJANGO_SETTINGS_MODULE=myproject.settings_production

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Create media directories
mkdir -p media/employee_photos
mkdir -p media/faces
mkdir -p media/recognition_logs

# Set permissions
sudo chown -R www-data:www-data /var/www/attendance_system
sudo chmod -R 755 /var/www/attendance_system
```

---

## 🦄 STEP 8: SETUP GUNICORN

Create Gunicorn config:

```bash
nano /var/www/attendance_system/gunicorn_config.py
```

Add:

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
errorlog = "/var/www/attendance_system/logs/gunicorn_error.log"
accesslog = "/var/www/attendance_system/logs/gunicorn_access.log"
loglevel = "info"
```

Create logs directory:

```bash
mkdir -p /var/www/attendance_system/logs
```

Test Gunicorn:

```bash
cd /var/www/attendance_system
source venv/bin/activate
gunicorn --config gunicorn_config.py myproject.wsgi:application
```

Press Ctrl+C to stop.

---

## 👁️ STEP 9: SETUP SUPERVISOR

Create supervisor config:

```bash
sudo nano /etc/supervisor/conf.d/attendance_system.conf
```

Add:

```ini
[program:attendance_system]
command=/var/www/attendance_system/venv/bin/gunicorn --config /var/www/attendance_system/gunicorn_config.py myproject.wsgi:application
directory=/var/www/attendance_system
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/www/attendance_system/logs/supervisor.log
environment=DJANGO_SETTINGS_MODULE="myproject.settings_production"
```

Start supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start attendance_system
sudo supervisorctl status
```

---

## 🌐 STEP 10: SETUP NGINX

Create Nginx config:

```bash
sudo nano /etc/nginx/sites-available/attendance_system
```

Add:

```nginx
server {
    listen 80;
    server_name your_domain.com www.your_domain.com your_vps_ip;
    
    client_max_body_size 20M;
    
    # Static files
    location /static/ {
        alias /var/www/attendance_system/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/attendance_system/media/;
        expires 7d;
    }
    
    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/attendance_system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔒 STEP 11: SETUP SSL (HTTPS) - Optional but Recommended

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your_domain.com -d www.your_domain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

---

## 🔥 STEP 12: SETUP FIREWALL

```bash
# Enable UFW
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

---

## ✅ STEP 13: VERIFY DEPLOYMENT

```bash
# Check Gunicorn status
sudo supervisorctl status attendance_system

# Check Nginx status
sudo systemctl status nginx

# Check logs
tail -f /var/www/attendance_system/logs/gunicorn_error.log
tail -f /var/www/attendance_system/logs/supervisor.log
tail -f /var/log/nginx/error.log

# Test application
curl http://your_vps_ip
curl http://your_domain.com
```

---

## 🔄 STEP 14: DEPLOYMENT COMMANDS (For Updates)

Create deployment script:

```bash
nano /var/www/attendance_system/deploy.sh
```

Add:

```bash
#!/bin/bash

echo "🚀 Starting deployment..."

# Navigate to project
cd /var/www/attendance_system

# Activate virtual environment
source venv/bin/activate

# Pull latest code (if using git)
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart Gunicorn
sudo supervisorctl restart attendance_system

# Restart Nginx
sudo systemctl restart nginx

echo "✅ Deployment completed!"
```

Make executable:

```bash
chmod +x /var/www/attendance_system/deploy.sh
```

Run deployment:

```bash
./deploy.sh
```

---

## 📊 MONITORING & MAINTENANCE

### Check Application Status:
```bash
sudo supervisorctl status
sudo systemctl status nginx
```

### View Logs:
```bash
# Application logs
tail -f /var/www/attendance_system/logs/gunicorn_error.log

# Nginx logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# Supervisor logs
tail -f /var/www/attendance_system/logs/supervisor.log
```

### Restart Services:
```bash
# Restart Gunicorn
sudo supervisorctl restart attendance_system

# Restart Nginx
sudo systemctl restart nginx

# Restart all
sudo supervisorctl restart all
sudo systemctl restart nginx
```

### Database Backup:
```bash
# Backup database
sudo -u postgres pg_dump attendance_db > backup_$(date +%Y%m%d).sql

# Restore database
sudo -u postgres psql attendance_db < backup_20260226.sql
```

---

## 🐛 TROUBLESHOOTING

### Issue: 502 Bad Gateway
```bash
# Check Gunicorn is running
sudo supervisorctl status attendance_system

# Check logs
tail -f /var/www/attendance_system/logs/gunicorn_error.log

# Restart
sudo supervisorctl restart attendance_system
```

### Issue: Static files not loading
```bash
# Collect static again
python manage.py collectstatic --noinput

# Check permissions
sudo chown -R www-data:www-data /var/www/attendance_system/staticfiles
sudo chmod -R 755 /var/www/attendance_system/staticfiles
```

### Issue: Database connection error
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -l

# Test connection
sudo -u postgres psql attendance_db
```

### Issue: Permission denied
```bash
# Fix permissions
sudo chown -R www-data:www-data /var/www/attendance_system
sudo chmod -R 755 /var/www/attendance_system
```

---

## 📱 ACCESS YOUR APPLICATION

After successful deployment:

- **HTTP:** http://your_vps_ip or http://your_domain.com
- **HTTPS:** https://your_domain.com (if SSL configured)

**Admin Login:** http://your_domain.com/admin/login/  
**Employee Login:** http://your_domain.com/employee/login/

---

## 🔐 SECURITY CHECKLIST

- ✅ Change DEBUG to False
- ✅ Set strong SECRET_KEY
- ✅ Configure ALLOWED_HOSTS
- ✅ Use PostgreSQL (not SQLite)
- ✅ Setup SSL/HTTPS
- ✅ Enable firewall (UFW)
- ✅ Use strong database password
- ✅ Regular backups
- ✅ Keep system updated
- ✅ Monitor logs regularly

---

## 📞 SUPPORT

For issues:
1. Check logs first
2. Verify all services are running
3. Check file permissions
4. Review configuration files

---

**Deployment Status:** ✅ READY FOR PRODUCTION

**Last Updated:** February 26, 2026
