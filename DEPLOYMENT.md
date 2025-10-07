# Deployment Guide

This guide covers deploying the E-Modal Management System to production.

## Pre-Deployment Checklist

### Security
- [ ] Change `SECRET_KEY` in `.env` to a strong random value
- [ ] Change `ADMIN_SECRET_KEY` in `.env` to a strong random value
- [ ] Set `DEBUG=False` in `.env`
- [ ] Use strong database passwords
- [ ] Review and restrict database access
- [ ] Enable PostgreSQL SSL connections
- [ ] Set up firewall rules

### Configuration
- [ ] Update `DATABASE_URL` with production database
- [ ] Configure `EMODAL_API_URL` for production
- [ ] Set appropriate `STORAGE_PATH`
- [ ] Configure log rotation settings
- [ ] Set up monitoring and alerting

### Infrastructure
- [ ] Provision production server
- [ ] Install PostgreSQL
- [ ] Set up backup strategy
- [ ] Configure SSL certificates
- [ ] Set up reverse proxy (nginx)

## Deployment Options

### Option 1: Traditional Server Deployment

#### 1. Server Setup (Ubuntu/Debian)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+
sudo apt install python3.9 python3.9-venv python3-pip -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install nginx (optional, for reverse proxy)
sudo apt install nginx -y
```

#### 2. Create Application User

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash emodal
sudo su - emodal
```

#### 3. Deploy Application

```bash
# Clone or copy application files
cd /home/emodal
# Copy your files here

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install production WSGI server
pip install gunicorn
```

#### 4. Configure Database

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE emodal_db;
CREATE USER emodal_user WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE emodal_db TO emodal_user;
\q
```

#### 5. Configure Environment

```bash
# Edit .env file
nano .env

# Set production values:
SECRET_KEY=<generate-random-key>
DEBUG=False
DATABASE_URL=postgresql://emodal_user:strong_password_here@localhost:5432/emodal_db
EMODAL_API_URL=http://your-emodal-api:5010
ADMIN_SECRET_KEY=<generate-random-key>
```

#### 6. Initialize Database

```bash
source venv/bin/activate
flask db upgrade
```

#### 7. Create Systemd Service

Create `/etc/systemd/system/emodal.service`:

```ini
[Unit]
Description=E-Modal Management System
After=network.target postgresql.service

[Service]
Type=notify
User=emodal
Group=emodal
WorkingDirectory=/home/emodal
Environment="PATH=/home/emodal/venv/bin"
ExecStart=/home/emodal/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 --timeout 300 app:create_app()
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable emodal
sudo systemctl start emodal
sudo systemctl status emodal
```

#### 8. Configure Nginx (Optional)

Create `/etc/nginx/sites-available/emodal`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # Logging
    access_log /var/log/nginx/emodal_access.log;
    error_log /var/log/nginx/emodal_error.log;

    # Proxy settings
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings for long-running queries
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # File upload size limit
    client_max_body_size 100M;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/emodal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Option 2: Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p storage/users logs

# Expose port
EXPOSE 5000

# Run migrations and start server
CMD ["sh", "-c", "flask db upgrade && gunicorn -w 4 -b 0.0.0.0:5000 --timeout 300 'app:create_app()'"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: emodal_db
      POSTGRES_USER: emodal_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    networks:
      - emodal-network

  app:
    build: .
    environment:
      SECRET_KEY: ${SECRET_KEY}
      DEBUG: "False"
      DATABASE_URL: postgresql://emodal_user:${DB_PASSWORD}@postgres:5432/emodal_db
      EMODAL_API_URL: ${EMODAL_API_URL}
      ADMIN_SECRET_KEY: ${ADMIN_SECRET_KEY}
      STORAGE_PATH: /app/storage
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
    ports:
      - "5000:5000"
    depends_on:
      - postgres
    restart: always
    networks:
      - emodal-network

volumes:
  postgres_data:

networks:
  emodal-network:
    driver: bridge
```

#### 3. Create .env.docker

```env
DB_PASSWORD=your_db_password
SECRET_KEY=your_secret_key
ADMIN_SECRET_KEY=your_admin_key
EMODAL_API_URL=http://emodal-api:5010
```

#### 4. Deploy with Docker

```bash
# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f app

# Stop
docker-compose down
```

## Post-Deployment Tasks

### 1. Create Admin User

```bash
curl -X POST https://your-domain.com/admin/users \
  -H "X-Admin-Key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Admin User",
    "username": "admin",
    "password": "strong_password",
    "emodal_username": "your_emodal_username",
    "emodal_password": "your_emodal_password",
    "emodal_captcha_key": "your_captcha_key"
  }'
```

### 2. Test System

```bash
# Health check
curl https://your-domain.com/health

# Test authentication
curl https://your-domain.com/queries \
  -H "Authorization: Bearer your-user-token"
```

### 3. Set Up Monitoring

#### Application Monitoring

Install and configure monitoring tools:
- **Prometheus** for metrics
- **Grafana** for visualization
- **Sentry** for error tracking

#### System Monitoring

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Monitor service
sudo systemctl status emodal
sudo journalctl -u emodal -f
```

#### Log Monitoring

```bash
# Monitor application logs
tail -f /home/emodal/logs/app.log

# Monitor nginx logs (if using)
tail -f /var/log/nginx/emodal_access.log
tail -f /var/log/nginx/emodal_error.log
```

### 4. Configure Backups

#### Database Backup Script

Create `/home/emodal/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/home/emodal/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_NAME="emodal_db"
DB_USER="emodal_user"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/db_$TIMESTAMP.sql

# Backup storage
tar -czf $BACKUP_DIR/storage_$TIMESTAMP.tar.gz /home/emodal/storage

# Delete backups older than 30 days
find $BACKUP_DIR -name "db_*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "storage_*.tar.gz" -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
```

```bash
# Make executable
chmod +x /home/emodal/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * /home/emodal/backup.sh >> /home/emodal/backup.log 2>&1
```

### 5. Set Up SSL/TLS

Using Let's Encrypt:

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

## Performance Tuning

### Gunicorn Workers

```bash
# Calculate optimal workers: (2 x CPU cores) + 1
# For 4 CPU cores: (2 x 4) + 1 = 9 workers

# Update systemd service
ExecStart=/home/emodal/venv/bin/gunicorn -w 9 -b 127.0.0.1:5000 --timeout 300 app:create_app()
```

### PostgreSQL Tuning

Edit `/etc/postgresql/14/main/postgresql.conf`:

```conf
# Adjust based on available RAM
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
work_mem = 16MB
max_connections = 100
```

### Application Caching

Consider adding Redis for caching:

```bash
# Install Redis
sudo apt install redis-server -y

# Update application to use Redis for session caching
pip install redis flask-caching
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u emodal -n 50 --no-pager

# Check permissions
ls -la /home/emodal

# Check port availability
sudo netstat -tulpn | grep 5000
```

### Database Connection Issues

```bash
# Test database connection
psql -U emodal_user -d emodal_db -h localhost

# Check PostgreSQL status
sudo systemctl status postgresql

# Check logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### High Memory Usage

```bash
# Check memory usage
free -h
sudo systemctl status emodal

# Reduce Gunicorn workers if needed
# Monitor with htop
htop
```

## Scaling Considerations

### Horizontal Scaling

1. **Database**: Use PostgreSQL replication
2. **Application**: Deploy multiple app instances behind load balancer
3. **Storage**: Use shared network storage (NFS, S3)
4. **Queue**: Move query execution to Celery with Redis/RabbitMQ

### Vertical Scaling

1. Increase server resources (CPU, RAM)
2. Optimize database queries
3. Add database indexes
4. Implement caching

## Security Hardening

### Firewall Configuration

```bash
# Install UFW
sudo apt install ufw -y

# Configure rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### Fail2Ban

```bash
# Install Fail2Ban
sudo apt install fail2ban -y

# Configure for nginx
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Maintenance

### Regular Tasks

1. **Weekly**: Check logs for errors
2. **Weekly**: Review backup integrity
3. **Monthly**: Update system packages
4. **Monthly**: Review and rotate API keys
5. **Quarterly**: Security audit
6. **Yearly**: SSL certificate renewal (automatic with Let's Encrypt)

### Update Application

```bash
# Stop service
sudo systemctl stop emodal

# Backup current version
cp -r /home/emodal /home/emodal_backup_$(date +%Y%m%d)

# Update code
cd /home/emodal
# Update your files

# Install new dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run migrations
flask db upgrade

# Start service
sudo systemctl start emodal

# Check status
sudo systemctl status emodal
```

## Rollback Procedure

```bash
# Stop service
sudo systemctl stop emodal

# Restore previous version
rm -rf /home/emodal
mv /home/emodal_backup_YYYYMMDD /home/emodal

# Restore database (if needed)
psql -U emodal_user emodal_db < backup_YYYYMMDD.sql

# Start service
sudo systemctl start emodal
```

## Support Contacts

- System Administrator: [email]
- Database Administrator: [email]
- Application Developer: [email]

## Additional Resources

- [Flask Production Best Practices](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Nginx Documentation](https://nginx.org/en/docs/)

---

**Remember**: Always test deployments in a staging environment before production!

