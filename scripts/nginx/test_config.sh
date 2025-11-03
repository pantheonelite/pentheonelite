#!/bin/bash

# Nginx Configuration Tester
# Validates nginx config and tests site functionality

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=============================================="
echo "Nginx Configuration Test"
echo "=============================================="
echo ""

# Test 1: Nginx syntax
echo -e "${YELLOW}[1/6] Testing nginx configuration syntax...${NC}"
if docker exec nginx-proxy nginx -t 2>&1; then
    echo -e "${GREEN}✓ Nginx syntax valid${NC}"
else
    echo -e "${RED}✗ Nginx syntax error!${NC}"
    exit 1
fi
echo ""

# Test 2: Test pantheonelite.ai (frontend)
echo -e "${YELLOW}[2/6] Testing pantheonelite.ai accessibility...${NC}"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://pantheonelite.ai --max-time 10 || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Frontend accessible (HTTP $FRONTEND_STATUS)${NC}"
else
    echo -e "${RED}✗ Frontend not accessible (HTTP $FRONTEND_STATUS)${NC}"
fi
echo ""

# Test 3: Test api.pantheonelite.ai (backend)
echo -e "${YELLOW}[3/6] Testing api.pantheonelite.ai accessibility...${NC}"
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.pantheonelite.ai/healthz --max-time 10 || echo "000")
if [ "$API_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ API accessible (HTTP $API_STATUS)${NC}"
else
    echo -e "${RED}✗ API not accessible (HTTP $API_STATUS)${NC}"
fi
echo ""

# Test 4: Test SSL certificate
echo -e "${YELLOW}[4/6] Testing SSL certificate validity...${NC}"
SSL_EXPIRY=$(echo | openssl s_client -servername pantheonelite.ai -connect pantheonelite.ai:443 2>/dev/null | openssl x509 -noout -dates | grep "notAfter" | cut -d= -f2)
if [ -n "$SSL_EXPIRY" ]; then
    echo -e "${GREEN}✓ SSL certificate valid (Expires: $SSL_EXPIRY)${NC}"
else
    echo -e "${YELLOW}⚠ Could not verify SSL certificate${NC}"
fi
echo ""

# Test 5: Test exploit blocking
echo -e "${YELLOW}[5/6] Testing exploit path blocking...${NC}"
EXPLOIT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://pantheonelite.ai/admin --max-time 5 || echo "000")
if [ "$EXPLOIT_STATUS" = "444" ] || [ "$EXPLOIT_STATUS" = "000" ]; then
    echo -e "${GREEN}✓ Exploit blocking working (HTTP $EXPLOIT_STATUS)${NC}"
else
    echo -e "${YELLOW}⚠ Exploit blocking may not be working (HTTP $EXPLOIT_STATUS)${NC}"
fi
echo ""

# Test 6: Test rate limiting
echo -e "${YELLOW}[6/6] Testing rate limiting...${NC}"
RATE_TEST_SUCCESS=0
for i in {1..30}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.pantheonelite.ai/healthz --max-time 1 || echo "000")
    if [ "$STATUS" = "429" ]; then
        RATE_TEST_SUCCESS=1
        break
    fi
    sleep 0.1
done

if [ "$RATE_TEST_SUCCESS" = "1" ]; then
    echo -e "${GREEN}✓ Rate limiting working (Got HTTP 429)${NC}"
else
    echo -e "${YELLOW}⚠ Rate limiting not triggered (may be too permissive)${NC}"
fi
echo ""

# Summary
echo "=============================================="
echo -e "${GREEN}Configuration test complete!${NC}"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. If all tests passed, configuration is safe to use"
echo "  2. Monitor logs for 15 minutes after deployment"
echo "  3. Check pantheonelite.ai in browser"
echo "  4. Verify WebSocket connections work"
echo "=============================================="

