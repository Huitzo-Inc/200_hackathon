#!/bin/bash
# Smart Notes - Test Commands
#
# Run these after starting the dev server:
#   cd starters/01-smart-notes
#   huitzo pack dev
#
# Then in another terminal, run this script:
#   bash examples/test-commands.sh

BASE_URL="http://localhost:8080/api/v1/commands/notes"

echo "=== Smart Notes: Testing All Commands ==="
echo ""

# 1. Save a note
echo "--- 1. Save a note ---"
curl -s -X POST "$BASE_URL/save-note" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Meeting Notes",
    "content": "Discussed Q1 roadmap. Focus on user growth and retention."
  }' | python3 -m json.tool
echo ""

# 2. Save another note
echo "--- 2. Save another note ---"
curl -s -X POST "$BASE_URL/save-note" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Shopping List",
    "content": "Milk, eggs, bread, coffee beans"
  }' | python3 -m json.tool
echo ""

# 3. Get a note
echo "--- 3. Get a note ---"
curl -s -X POST "$BASE_URL/get-note" \
  -H "Content-Type: application/json" \
  -d '{"title": "Meeting Notes"}' | python3 -m json.tool
echo ""

# 4. List all notes
echo "--- 4. List all notes ---"
curl -s -X POST "$BASE_URL/list-notes" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
echo ""

# 5. Update a note
echo "--- 5. Update a note ---"
curl -s -X POST "$BASE_URL/save-note" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Meeting Notes",
    "content": "UPDATED: Discussed Q1 roadmap. Added action items for next week."
  }' | python3 -m json.tool
echo ""

# 6. Delete a note
echo "--- 6. Delete a note ---"
curl -s -X POST "$BASE_URL/delete-note" \
  -H "Content-Type: application/json" \
  -d '{"title": "Shopping List"}' | python3 -m json.tool
echo ""

# 7. Verify deletion
echo "--- 7. Verify deletion (expect not_found) ---"
curl -s -X POST "$BASE_URL/get-note" \
  -H "Content-Type: application/json" \
  -d '{"title": "Shopping List"}' | python3 -m json.tool
echo ""

# 8. List notes after deletion
echo "--- 8. List notes after deletion ---"
curl -s -X POST "$BASE_URL/list-notes" \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}' | python3 -m json.tool
echo ""

echo "=== All tests complete! ==="
