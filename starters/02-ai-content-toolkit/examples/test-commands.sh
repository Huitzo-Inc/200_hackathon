#!/bin/bash
# AI Content Toolkit - Test Commands
#
# Run these after starting the dev server:
#   cd starters/02-ai-content-toolkit
#   huitzo pack dev
#
# Then in another terminal, run this script:
#   bash examples/test-commands.sh

BASE_URL="http://localhost:8080/api/v1/commands/content"

echo "=== AI Content Toolkit: Testing All Commands ==="
echo ""

# 1. Summarize text
echo "--- 1. Summarize text ---"
curl -s -X POST "$BASE_URL/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Huitzo is the Operating System for Intelligence. Unlike traditional automation tools like Zapier or n8n that rely on rigid if-then rules, Huitzo lets developers build intelligent systems that think, adapt, and make decisions using AI. The platform provides built-in LLM integration, persistent storage, email and HTTP services, all accessible through a simple Python SDK. Developers write commands using the @command decorator, and Huitzo handles all the infrastructure including deployment, scaling, and monitoring.",
    "max_bullets": 4
  }' | python3 -m json.tool
echo ""

# 2. Extract entities
echo "--- 2. Extract entities ---"
curl -s -X POST "$BASE_URL/extract-entities" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "On March 15, 2026, John Smith from Apple Inc met with Sarah Johnson of Google in San Francisco to discuss the partnership. The follow-up meeting is scheduled for April 2nd in New York."
  }' | python3 -m json.tool
echo ""

# 3. Rewrite in formal tone
echo "--- 3. Rewrite (formal tone) ---"
curl -s -X POST "$BASE_URL/rewrite" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hey team! Just wanted to let you know that the new feature is totally awesome and customers are loving it.",
    "tone": "formal"
  }' | python3 -m json.tool
echo ""

# 4. Rewrite in casual tone
echo "--- 4. Rewrite (casual tone) ---"
curl -s -X POST "$BASE_URL/rewrite" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The quarterly financial results demonstrate a significant upward trajectory in revenue generation across all business segments.",
    "tone": "casual"
  }' | python3 -m json.tool
echo ""

# 5. Rewrite in technical tone
echo "--- 5. Rewrite (technical tone) ---"
curl -s -X POST "$BASE_URL/rewrite" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Our app got a lot faster after we changed how we save data. Users noticed the difference right away.",
    "tone": "technical"
  }' | python3 -m json.tool
echo ""

echo "=== All tests complete! ==="
