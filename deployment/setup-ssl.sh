#!/bin/bash

# SSL Setup Script for Alkana Dashboard
# Configures Let's Encrypt SSL certificates with auto-renewal

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: sudo $0 <domain> <email>"
    echo "Example: sudo $0 dashboard.alkana.com admin@alkana.com"
    exit 1
fi

DOMAIN=$1
EMAIL=$2

echo "=========================================="
echo "Setting up SSL for $DOMAIN"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root or with sudo"
    exit 1
fi

# Create directories
mkdir -p /var/www/certbot
mkdir -p ~/alkana-dashboard/nginx/ssl

# Obtain certificate
echo "📜 Obtaining SSL certificate..."
certbot certonly \
    --standalone \
    --preferred-challenges http \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    --non-interactive

# Copy certificates to nginx directory
echo "📋 Copying certificates..."
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ~/alkana-dashboard/nginx/ssl/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ~/alkana-dashboard/nginx/ssl/
chmod 644 ~/alkana-dashboard/nginx/ssl/fullchain.pem
chmod 600 ~/alkana-dashboard/nginx/ssl/privkey.pem
chown -R deploy:deploy ~/alkana-dashboard/nginx/ssl

# Setup auto-renewal
echo "🔄 Setting up auto-renewal..."
cat > /etc/cron.d/certbot-renewal << 'EOF'
# Renew Let's Encrypt certificates twice daily
0 0,12 * * * root certbot renew --quiet --deploy-hook "cd /home/deploy/alkana-dashboard && docker compose -f docker-compose.prod.yml restart frontend"
EOF

chmod 644 /etc/cron.d/certbot-renewal

# Test renewal
echo "🧪 Testing certificate renewal..."
certbot renew --dry-run

echo ""
echo "=========================================="
echo "✅ SSL setup completed!"
echo "=========================================="
echo "Certificate location: /etc/letsencrypt/live/$DOMAIN/"
echo "Renewal check: certbot certificates"
echo "Auto-renewal configured via cron"
echo ""
echo "Update nginx/nginx.prod.conf with:"
echo "  server_name $DOMAIN;"
echo ""
