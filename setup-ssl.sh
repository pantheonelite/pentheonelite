#!/bin/bash

# SSL Certificate Setup Script for Pantheon Elite
# This script obtains SSL certificates for pantheonelite.ai and api.pantheonelite.ai

set -e

echo "🔐 SSL Certificate Setup for Pantheon Elite"
echo "==========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root (use sudo)${NC}"
    exit 1
fi

# Email for Let's Encrypt notifications
read -p "Enter your email for SSL certificate notifications: " EMAIL

if [ -z "$EMAIL" ]; then
    echo -e "${RED}❌ Email is required${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}📋 Prerequisites Check${NC}"
echo "---------------------"

# Check if domains are pointed to this server
echo "⚠️  Before continuing, ensure that:"
echo "  - pantheonelite.ai points to this server's IP"
echo "  - api.pantheonelite.ai points to this server's IP"
echo ""
read -p "Are both domains configured? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo -e "${RED}❌ Please configure DNS records first${NC}"
    exit 1
fi

# Create necessary directories
echo ""
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p /etc/letsencrypt
mkdir -p /var/www/certbot
mkdir -p ./nginx/logs

# Create temporary nginx configuration for initial certificate request
echo ""
echo -e "${YELLOW}📝 Creating temporary nginx configuration...${NC}"

cat > ./nginx/nginx-temp.conf << 'EOF'
worker_processes 1;

events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name pantheonelite.ai www.pantheonelite.ai api.pantheonelite.ai;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 200 'SSL setup in progress...';
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Backup original nginx.conf if exists
if [ -f ./nginx/nginx.conf ]; then
    echo -e "${YELLOW}💾 Backing up existing nginx.conf...${NC}"
    cp ./nginx/nginx.conf ./nginx/nginx.conf.backup
fi

# Use temporary config
cp ./nginx/nginx-temp.conf ./nginx/nginx.conf

# Stop any existing nginx container
echo ""
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose down nginx certbot 2>/dev/null || true

# Start nginx with temporary config
echo ""
echo -e "${YELLOW}🚀 Starting nginx for certificate verification...${NC}"
docker-compose up -d nginx

# Wait for nginx to start
sleep 3

# Obtain certificates for pantheonelite.ai
echo ""
echo -e "${YELLOW}🔐 Obtaining certificate for pantheonelite.ai...${NC}"
docker run --rm \
    -v /etc/letsencrypt:/etc/letsencrypt \
    -v /var/www/certbot:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d pantheonelite.ai \
    -d www.pantheonelite.ai

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Certificate obtained for pantheonelite.ai${NC}"
else
    echo -e "${RED}❌ Failed to obtain certificate for pantheonelite.ai${NC}"
    exit 1
fi

# Obtain certificates for api.pantheonelite.ai
echo ""
echo -e "${YELLOW}🔐 Obtaining certificate for api.pantheonelite.ai...${NC}"
docker run --rm \
    -v /etc/letsencrypt:/etc/letsencrypt \
    -v /var/www/certbot:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d api.pantheonelite.ai

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Certificate obtained for api.pantheonelite.ai${NC}"
else
    echo -e "${RED}❌ Failed to obtain certificate for api.pantheonelite.ai${NC}"
    exit 1
fi

# Restore original nginx configuration
echo ""
echo -e "${YELLOW}🔄 Restoring production nginx configuration...${NC}"
if [ -f ./nginx/nginx.conf.backup ]; then
    cp ./nginx/nginx.conf.backup ./nginx/nginx.conf
    rm ./nginx/nginx.conf.backup
else
    echo -e "${RED}⚠️  No backup found, please ensure nginx.conf is properly configured${NC}"
fi

# Remove temporary config
rm -f ./nginx/nginx-temp.conf

# Restart nginx with production config
echo ""
echo -e "${YELLOW}🔄 Restarting nginx with SSL configuration...${NC}"
docker-compose down nginx
docker-compose up -d nginx certbot

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}✅ SSL Setup Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Your certificates are located at:"
echo "  • /etc/letsencrypt/live/pantheonelite.ai/"
echo "  • /etc/letsencrypt/live/api.pantheonelite.ai/"
echo ""
echo "Certificate auto-renewal is configured via the certbot container."
echo ""
echo "Next steps:"
echo "  1. Ensure your frontend is running on port 5173"
echo "  2. Ensure your backend is running on port 8000"
echo "  3. Test your sites:"
echo "     • https://pantheonelite.ai"
echo "     • https://api.pantheonelite.ai"
echo ""
echo -e "${YELLOW}Note: Initial certificate issuance may take a few minutes.${NC}"
