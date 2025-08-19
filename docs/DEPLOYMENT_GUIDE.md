# TODOIT MCP - Production Deployment Guide

**Professional deployment guide for TODOIT MCP in production environments**

---

## 📋 Table of Contents

- [Pre-Deployment Checklist](#-pre-deployment-checklist)
- [Environment Setup](#-environment-setup)
- [Installation Methods](#-installation-methods)
- [Configuration](#-configuration)
- [Security Hardening](#-security-hardening)
- [Performance Optimization](#-performance-optimization)
- [Monitoring & Logging](#-monitoring--logging)
- [Backup & Recovery](#-backup--recovery)
- [Troubleshooting](#-troubleshooting)

---

## ✅ Pre-Deployment Checklist

### System Requirements
- [ ] **Python 3.12+** installed and verified
- [ ] **SQLite 3.35+** with foreign key support enabled
- [ ] **Disk Space**: Minimum 1GB free space for database and logs
- [ ] **Memory**: Minimum 512MB RAM for CLI operations
- [ ] **Network**: Outbound internet access for package installation

### Security Requirements
- [ ] **User Account**: Non-root service user created
- [ ] **File Permissions**: Database directory with appropriate permissions
- [ ] **Firewall**: Only necessary ports open
- [ ] **Environment Variables**: Secrets management strategy in place

### Backup Strategy
- [ ] **Database Backup**: Automated backup solution configured
- [ ] **Configuration Backup**: Environment variables documented
- [ ] **Recovery Testing**: Restore procedures tested

---

## 🏗️ Environment Setup

### Create Service User
```bash
# Create dedicated user for TODOIT
sudo useradd -m -s /bin/bash todoit
sudo usermod -a -G users todoit

# Create application directories
sudo mkdir -p /var/lib/todoit/{data,logs,backups}
sudo mkdir -p /etc/todoit
sudo chown -R todoit:todoit /var/lib/todoit
sudo chown -R todoit:todoit /etc/todoit
```

### Directory Structure
```
/var/lib/todoit/
├── data/
│   ├── production.db         # Main production database
│   └── production.db.backup  # Latest backup
├── logs/
│   ├── todoit.log           # Application logs
│   └── audit.log            # Audit trail
├── backups/
│   ├── daily/               # Daily backups
│   └── weekly/              # Weekly backups
└── config/
    └── .env                 # Environment configuration
```

---

## 📦 Installation Methods

### Method 1: PyPI Installation (Recommended)

```bash
# Switch to service user
sudo su - todoit

# Create virtual environment
python -m venv /var/lib/todoit/venv
source /var/lib/todoit/venv/bin/activate

# Install TODOIT MCP
pip install todoit-mcp

# Verify installation
todoit --version
```

### Method 2: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.12-slim

# Create user
RUN useradd -m -s /bin/bash todoit

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .
RUN chown -R todoit:todoit /app

# Switch to service user
USER todoit

# Expose ports (if needed for MCP server)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD todoit list all --format json || exit 1

# Start command
CMD ["python", "-m", "interfaces.mcp_server"]
```

```bash
# Build and run
docker build -t todoit-mcp:latest .
docker run -d \
  --name todoit-production \
  -v /var/lib/todoit/data:/app/data \
  -v /var/lib/todoit/logs:/app/logs \
  -e TODOIT_DB_PATH=/app/data/production.db \
  todoit-mcp:latest
```

### Method 3: System Package (Advanced)

```bash
# Create systemd service file
sudo tee /etc/systemd/system/todoit-mcp.service > /dev/null <<EOF
[Unit]
Description=TODOIT MCP Server
After=network.target

[Service]
Type=simple
User=todoit
Group=todoit
WorkingDirectory=/var/lib/todoit
Environment=TODOIT_DB_PATH=/var/lib/todoit/data/production.db
Environment=TODOIT_MCP_TOOLS_LEVEL=standard
Environment=TODOIT_OUTPUT_FORMAT=json
ExecStart=/var/lib/todoit/venv/bin/python -m interfaces.mcp_server
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=todoit-mcp

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable todoit-mcp
sudo systemctl start todoit-mcp
```

---

## ⚙️ Configuration

### Environment Variables

Create `/etc/todoit/production.env`:
```bash
# Database Configuration
TODOIT_DB_PATH=/var/lib/todoit/data/production.db

# MCP Configuration
TODOIT_MCP_TOOLS_LEVEL=standard

# Environment Isolation
TODOIT_FORCE_TAGS=production

# Output Configuration
TODOIT_OUTPUT_FORMAT=json

# Performance Tuning
TODOIT_MAX_CONNECTIONS=20
TODOIT_QUERY_TIMEOUT=30

# Security
TODOIT_ENABLE_AUDIT_LOG=true
TODOIT_LOG_LEVEL=INFO
```

### Load Configuration
```bash
# Method 1: Source in shell
source /etc/todoit/production.env

# Method 2: systemd environment file
# Add to service file: EnvironmentFile=/etc/todoit/production.env

# Method 3: Docker environment file
docker run --env-file /etc/todoit/production.env todoit-mcp
```

### Database Initialization

```bash
# Initialize production database
sudo su - todoit
source /var/lib/todoit/venv/bin/activate

# Create database with proper permissions
TODOIT_DB_PATH=/var/lib/todoit/data/production.db python -c "
from core.manager import TodoManager
manager = TodoManager()
print('Database initialized successfully')
"

# Verify database
sqlite3 /var/lib/todoit/data/production.db ".tables"
```

---

## 🔒 Security Hardening

### File Permissions
```bash
# Secure database file
chmod 660 /var/lib/todoit/data/production.db
chown todoit:todoit /var/lib/todoit/data/production.db

# Secure configuration
chmod 640 /etc/todoit/production.env
chown root:todoit /etc/todoit/production.env

# Secure directories
chmod 750 /var/lib/todoit/data
chmod 750 /var/lib/todoit/logs
chmod 755 /var/lib/todoit/backups
```

### Database Security
```sql
-- Enable foreign key constraints (critical)
PRAGMA foreign_keys = ON;

-- Set secure permissions on database file
-- (handled by file system permissions above)

-- Disable unsafe features
PRAGMA trusted_schema = OFF;
```

### Input Validation
```python
# TODOIT includes comprehensive input validation via Pydantic
# All user inputs are validated before reaching the database
# SQL injection protection through parameterized queries
# Path traversal protection in import/export functions
```

### Network Security
```bash
# If running MCP server as network service
# Bind to localhost only
export MCP_BIND_HOST=127.0.0.1
export MCP_BIND_PORT=8000

# Use firewall to restrict access
sudo ufw allow from 127.0.0.1 to any port 8000
sudo ufw deny 8000
```

---

## ⚡ Performance Optimization

### Database Optimization
```sql
-- Run these periodically on production database
PRAGMA optimize;
PRAGMA wal_checkpoint(TRUNCATE);
VACUUM;
REINDEX;

-- Check database statistics
PRAGMA table_info(todo_items);
PRAGMA index_list(todo_items);
```

### Application Tuning
```bash
# Environment variables for performance
export TODOIT_MCP_TOOLS_LEVEL=standard  # Balance features vs performance
export TODOIT_CACHE_SIZE=10000          # SQLite cache size
export TODOIT_BATCH_SIZE=100            # Bulk operation batch size
```

### Monitoring Performance
```bash
# Create performance monitoring script
cat > /var/lib/todoit/monitor_performance.py << 'EOF'
#!/usr/bin/env python3
import time
import sqlite3
from pathlib import Path

def check_database_performance():
    db_path = "/var/lib/todoit/data/production.db"
    
    # Check database size
    size_mb = Path(db_path).stat().st_size / (1024 * 1024)
    
    # Check query performance
    conn = sqlite3.connect(db_path)
    start_time = time.time()
    
    cursor = conn.execute("SELECT COUNT(*) FROM todo_items")
    item_count = cursor.fetchone()[0]
    
    query_time = time.time() - start_time
    
    print(f"Database size: {size_mb:.2f} MB")
    print(f"Total items: {item_count}")
    print(f"Query time: {query_time:.3f} seconds")
    
    # Performance thresholds
    if size_mb > 500:
        print("WARNING: Database size > 500MB, consider archiving")
    if query_time > 1.0:
        print("WARNING: Query time > 1s, consider optimization")
    
    conn.close()

if __name__ == "__main__":
    check_database_performance()
EOF

chmod +x /var/lib/todoit/monitor_performance.py
```

---

## 📊 Monitoring & Logging

### Application Logging
```python
# Configure logging in production
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/lib/todoit/logs/todoit.log'),
        logging.StreamHandler()
    ]
)
```

### Health Check Script
```bash
cat > /var/lib/todoit/health_check.py << 'EOF'
#!/usr/bin/env python3
import sys
import json
from pathlib import Path

def health_check():
    try:
        # Check database exists and is readable
        db_path = Path("/var/lib/todoit/data/production.db")
        if not db_path.exists():
            return {"status": "CRITICAL", "message": "Database file missing"}
        
        # Check database is writable
        if not db_path.stat().st_mode & 0o200:
            return {"status": "CRITICAL", "message": "Database not writable"}
        
        # Test basic functionality
        from core.manager import TodoManager
        manager = TodoManager(str(db_path))
        
        # Quick test query
        lists = manager.get_all_lists()
        
        return {
            "status": "OK", 
            "message": f"System healthy, {len(lists)} lists"
        }
        
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

if __name__ == "__main__":
    result = health_check()
    print(json.dumps(result))
    sys.exit(0 if result["status"] == "OK" else 1)
EOF

chmod +x /var/lib/todoit/health_check.py
```

### Cron Jobs for Monitoring
```bash
# Add to crontab for todoit user
crontab -u todoit -e

# Add these lines:
# Health check every 5 minutes
*/5 * * * * /var/lib/todoit/venv/bin/python /var/lib/todoit/health_check.py >> /var/lib/todoit/logs/health.log 2>&1

# Performance monitoring daily
0 6 * * * /var/lib/todoit/venv/bin/python /var/lib/todoit/monitor_performance.py >> /var/lib/todoit/logs/performance.log 2>&1

# Database maintenance weekly
0 2 * * 0 sqlite3 /var/lib/todoit/data/production.db "VACUUM; REINDEX; PRAGMA optimize;" >> /var/lib/todoit/logs/maintenance.log 2>&1
```

---

## 💾 Backup & Recovery

### Automated Backup Script
```bash
cat > /var/lib/todoit/backup.sh << 'EOF'
#!/bin/bash
set -e

DB_PATH="/var/lib/todoit/data/production.db"
BACKUP_DIR="/var/lib/todoit/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Daily backup
DAILY_BACKUP="$BACKUP_DIR/daily/production_$DATE.db"
mkdir -p "$BACKUP_DIR/daily"

# Create backup using SQLite backup API (safe for live database)
sqlite3 "$DB_PATH" ".backup '$DAILY_BACKUP'"

# Compress backup
gzip "$DAILY_BACKUP"

# Keep last 7 daily backups
find "$BACKUP_DIR/daily" -name "*.gz" -mtime +7 -delete

# Weekly backup (Sundays)
if [ "$(date +%w)" -eq 0 ]; then
    WEEKLY_BACKUP="$BACKUP_DIR/weekly/production_weekly_$DATE.db.gz"
    mkdir -p "$BACKUP_DIR/weekly"
    cp "$DAILY_BACKUP.gz" "$WEEKLY_BACKUP"
    
    # Keep last 4 weekly backups
    find "$BACKUP_DIR/weekly" -name "*.gz" -mtime +28 -delete
fi

echo "Backup completed: $DAILY_BACKUP.gz"
EOF

chmod +x /var/lib/todoit/backup.sh

# Add to crontab
crontab -u todoit -e
# Add: 0 1 * * * /var/lib/todoit/backup.sh >> /var/lib/todoit/logs/backup.log 2>&1
```

### Recovery Procedures
```bash
# Emergency recovery script
cat > /var/lib/todoit/recover.sh << 'EOF'
#!/bin/bash
set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file.gz>"
    echo "Available backups:"
    ls -la /var/lib/todoit/backups/daily/
    exit 1
fi

BACKUP_FILE="$1"
DB_PATH="/var/lib/todoit/data/production.db"
RECOVERY_DB="/tmp/recovery_$(date +%s).db"

echo "Starting recovery from $BACKUP_FILE..."

# Stop service
sudo systemctl stop todoit-mcp

# Backup current database
cp "$DB_PATH" "$DB_PATH.pre_recovery_$(date +%s)"

# Extract and restore backup
gunzip -c "$BACKUP_FILE" > "$RECOVERY_DB"

# Verify backup integrity
sqlite3 "$RECOVERY_DB" "PRAGMA integrity_check;"

# Move recovered database into place
mv "$RECOVERY_DB" "$DB_PATH"
chown todoit:todoit "$DB_PATH"
chmod 660 "$DB_PATH"

# Start service
sudo systemctl start todoit-mcp

echo "Recovery completed successfully"
EOF

chmod +x /var/lib/todoit/recover.sh
```

---

## 🔧 Troubleshooting

### Common Issues

#### Database Locked
```bash
# Symptoms: "database is locked" errors
# Cause: Multiple processes accessing database

# Check for multiple processes
ps aux | grep todoit
lsof /var/lib/todoit/data/production.db

# Solution: Kill processes and restart
sudo systemctl restart todoit-mcp
```

#### Performance Degradation
```bash
# Check database size and fragmentation
sqlite3 /var/lib/todoit/data/production.db "
SELECT 
    page_count * page_size as database_size,
    freelist_count * page_size as free_space
FROM pragma_page_count(), pragma_freelist_count(), pragma_page_size();"

# Optimize database
sqlite3 /var/lib/todoit/data/production.db "VACUUM; REINDEX;"
```

#### Memory Issues
```bash
# Monitor memory usage
ps aux | grep todoit
sudo systemctl status todoit-mcp

# Adjust memory limits if needed
sudo systemctl edit todoit-mcp
# Add:
# [Service]
# MemoryLimit=1G
```

### Log Analysis
```bash
# Check application logs
tail -f /var/lib/todoit/logs/todoit.log

# Search for errors
grep -i error /var/lib/todoit/logs/todoit.log

# Check system logs
journalctl -u todoit-mcp -f
```

### Emergency Procedures

#### Service Won't Start
```bash
# Check service status
sudo systemctl status todoit-mcp

# Check configuration
sudo -u todoit bash
source /var/lib/todoit/venv/bin/activate
python -c "from core.manager import TodoManager; print('Config OK')"

# Manual start for debugging
sudo -u todoit /var/lib/todoit/venv/bin/python -m interfaces.mcp_server
```

#### Data Corruption
```bash
# Check database integrity
sqlite3 /var/lib/todoit/data/production.db "PRAGMA integrity_check;"

# If corrupted, restore from backup
/var/lib/todoit/recover.sh /var/lib/todoit/backups/daily/production_YYYYMMDD_HHMMSS.db.gz
```

---

## 📞 Support

### Getting Help
1. **Check logs** first for specific error messages
2. **Run health check** to identify system issues
3. **Review documentation** for configuration options
4. **Search GitHub issues** for similar problems
5. **Create detailed bug report** with environment details

### Escalation Path
1. **Level 1**: Check documentation and logs
2. **Level 2**: Community support via GitHub issues
3. **Level 3**: Professional support (if available)

---

## ✅ Post-Deployment Validation

### Functional Testing
```bash
# Test basic CLI functionality
sudo -u todoit bash
source /var/lib/todoit/venv/bin/activate

# Create test list
todoit list create --list "deployment-test" --title "Deployment Test"

# Add test item
todoit item add --list "deployment-test" --item "test1" --title "Test deployment"

# Check status
todoit list show --list "deployment-test"

# Clean up
todoit list delete --list "deployment-test" --force
```

### Performance Baseline
```bash
# Run performance check
/var/lib/todoit/monitor_performance.py

# Load testing (if applicable)
# Create sample data and measure response times
```

### Security Verification
```bash
# Check file permissions
ls -la /var/lib/todoit/data/
ls -la /etc/todoit/

# Verify service user
id todoit
groups todoit

# Check network exposure
netstat -tlnp | grep todoit
```

---

**✅ Deployment Complete!**

Your TODOIT MCP installation is now production-ready with:
- ✅ Secure configuration
- ✅ Automated backups
- ✅ Performance monitoring
- ✅ Health checks
- ✅ Recovery procedures

*Remember to regularly review logs and perform maintenance tasks as scheduled.*