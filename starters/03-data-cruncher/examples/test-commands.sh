#!/bin/bash
# Data Cruncher - Test Commands
#
# Run these after starting the dev server:
#   cd starters/03-data-cruncher
#   huitzo pack dev
#
# Then in another terminal, run this script:
#   bash examples/test-commands.sh

BASE_URL="http://localhost:8080/api/v1/commands/data"

echo "=== Data Cruncher: Testing Full Workflow ==="
echo ""

# 1. Analyze CSV file (revenue column)
echo "--- 1. Analyze CSV file (revenue column) ---"
RESULT=$(curl -s -X POST "$BASE_URL/analyze-file" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "examples/sample-data/sales.csv",
    "column_name": "revenue"
  }')
echo "$RESULT" | python3 -m json.tool

# Extract analysis_id for subsequent commands
ANALYSIS_ID=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('analysis_id', ''))" 2>/dev/null)
echo ""
echo "Analysis ID: $ANALYSIS_ID"
echo ""

if [ -z "$ANALYSIS_ID" ]; then
    echo "ERROR: Could not extract analysis_id. Stopping."
    exit 1
fi

# 2. Get AI insights
echo "--- 2. Get AI insights ---"
curl -s -X POST "$BASE_URL/ai-insights" \
  -H "Content-Type: application/json" \
  -d "{\"analysis_id\": \"$ANALYSIS_ID\"}" | python3 -m json.tool
echo ""

# 3. Export report
echo "--- 3. Export report ---"
curl -s -X POST "$BASE_URL/export-report" \
  -H "Content-Type: application/json" \
  -d "{
    \"analysis_id\": \"$ANALYSIS_ID\",
    \"output_path\": \"output/sales-report.csv\"
  }" | python3 -m json.tool
echo ""

# 4. Analyze a different column
echo "--- 4. Analyze units_sold column ---"
curl -s -X POST "$BASE_URL/analyze-file" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "examples/sample-data/sales.csv",
    "column_name": "units_sold"
  }' | python3 -m json.tool
echo ""

echo "=== All tests complete! ==="
