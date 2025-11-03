#!/bin/bash

# Nginx Attack Monitor
# Real-time monitoring of attack patterns in nginx logs

set -e

# Configuration
LOG_FILE="/root/vibe-trading/nginx/logs/access.log"
ALERT_LOG="/root/vibe-trading/logs/attack_alerts.log"
BLOCKLIST="/root/vibe-trading/nginx/blocklists/blocked-ips.conf"
THRESHOLD=10  # Alert if more than 10 exploits attempts

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Create log directory
mkdir -p "$(dirname "$ALERT_LOG")"

# Function to log alerts
log_alert() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$ALERT_LOG"
}

echo "==================================="
echo "Nginx Attack Monitor"
echo "==================================="
echo "Monitoring: $LOG_FILE"
echo "Threshold: $THRESHOLD attempts"
echo ""

# Get recent attack attempts (last 5 minutes)
EXPLOIT_COUNT=$(tail -1000 "$LOG_FILE" | grep -E "(admin|phpmyadmin|wp-admin|config\.php|\.env|mining|eth_submit|cgi-bin|owa|\.asp|\.jsp)" | wc -l)

# Get unique attacking IPs
ATTACKING_IPS=$(tail -1000 "$LOG_FILE" | grep -E "(admin|phpmyadmin|wp-admin|config\.php|mining)" | awk '{print $1}' | sort | uniq -c | sort -rn | head -10)

# Display current status
echo -e "${GREEN}Recent Activity (last 1000 requests):${NC}"
echo "  Total exploit attempts: $EXPLOIT_COUNT"
echo ""

if [ "$EXPLOIT_COUNT" -gt "$THRESHOLD" ]; then
    echo -e "${RED}⚠ HIGH ACTIVITY DETECTED!${NC}"
    log_alert "HIGH: $EXPLOIT_COUNT exploit attempts detected"
    
    echo ""
    echo -e "${YELLOW}Top Attacking IPs:${NC}"
    echo "$ATTACKING_IPS"
    
    # Auto-add to blocklist if not already there
    echo "$ATTACKING_IPS" | while read count ip; do
        if [ "$count" -gt 5 ] && ! grep -q "$ip" "$BLOCKLIST" 2>/dev/null; then
            echo "deny $ip;  # Auto-added: $count attempts on $(date '+%Y-%m-%d')" >> "$BLOCKLIST"
            log_alert "AUTO-BLOCKED: $ip ($count attempts)"
            echo -e "${RED}  → Auto-blocked: $ip${NC}"
        fi
    done
else
    echo -e "${GREEN}✓ Activity normal${NC}"
fi

# Show recent bad bot attempts
BOT_COUNT=$(tail -1000 "$LOG_FILE" | grep -E "(zgrab|masscan|nmap|sqlmap|XMRig|cpuminer)" | wc -l)
if [ "$BOT_COUNT" -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Bad bot attempts: $BOT_COUNT${NC}"
fi

# Show mining protocol attempts
MINING_COUNT=$(tail -1000 "$LOG_FILE" | grep -E "(mining\.subscribe|eth_submit|getwork|stratum)" | wc -l)
if [ "$MINING_COUNT" -gt 0 ]; then
    echo -e "${RED}Mining protocol attempts: $MINING_COUNT${NC}"
fi

# Show rate limit hits
RATE_LIMIT_COUNT=$(tail -1000 "$LOG_FILE" | grep " 429 " | wc -l)
if [ "$RATE_LIMIT_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}Rate limit hits: $RATE_LIMIT_COUNT${NC}"
fi

echo ""
echo "Last update: $(date '+%Y-%m-%d %H:%M:%S')"
echo "==================================="

