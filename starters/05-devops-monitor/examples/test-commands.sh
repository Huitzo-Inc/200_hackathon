#!/bin/bash
# DevOps Monitor - Test Commands
#
# Run these after starting the dev server:
#   cd starters/05-devops-monitor
#   huitzo pack dev
#
# Then in another terminal, run this script:
#   bash examples/test-commands.sh

BASE_URL="http://localhost:8080/api/v1/commands/monitor"

echo "=== DevOps Monitor: Testing Full Workflow ==="
echo ""

# 1. Health check (using httpbin as a mock service)
echo "--- 1. Health Check ---"
curl -s -X POST "$BASE_URL/health-check" \
  -H "Content-Type: application/json" \
  -d '{
    "endpoints": [
      "https://httpbin.org/status/200",
      "https://httpbin.org/delay/3",
      "https://httpbin.org/status/500"
    ],
    "timeout_seconds": 5
  }' | python3 -m json.tool
echo ""

# 2. Diagnose the failing service
echo "--- 2. Diagnose ---"
curl -s -X POST "$BASE_URL/diagnose" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "httpbin",
    "lookback_minutes": 60
  }' | python3 -m json.tool
echo ""

# 3. Send a critical alert
echo "--- 3. Alert (Critical) ---"
curl -s -X POST "$BASE_URL/alert" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "httpbin",
    "severity": "critical",
    "message": "Endpoint returned HTTP 500 - server error detected",
    "channels": ["email", "telegram"]
  }' | python3 -m json.tool
echo ""

# 4. Generate a status report
echo "--- 4. Status Report ---"
curl -s -X POST "$BASE_URL/status-report" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
echo ""

echo "=== All tests complete! ==="
