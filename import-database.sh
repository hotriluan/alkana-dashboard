#!/bin/bash
#
# Import Database to Production Server
# Usage: sudo ./import-database.sh /path/to/backup.sql.gz
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Import Database to Production${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Check if backup file provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: No backup file specified${NC}"
    echo -e "Usage: sudo ./import-database.sh /path/to/backup.sql.gz"
    exit 1
fi

BACKUP_FILE=$1

# Check if file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}Backup file: $BACKUP_FILE${NC}"
echo -e "${YELLOW}Size: $(du -h $BACKUP_FILE | cut -f1)${NC}\n"

# Confirm before proceeding
read -p "⚠️  This will REPLACE all data in the database. Continue? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo -e "${RED}Import cancelled${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Stopping backend service...${NC}"
docker compose stop backend
echo -e "${GREEN}✓ Backend stopped${NC}\n"

echo -e "${YELLOW}Step 2: Creating backup of current database...${NC}"
CURRENT_BACKUP="/var/backups/alkana/before_import_$(date +%Y%m%d_%H%M%S).sql.gz"
mkdir -p /var/backups/alkana
docker compose exec -T postgres pg_dump -U postgres alkana_dashboard | gzip > "$CURRENT_BACKUP"
echo -e "${GREEN}✓ Current data backed up to: $CURRENT_BACKUP${NC}\n"

echo -e "${YELLOW}Step 3: Dropping and recreating database...${NC}"
docker compose exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS alkana_dashboard;"
docker compose exec -T postgres psql -U postgres -c "CREATE DATABASE alkana_dashboard;"
echo -e "${GREEN}✓ Database recreated${NC}\n"

echo -e "${YELLOW}Step 4: Importing data (this may take a while)...${NC}"
gunzip < "$BACKUP_FILE" | docker compose exec -T postgres psql -U postgres alkana_dashboard
echo -e "${GREEN}✓ Data imported${NC}\n"

echo -e "${YELLOW}Step 5: Restarting backend service...${NC}"
docker compose start backend
sleep 5
echo -e "${GREEN}✓ Backend restarted${NC}\n"

echo -e "${YELLOW}Step 6: Verifying database...${NC}"
TABLE_COUNT=$(docker compose exec -T postgres psql -U postgres -d alkana_dashboard -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")
echo -e "${GREEN}✓ Tables count: $TABLE_COUNT${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Database Import Complete!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "${YELLOW}Verification:${NC}"
echo -e "  Check backend health: curl http://localhost:8000/api/health"
echo -e "  View logs: docker compose logs -f backend"
echo -e "  Access dashboard: http://your-server-ip"

echo -e "\n${YELLOW}Rollback (if needed):${NC}"
echo -e "  Restore from backup: sudo ./import-database.sh $CURRENT_BACKUP"

echo -e "\n${GREEN}Import completed successfully!${NC}\n"
