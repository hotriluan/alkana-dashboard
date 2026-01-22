#!/bin/bash
#
# Alkana Dashboard - Ubuntu 24 Deployment Script
# 
# Usage: sudo ./deploy.sh
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Alkana Dashboard - Ubuntu 24 Deployment${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (sudo ./deploy.sh)${NC}"
    exit 1
fi

# Variables
APP_DIR="/opt/alkana-dashboard"
GITHUB_REPO="https://github.com/hotriluan/alkana-dashboard.git"  # Update with your repo
BRANCH="main"

# Step 1: Install Docker
echo -e "\n${YELLOW}[1/8] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release
    
    # Add Docker's official GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    
    # Set up repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    echo -e "${GREEN}✓ Docker installed${NC}"
else
    echo -e "${GREEN}✓ Docker already installed${NC}"
fi

# Step 2: Install Git
echo -e "\n${YELLOW}[2/8] Installing Git...${NC}"
if ! command -v git &> /dev/null; then
    apt-get install -y git
    echo -e "${GREEN}✓ Git installed${NC}"
else
    echo -e "${GREEN}✓ Git already installed${NC}"
fi

# Step 3: Clone repository
echo -e "\n${YELLOW}[3/8] Cloning repository...${NC}"
if [ -d "$APP_DIR" ]; then
    echo -e "${YELLOW}Directory exists. Pulling latest changes...${NC}"
    cd $APP_DIR
    git pull origin $BRANCH
else
    git clone -b $BRANCH $GITHUB_REPO $APP_DIR
    cd $APP_DIR
fi
echo -e "${GREEN}✓ Repository ready${NC}"

# Step 4: Configure environment
echo -e "\n${YELLOW}[4/8] Configuring environment...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    
    # Generate secrets
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -hex 16)
    
    # Update .env file
    sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=$DB_PASSWORD|g" .env
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env
    sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|g" .env
    sed -i "s|ENVIRONMENT=.*|ENVIRONMENT=production|g" .env
    sed -i "s|DEBUG=.*|DEBUG=false|g" .env
    
    echo -e "${GREEN}✓ Environment configured${NC}"
    echo -e "${YELLOW}⚠ Database password: $DB_PASSWORD${NC}"
    echo -e "${YELLOW}⚠ Please save this password securely!${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Step 5: Create data directory
echo -e "\n${YELLOW}[5/8] Creating data directories...${NC}"
mkdir -p $APP_DIR/demodata
mkdir -p $APP_DIR/logs
chmod -R 755 $APP_DIR/demodata
echo -e "${GREEN}✓ Directories created${NC}"

# Step 6: Build Docker images
echo -e "\n${YELLOW}[6/8] Building Docker images (this may take a few minutes)...${NC}"
docker compose build
echo -e "${GREEN}✓ Images built${NC}"

# Step 7: Start services
echo -e "\n${YELLOW}[7/8] Starting services...${NC}"
docker compose down 2>/dev/null || true
docker compose up -d
echo -e "${GREEN}✓ Services started${NC}"

# Step 8: Initialize database
echo -e "\n${YELLOW}[8/8] Waiting for database to be ready...${NC}"
sleep 10

echo -e "\n${YELLOW}Initializing database schema...${NC}"
docker compose exec -T backend python -m src.main init || echo -e "${YELLOW}Database already initialized${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Show status
docker compose ps

echo -e "\n${GREEN}Services:${NC}"
echo -e "  Frontend: http://$(hostname -I | awk '{print $1}'):80"
echo -e "  Backend API: http://$(hostname -I | awk '{print $1}'):8000"
echo -e "  API Docs: http://$(hostname -I | awk '{print $1}'):8000/docs"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "  1. Upload SAP Excel files to: $APP_DIR/demodata/"
echo -e "  2. Load data: docker compose exec backend python -m src.main load"
echo -e "  3. Transform data: docker compose exec backend python -m src.main transform"
echo -e "  4. Access dashboard at: http://your-server-ip"

echo -e "\n${YELLOW}Useful Commands:${NC}"
echo -e "  View logs:    docker compose logs -f"
echo -e "  Stop:         docker compose down"
echo -e "  Restart:      docker compose restart"
echo -e "  Update:       cd $APP_DIR && git pull && docker compose up -d --build"

echo -e "\n${GREEN}Deployment script completed successfully!${NC}\n"
