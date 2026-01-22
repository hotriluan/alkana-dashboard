#!/bin/bash
#
# Export Database from Development Machine
# Usage: ./export-database.sh
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Export Database from Development${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Configuration
BACKUP_DIR="./database-exports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="alkana_db_${TIMESTAMP}.sql.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

echo -e "${YELLOW}Exporting database...${NC}"

# Check if using Docker or local PostgreSQL
if docker compose ps postgres &> /dev/null; then
    echo -e "${GREEN}Using Docker Compose${NC}"
    
    # Export from Docker container
    docker compose exec -T postgres pg_dump -U postgres alkana_dashboard | gzip > "$BACKUP_DIR/$BACKUP_FILE"
    
elif command -v psql &> /dev/null; then
    echo -e "${GREEN}Using local PostgreSQL${NC}"
    
    # Export from local PostgreSQL
    # Update credentials if needed
    PGPASSWORD=password123 pg_dump -h localhost -U postgres -d alkana_dashboard | gzip > "$BACKUP_DIR/$BACKUP_FILE"
    
else
    echo -e "${RED}PostgreSQL not found!${NC}"
    exit 1
fi

# Get file size
FILE_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)

echo -e "\n${GREEN}✓ Database exported successfully!${NC}"
echo -e "  File: $BACKUP_DIR/$BACKUP_FILE"
echo -e "  Size: $FILE_SIZE"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "  1. Transfer to production server:"
echo -e "     scp $BACKUP_DIR/$BACKUP_FILE user@production-server:/tmp/"
echo -e "\n  2. On production server, run:"
echo -e "     cd /opt/alkana-dashboard"
echo -e "     sudo ./import-database.sh /tmp/$BACKUP_FILE"

echo -e "\n${GREEN}Export completed!${NC}\n"
