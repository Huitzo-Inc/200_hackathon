#!/bin/bash
# Lead Engine - Full Workflow Example
#
# This script demonstrates the complete lead pipeline:
# 1. Add a lead
# 2. Score the lead with AI
# 3. Send personalized outreach
# 4. Generate a pipeline report
#
# Prerequisites:
#   cd starters/04-lead-engine
#   huitzo pack dev
#
# Then run this script in another terminal.

BASE_URL="http://localhost:8080/api/v1/commands"

echo "============================================"
echo "  Lead Engine - Full Workflow Demo"
echo "============================================"
echo ""

# Step 1: Add a lead
echo "Step 1: Adding a new lead..."
echo "---"
RESPONSE=$(curl -s -X POST "$BASE_URL/leads/add-lead" \
  -H "Content-Type: application/json" \
  -d '{
    "company": "TechStart Inc",
    "contact_name": "Sarah Chen",
    "email": "sarah@techstart.io",
    "website": "https://techstart.io",
    "notes": "VP of Engineering. Met at AI conference. 50-person startup, Series A funded."
  }')
echo "$RESPONSE" | python3 -m json.tool
LEAD_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['lead_id'])" 2>/dev/null)
echo ""
echo "Lead ID: $LEAD_ID"
echo ""

# Step 2: Score the lead
echo "Step 2: Scoring the lead with AI..."
echo "---"
curl -s -X POST "$BASE_URL/leads/score-lead" \
  -H "Content-Type: application/json" \
  -d "{\"lead_id\": \"$LEAD_ID\"}" | python3 -m json.tool
echo ""

# Step 3: Send outreach
echo "Step 3: Sending intro outreach email..."
echo "---"
curl -s -X POST "$BASE_URL/leads/send-outreach" \
  -H "Content-Type: application/json" \
  -d "{\"lead_id\": \"$LEAD_ID\", \"template_name\": \"intro\"}" | python3 -m json.tool
echo ""

# Step 4: Add more leads for a richer report
echo "Step 4: Adding more leads for the pipeline..."
echo "---"

curl -s -X POST "$BASE_URL/leads/add-lead" \
  -H "Content-Type: application/json" \
  -d '{
    "company": "BigCorp Enterprise",
    "contact_name": "James Wilson",
    "email": "james@bigcorp.com",
    "notes": "CTO. Fortune 500 company. Looking for AI solutions."
  }' | python3 -m json.tool

LEAD2=$(curl -s -X POST "$BASE_URL/leads/add-lead" \
  -H "Content-Type: application/json" \
  -d '{
    "company": "SmallBiz LLC",
    "contact_name": "Pat Rivera",
    "email": "pat@smallbiz.co",
    "notes": "Owner. 5-person team."
  }')
echo "$LEAD2" | python3 -m json.tool
echo ""

# Step 5: Pipeline report
echo "Step 5: Generating pipeline report..."
echo "---"
curl -s -X POST "$BASE_URL/leads/pipeline-report" \
  -H "Content-Type: application/json" \
  -d '{"include_details": true}' | python3 -m json.tool
echo ""

echo "============================================"
echo "  Workflow complete!"
echo "============================================"
echo ""
echo "Try experimenting:"
echo "  - Score the other leads"
echo "  - Send follow-up emails"
echo "  - Try the demo-invite template"
echo "  - Add your own leads and see how AI scores them"
