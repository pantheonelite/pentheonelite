#!/bin/bash

# Nginx Log Analyzer
# Daily analysis and reporting of attack patterns

set -e

# Configuration
LOG_FILE="/root/vibe-trading/nginx/logs/access.log"
REPORT_DIR="/root/vibe-trading/reports"
REPORT_FILE="$REPORT_DIR/attack_report_$(date +%Y%m%d).txt"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Create report directory
mkdir -p "$REPORT_DIR"

echo "==================================="
echo "Nginx Log Analysis Report"
echo "Generated: $(date)"
echo "==================================="
echo ""

{
    echo "=================================="
    echo "Nginx Security Analysis Report"
    echo "Generated: $(date)"
    echo "=================================="
    echo ""

    # Total requests
    TOTAL_REQUESTS=$(wc -l < "$LOG_FILE")
    echo "Total Requests: $TOTAL_REQUESTS"
    echo ""

    # Exploit attempts
    echo "--- EXPLOIT ATTEMPTS ---"
    EXPLOIT_COUNT=$(grep -E "(admin|phpmyadmin|wp-admin|config\.php|\.env|cgi-bin|owa)" "$LOG_FILE" | wc -l)
    echo "Total exploit attempts: $EXPLOIT_COUNT"
    echo ""

    echo "Top exploit paths:"
    grep -E "(admin|phpmyadmin|wp-admin|config\.php|\.env)" "$LOG_FILE" | awk '{print $7}' | sort | uniq -c | sort -rn | head -10
    echo ""

    # Mining attempts
    echo "--- MINING ATTEMPTS ---"
    MINING_COUNT=$(grep -E "(mining|eth_submit|XMRig|cpuminer)" "$LOG_FILE" | wc -l)
    echo "Total mining attempts: $MINING_COUNT"
    echo ""

    # Bad bots
    echo "--- BAD BOT ATTEMPTS ---"
    BOT_COUNT=$(grep -E "(zgrab|masscan|nmap|sqlmap|nikto)" "$LOG_FILE" | wc -l)
    echo "Total bad bot requests: $BOT_COUNT"
    echo ""

    echo "Top bad bots:"
    grep -E "(zgrab|masscan|nmap|sqlmap|nikto)" "$LOG_FILE" | awk '{print $12}' | sort | uniq -c | sort -rn | head -10
    echo ""

    # Top attacking IPs
    echo "--- TOP ATTACKING IPs ---"
    grep -E "(admin|phpmyadmin|mining|zgrab)" "$LOG_FILE" | awk '{print $1}' | sort | uniq -c | sort -rn | head -20
    echo ""

    # Status code distribution
    echo "--- STATUS CODE DISTRIBUTION ---"
    awk '{print $9}' "$LOG_FILE" | sort | uniq -c | sort -rn
    echo ""

    # Rate limiting effectiveness
    echo "--- RATE LIMITING ---"
    RATE_LIMIT_HITS=$(grep " 429 " "$LOG_FILE" | wc -l)
    echo "Rate limit hits (429): $RATE_LIMIT_HITS"
    echo ""

    if [ "$RATE_LIMIT_HITS" -gt 0 ]; then
        echo "Top rate-limited IPs:"
        grep " 429 " "$LOG_FILE" | awk '{print $1}' | sort | uniq -c | sort -rn | head -10
        echo ""
    fi

    # Recommendations
    echo "--- RECOMMENDATIONS ---"
    if [ "$EXPLOIT_COUNT" -gt 100 ]; then
        echo "⚠ HIGH: Consider blocking top attacking IPs"
    fi

    if [ "$MINING_COUNT" -gt 10 ]; then
        echo "⚠ MEDIUM: Mining attempts detected, ensure blocklist is updated"
    fi

    if [ "$BOT_COUNT" -gt 50 ]; then
        echo "⚠ MEDIUM: High bot activity, verify bot-blocking is effective"
    fi

    if [ "$RATE_LIMIT_HITS" -gt 1000 ]; then
        echo "⚠ INFO: High rate limiting activity, may need to adjust thresholds"
    fi

    echo ""
    echo "=================================="
    echo "End of Report"
    echo "=================================="
} | tee "$REPORT_FILE"

echo ""
echo -e "${GREEN}Report saved to: $REPORT_FILE${NC}"
echo ""

# Generate ban recommendations
echo -e "${YELLOW}Ban Recommendations:${NC}"
grep -E "(admin|phpmyadmin|mining|zgrab)" "$LOG_FILE" | awk '{print $1}' | sort | uniq -c | sort -rn | head -10 | while read count ip; do
    if [ "$count" -gt 20 ]; then
        echo -e "${RED}  → RECOMMEND BAN: $ip ($count attempts)${NC}"
    fi
done
