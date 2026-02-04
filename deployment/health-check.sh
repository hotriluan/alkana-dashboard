#!/bin/bash

# Health Check Script
# Monitors application health and sends alerts

set -e

DOMAIN="${DOMAIN:-dashboard.alkana.com}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
EMAIL="${ALERT_EMAIL:-}"

check_service() {
    local service=$1
    local url=$2
    
    if curl -sf "$url" > /dev/null; then
        echo "✅ $service is healthy"
        return 0
    else
        echo "❌ $service is down!"
        return 1
    fi
}

send_alert() {
    local message=$1
    
    # Send to Slack if webhook configured
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 Alkana Dashboard Alert: $message\"}" \
            "$SLACK_WEBHOOK"
    fi
    
    # Send email if configured
    if [ -n "$EMAIL" ]; then
        echo "$message" | mail -s "Alkana Dashboard Alert" "$EMAIL"
    fi
}

# Check services
echo "Checking Alkana Dashboard health..."

FAILED=0

# Check frontend
if ! check_service "Frontend" "https://$DOMAIN/health"; then
    send_alert "Frontend is down on $DOMAIN"
    FAILED=$((FAILED + 1))
fi

# Check API
if ! check_service "API" "https://$DOMAIN/api/health"; then
    send_alert "API is down on $DOMAIN"
    FAILED=$((FAILED + 1))
fi

# Check Docker services
echo ""
echo "Docker services status:"
docker compose -f /home/deploy/alkana-dashboard/docker-compose.prod.yml ps

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️  Warning: Disk usage is at ${DISK_USAGE}%"
    send_alert "Disk usage is at ${DISK_USAGE}%"
fi

# Check memory
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
if [ "$MEMORY_USAGE" -gt 85 ]; then
    echo "⚠️  Warning: Memory usage is at ${MEMORY_USAGE}%"
    send_alert "Memory usage is at ${MEMORY_USAGE}%"
fi

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "✅ All services are healthy"
    exit 0
else
    echo ""
    echo "❌ $FAILED service(s) are down"
    exit 1
fi
