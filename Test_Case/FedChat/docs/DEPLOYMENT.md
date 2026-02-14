# Deployment Guide

Complete guide for deploying FedChat System in a FISMA Moderate federal environment.

## Prerequisites

### Hardware Requirements

**Minimum**:
- CPU: 8 cores
- RAM: 16GB
- Storage: 100GB SSD
- Network: 1 Gbps

**Recommended** (with local LLM):
- CPU: 16+ cores
- RAM: 64GB
- Storage: 500GB NVMe SSD
- GPU: NVIDIA RTX 4090 or A100 (24GB+ VRAM)
- Network: 10 Gbps

### Software Requirements

- Docker 24.0+
- Docker Compose 2.20+
- Git 2.30+
- OpenSSL 1.1.1+
- (Optional) NVIDIA Container Toolkit for GPU support

### Operating System

**Supported**:
- Red Hat Enterprise Linux 8/9
- Ubuntu 20.04/22.04 LTS
- Rocky Linux 8/9

## Pre-Deployment

### 1. System Preparation

```bash
# Update system
sudo yum update -y  # RHEL/Rocky
sudo apt update && sudo apt upgrade -y  # Ubuntu

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 2. GPU Setup (Optional)

For local LLM inference with GPU:

```bash
# Install NVIDIA drivers
sudo yum install nvidia-driver  # RHEL
sudo apt install nvidia-driver-535  # Ubuntu

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.repo | \
  sudo tee /etc/yum.repos.d/nvidia-docker.repo

sudo yum install -y nvidia-container-toolkit
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### 3. Clone Repository

```bash
# Clone to appropriate location
cd /opt
sudo git clone <your-repository-url>
cd fedchat-system

# Set ownership
sudo chown -R $USER:$USER /opt/fedchat-system
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

**Critical Settings to Change**:
```bash
# Security (MUST CHANGE)
JWT_SECRET="<generate-random-64-char-string>"
SESSION_SECRET="<generate-random-64-char-string>"
POSTGRES_PASSWORD="<strong-database-password>"
REDIS_PASSWORD="<strong-redis-password>"

# Agency Configuration
AGENCY_NAME="Department of Example"
AGENCY_PRIMARY_COLOR="#002868"

# LLM Provider
LLM_PROVIDER=local  # or azure, aws for FedRAMP

# Disable insecure features
ALLOW_REGISTRATION=false
ENABLE_API_DOCS=false
DEBUG_MODE=false
```

Generate secure secrets:
```bash
# Generate JWT_SECRET
openssl rand -hex 32

# Generate SESSION_SECRET
openssl rand -hex 32
```

## Deployment Steps

### 1. Initial Deployment

```bash
# Build and start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 2. Database Initialization

```bash
# Wait for database to be ready
docker-compose exec database pg_isready -U fedchat_user

# Verify pgvector extension
docker-compose exec database psql -U fedchat_user -d fedchat -c "SELECT * FROM pg_extension WHERE extname='vector';"

# Check tables
docker-compose exec database psql -U fedchat_user -d fedchat -c "\dt"
```

### 3. Load LLM Models (Local Provider)

```bash
# Pull Llama 3 70B model
docker-compose exec ollama ollama pull llama3:70b

# Pull embedding model
docker-compose exec ollama ollama pull nomic-embed-text

# List installed models
docker-compose exec ollama ollama list
```

### 4. Create Admin User

```bash
# Enter backend container
docker-compose exec backend python

# In Python shell:
from services.user_service import UserService
user_service = UserService()
await user_service.create_admin(
    email="admin@agency.gov",
    username="admin",
    password="ChangeThisPassword123!",
    full_name="System Administrator"
)
exit()
```

### 5. Configure TLS/SSL

#### Option A: Let's Encrypt (Internet-accessible)

```bash
# Install certbot
sudo snap install --classic certbot

# Obtain certificate
sudo certbot certonly --standalone -d fedchat.agency.gov

# Copy certificates
sudo cp /etc/letsencrypt/live/fedchat.agency.gov/fullchain.pem ./nginx/ssl/
sudo cp /etc/letsencrypt/live/fedchat.agency.gov/privkey.pem ./nginx/ssl/

# Update nginx config
nano nginx/nginx.conf
# Point to certificate paths

# Restart nginx
docker-compose restart nginx
```

#### Option B: Agency CA Certificates

```bash
# Copy certificates to nginx/ssl/
cp /path/to/agency-cert.pem ./nginx/ssl/server.crt
cp /path/to/agency-key.pem ./nginx/ssl/server.key

# Update nginx config
nano nginx/nginx.conf

# Restart nginx
docker-compose restart nginx
```

### 6. Configure SAML/SSO (Optional)

```bash
# Copy IdP certificate
cp /path/to/idp-cert.pem ./librechat/config/

# Update .env
nano .env
```

Add:
```bash
ENABLE_SAML=true
SAML_IDP_ENTITY_ID=https://idp.agency.gov/saml
SAML_IDP_SSO_URL=https://idp.agency.gov/sso
SAML_IDP_CERT_PATH=/app/config/idp-cert.pem
```

```bash
# Restart librechat
docker-compose restart librechat
```

### 7. Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/api/v1/health/detailed

# Access frontend
curl http://localhost:3000
```

## Post-Deployment

### 1. Security Hardening

```bash
# Disable unnecessary services
docker-compose stop grafana  # If not using
docker-compose stop prometheus  # If not using

# Set file permissions
chmod 600 .env
chmod 600 nginx/ssl/*.key
chmod 600 librechat/config/*.pem

# Enable firewall
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

### 2. Configure Backups

```bash
# Create backup script
cat > /opt/fedchat-system/scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/fedchat"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec -T database pg_dump -U fedchat_user fedchat | \
  gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Backup documents
tar -czf "$BACKUP_DIR/docs_backup_$DATE.tar.gz" ./documents/

# Backup configs
tar -czf "$BACKUP_DIR/config_backup_$DATE.tar.gz" \
  .env docker-compose.yml librechat/config/ guardrails/

# Cleanup old backups (keep 90 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +90 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/fedchat-system/scripts/backup.sh

# Add to cron (daily at 2 AM)
echo "0 2 * * * /opt/fedchat-system/scripts/backup.sh" | sudo crontab -
```

### 3. Configure Monitoring

```bash
# Start monitoring services
docker-compose up -d prometheus grafana

# Import Grafana dashboards
# Access Grafana at http://localhost:3001
# Default credentials in .env
# Import dashboards from monitoring/grafana/dashboards/
```

### 4. Configure Log Forwarding

Forward logs to SIEM:

```bash
# Install filebeat or similar
sudo yum install filebeat

# Configure
sudo nano /etc/filebeat/filebeat.yml
```

Add:
```yaml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/fedchat/audit.log
    json.keys_under_root: true
    json.add_error_key: true

output.logstash:
  hosts: ["logstash.agency.gov:5044"]
```

```bash
# Start filebeat
sudo systemctl start filebeat
sudo systemctl enable filebeat
```

## Maintenance

### Updates

```bash
# Pull latest code
cd /opt/fedchat-system
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Verify
docker-compose ps
docker-compose logs -f backend
```

### Database Maintenance

```bash
# Vacuum database
docker-compose exec database psql -U fedchat_user -d fedchat -c "VACUUM ANALYZE;"

# Reindex
docker-compose exec database psql -U fedchat_user -d fedchat -c "REINDEX DATABASE fedchat;"

# Check database size
docker-compose exec database psql -U fedchat_user -d fedchat -c "SELECT pg_size_pretty(pg_database_size('fedchat'));"
```

### Log Rotation

```bash
# Configure logrotate
sudo nano /etc/logrotate.d/fedchat
```

Add:
```
/var/log/fedchat/*.log {
    daily
    rotate 365
    compress
    delaycompress
    notifempty
    create 0640 fedchat fedchat
    sharedscripts
    postrotate
        docker-compose restart backend
    endscript
}
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs backend
docker-compose logs database

# Check disk space
df -h

# Check memory
free -h

# Restart services
docker-compose restart
```

### Database Connection Errors

```bash
# Check database is running
docker-compose ps database

# Check connection
docker-compose exec backend python -c "
from sqlalchemy import create_engine
engine = create_engine('$DATABASE_URL')
conn = engine.connect()
print('Connected successfully')
"

# Reset database (CAUTION: deletes data)
docker-compose down -v
docker-compose up -d database
# Wait 30 seconds
docker-compose up -d
```

### LLM Not Responding

```bash
# Check Ollama is running
docker-compose ps ollama

# Check model is loaded
docker-compose exec ollama ollama list

# Test model
docker-compose exec ollama ollama run llama3:70b "Hello"

# Check GPU (if using)
docker-compose exec ollama nvidia-smi
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Reduce workers
nano .env
# Set WORKERS=2

# Restart
docker-compose restart backend
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend
docker-compose up -d --scale backend=3

# Add load balancer (nginx already configured)
# Update nginx.conf for multiple backends

# Scale can't be used for stateful services:
# - database (use replication instead)
# - redis (use Redis Cluster)
```

### Vertical Scaling

```bash
# Increase resources in docker-compose.yml
nano docker-compose.yml
```

Add:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

## Disaster Recovery

### Full System Restore

```bash
# 1. Install prerequisites (Docker, etc.)

# 2. Clone repository
git clone https://github.com/your-agency/fedchat-system.git
cd fedchat-system

# 3. Restore .env file
cp /backup/.env .env

# 4. Restore certificates
cp /backup/nginx/ssl/* ./nginx/ssl/

# 5. Start database only
docker-compose up -d database
sleep 30

# 6. Restore database
gunzip -c /backups/fedchat/db_backup_YYYYMMDD.sql.gz | \
  docker-compose exec -T database psql -U fedchat_user -d fedchat

# 7. Restore documents
tar -xzf /backups/fedchat/docs_backup_YYYYMMDD.tar.gz

# 8. Start all services
docker-compose up -d

# 9. Verify
docker-compose ps
curl http://localhost:8000/health
```

## Security Checklist

Before going live:

- [ ] All default passwords changed
- [ ] TLS/SSL configured and tested
- [ ] Firewall rules configured
- [ ] SAML/SSO tested (if enabled)
- [ ] Audit logging verified
- [ ] Backup tested and scheduled
- [ ] Monitoring configured
- [ ] Log forwarding to SIEM
- [ ] Security scanning completed
- [ ] Penetration testing completed
- [ ] Documentation updated
- [ ] Incident response plan in place
- [ ] Admin team trained
- [ ] ATO obtained

## Support

For deployment assistance:
- Technical Support: support@agency.gov
- Security Team: security@agency.gov
- Emergency: +1-555-AGENCY

## References

- [Main README](../README.md)
- [FISMA Compliance Guide](FISMA_COMPLIANCE.md)
- [Backend Documentation](../backend/README.md)
- [LibreChat Documentation](../librechat/README.md)
