#!/bin/bash

# Nginx Configuration Rollback Script
# Emergency rollback to previous working configuration

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=============================================="
echo -e "${RED}EMERGENCY ROLLBACK${NC}"
echo "=============================================="
echo ""

# Find most recent backup
BACKUP_FILE=$(ls -t /root/vibe-trading/nginx/nginx-production.conf.backup.* 2>/dev/null | head -1)

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}✗ No backup file found!${NC}"
    exit 1
fi

echo -e "${YELLOW}Found backup: $BACKUP_FILE${NC}"
echo "Rolling back to previous configuration..."
echo ""

# Copy backup to production-secure (in case that's what's mounted)
cp "$BACKUP_FILE" /root/vibe-trading/nginx/nginx-production-secure.conf
cp "$BACKUP_FILE" /root/vibe-trading/nginx/nginx-production.conf

# Test configuration
echo "Testing configuration..."
if docker exec nginx-proxy nginx -t 2>&1; then
    echo -e "${GREEN}✓ Configuration valid${NC}"
else
    echo -e "${RED}✗ Configuration test failed!${NC}"
    exit 1
fi

# Reload nginx
echo "Reloading nginx..."
docker exec nginx-proxy nginx -s reload

sleep 2

# Verify site is accessible
echo "Verifying site accessibility..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://pantheonelite.ai --max-time 10 || echo "000")
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.pantheonelite.ai/healthz --max-time 10 || echo "000")

if [ "$FRONTEND_STATUS" = "200" ] && [ "$API_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Rollback successful!${NC}"
    echo -e "${GREEN}✓ Frontend: HTTP $FRONTEND_STATUS${NC}"
    echo -e "${GREEN}✓ API: HTTP $API_STATUS${NC}"
else
    echo -e "${RED}✗ Rollback may have issues${NC}"
    echo -e "  Frontend: HTTP $FRONTEND_STATUS"
    echo -e "  API: HTTP $API_STATUS"
fi

echo ""
echo "Rollback complete. Timestamp: $(date)"
echo "Backup restored from: $(basename "$BACKUP_FILE")"
echo "=============================================="
