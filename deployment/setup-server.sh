#!/bin/bash

# Server Setup Script for Alkana Dashboard on Ubuntu
# This script should be run on a fresh Ubuntu 20.04/22.04 server

set -e

echo "=========================================="
echo "Alkana Dashboard - Server Setup"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root or with sudo"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install essential tools
echo "🔧 Installing essential tools..."
apt install -y \
    curl \
    wget \
    git \
    vim \
    ufw \
    fail2ban \
    htop \
    ncdu \
    postgresql-client \
    certbot \
    python3-certbot-nginx

# Create deploy user
echo "👤 Creating deploy user..."
if ! id "deploy" &>/dev/null; then
    adduser --disabled-password --gecos "" deploy
    usermod -aG sudo deploy
    echo "deploy ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/deploy
    echo "✅ User 'deploy' created"
else
    echo "✅ User 'deploy' already exists"
fi

# Install Docker
echo "🐋 Installing Docker..."
if ! command -v docker &> /dev/null; then
    # Remove old versions
    apt-get remove -y docker docker-engine docker.io containerd runc || true

    # Install dependencies
    apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # Add Docker GPG key
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
        gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    # Add Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Add deploy user to docker group
    usermod -aG docker deploy

    echo "✅ Docker installed successfully"
else
    echo "✅ Docker already installed"
fi

# Configure Docker
echo "⚙️  Configuring Docker..."
cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF

systemctl restart docker
systemctl enable docker

# Configure firewall
echo "🔥 Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "✅ Firewall configured"

# Configure fail2ban
echo "🛡️  Configuring fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Setup SSH for deploy user
echo "🔑 Setting up SSH for deploy user..."
mkdir -p /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chown -R deploy:deploy /home/deploy/.ssh

# Create project directory
echo "📁 Creating project directory..."
mkdir -p /home/deploy/alkana-dashboard
chown -R deploy:deploy /home/deploy/alkana-dashboard

# Install Docker Compose standalone (backup)
echo "🐋 Installing Docker Compose standalone..."
COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

echo ""
echo "=========================================="
echo "✅ Server setup completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Add your SSH public key to /home/deploy/.ssh/authorized_keys"
echo "2. Run as deploy user: sudo -u deploy bash -c 'ssh-keygen -t ed25519 -C deploy@alkana-server'"
echo "3. Add the deploy user's public key to GitHub as a deploy key"
echo "4. Clone repository: cd /home/deploy && git clone <repo-url> alkana-dashboard"
echo "5. Setup SSL: sudo ./deployment/setup-ssl.sh your-domain.com your-email@example.com"
echo "6. Configure environment: cd alkana-dashboard && cp .env.example .env.production"
echo "7. Deploy: docker compose -f docker-compose.prod.yml up -d"
echo ""
echo "Verify installation:"
echo "  docker --version"
echo "  docker compose version"
echo "  ufw status"
echo ""
