#!/usr/bin/env bash
#
# validate-pack.sh - Validate an Intelligence Pack structure
#
# Usage: ./scripts/validate-pack.sh <path-to-pack>
#
# Checks:
#   - Required files exist (README.md, huitzo.yaml, pyproject.toml, src/)
#   - YAML syntax is valid
#   - pyproject.toml has required fields
#   - src/ directory has Python files
#   - Recommends tests if missing
#
# Exit codes:
#   0 - All checks passed
#   1 - Required check failed
#   2 - Usage error

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0

pass() {
    echo -e "  ${GREEN}PASS${NC}  $1"
}

fail() {
    echo -e "  ${RED}FAIL${NC}  $1"
    ERRORS=$((ERRORS + 1))
}

warn() {
    echo -e "  ${YELLOW}WARN${NC}  $1"
    WARNINGS=$((WARNINGS + 1))
}

info() {
    echo -e "  ${BLUE}INFO${NC}  $1"
}

# --- Usage ---
if [ $# -lt 1 ]; then
    echo "Usage: $0 <path-to-pack>"
    echo ""
    echo "Example:"
    echo "  $0 starters/01-smart-notes"
    echo "  $0 ./my-custom-pack"
    exit 2
fi

PACK_DIR="$1"

# Resolve to absolute path
if [[ ! "$PACK_DIR" = /* ]]; then
    PACK_DIR="$(cd "$PACK_DIR" 2>/dev/null && pwd)" || {
        echo -e "${RED}Error: Directory '$1' does not exist.${NC}"
        exit 2
    }
fi

if [ ! -d "$PACK_DIR" ]; then
    echo -e "${RED}Error: '$PACK_DIR' is not a directory.${NC}"
    exit 2
fi

PACK_NAME=$(basename "$PACK_DIR")

echo ""
echo "============================================"
echo "  Validating Intelligence Pack: $PACK_NAME"
echo "============================================"
echo ""
echo "Directory: $PACK_DIR"
echo ""

# --- Required Files ---
echo "--- Required Files ---"

if [ -f "$PACK_DIR/README.md" ]; then
    pass "README.md exists"
    # Check if README has content
    if [ "$(wc -l < "$PACK_DIR/README.md")" -lt 5 ]; then
        warn "README.md is very short (less than 5 lines)"
    fi
else
    fail "README.md is missing"
fi

if [ -f "$PACK_DIR/huitzo.yaml" ]; then
    pass "huitzo.yaml exists"
else
    fail "huitzo.yaml is missing"
fi

if [ -f "$PACK_DIR/pyproject.toml" ]; then
    pass "pyproject.toml exists"
else
    fail "pyproject.toml is missing"
fi

if [ -d "$PACK_DIR/src" ]; then
    pass "src/ directory exists"
else
    fail "src/ directory is missing"
fi

echo ""

# --- YAML Validation ---
echo "--- YAML Validation ---"

if [ -f "$PACK_DIR/huitzo.yaml" ]; then
    # Try python yaml parsing first, fall back to basic syntax check
    if command -v python3 &>/dev/null; then
        if python3 -c "
import yaml, sys
try:
    with open('$PACK_DIR/huitzo.yaml') as f:
        data = yaml.safe_load(f)
    if data is None:
        print('Empty YAML file', file=sys.stderr)
        sys.exit(1)
    sys.exit(0)
except yaml.YAMLError as e:
    print(f'YAML error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; then
            pass "huitzo.yaml is valid YAML"
        else
            fail "huitzo.yaml has invalid YAML syntax"
        fi
    else
        # Fallback: basic syntax check (look for obvious issues)
        if grep -qP '^\t' "$PACK_DIR/huitzo.yaml" 2>/dev/null; then
            fail "huitzo.yaml contains tabs (YAML requires spaces)"
        else
            info "YAML syntax check skipped (python3 not available)"
        fi
    fi

    # Check for required fields in huitzo.yaml
    # Supports both top-level (name, version) and nested (pack.name, pack.version) formats
    if command -v python3 &>/dev/null; then
        YAML_CHECK=$(python3 -c "
import yaml, sys
try:
    with open('$PACK_DIR/huitzo.yaml') as f:
        data = yaml.safe_load(f)
    if not data:
        sys.exit(0)
    missing = []
    # Check top-level or nested under 'pack'
    pack = data.get('pack', data)
    for field in ['name', 'version']:
        if field not in pack:
            missing.append(field)
    if missing:
        print(','.join(missing))
except Exception:
    pass
" 2>/dev/null)
        if [ -n "$YAML_CHECK" ]; then
            fail "huitzo.yaml missing required fields: $YAML_CHECK"
        else
            pass "huitzo.yaml has required fields (name, version)"
        fi
    fi
else
    info "huitzo.yaml not found, skipping YAML validation"
fi

echo ""

# --- Source Code ---
echo "--- Source Code ---"

if [ -d "$PACK_DIR/src" ]; then
    PY_COUNT=$(find "$PACK_DIR/src" -name "*.py" -type f 2>/dev/null | wc -l)
    if [ "$PY_COUNT" -gt 0 ]; then
        pass "Found $PY_COUNT Python file(s) in src/"
    else
        fail "No Python files found in src/"
    fi

    # Check for __init__.py
    INIT_COUNT=$(find "$PACK_DIR/src" -name "__init__.py" -type f 2>/dev/null | wc -l)
    if [ "$INIT_COUNT" -gt 0 ]; then
        pass "Package has __init__.py"
    else
        warn "No __init__.py found in src/ (may cause import issues)"
    fi

    # Check for @command decorator usage
    if grep -rq "@command" "$PACK_DIR/src/" 2>/dev/null; then
        pass "Found @command decorator usage"
    else
        warn "No @command decorator found in source code"
    fi
fi

echo ""

# --- Recommended Files ---
echo "--- Recommended (Optional) ---"

if [ -d "$PACK_DIR/tests" ]; then
    TEST_COUNT=$(find "$PACK_DIR/tests" -name "test_*.py" -o -name "*_test.py" 2>/dev/null | wc -l)
    if [ "$TEST_COUNT" -gt 0 ]; then
        pass "Found $TEST_COUNT test file(s)"
    else
        warn "tests/ directory exists but no test files found"
    fi
else
    warn "No tests/ directory (recommended for Best Pack prize)"
fi

if [ -f "$PACK_DIR/.env.example" ]; then
    pass ".env.example exists"
else
    info "No .env.example (add one if your pack needs API keys)"
fi

echo ""

# --- Summary ---
echo "============================================"
if [ "$ERRORS" -gt 0 ]; then
    echo -e "  ${RED}FAILED${NC} - $ERRORS error(s), $WARNINGS warning(s)"
    echo ""
    echo "  Fix the errors above before submitting."
    echo "============================================"
    exit 1
else
    if [ "$WARNINGS" -gt 0 ]; then
        echo -e "  ${GREEN}PASSED${NC} - $WARNINGS warning(s)"
    else
        echo -e "  ${GREEN}PASSED${NC} - All checks passed!"
    fi
    echo ""
    echo "  Your pack is ready to submit!"
    echo "  Run: ./scripts/submit-pack.sh $1 <your-github-username>"
    echo "============================================"
    exit 0
fi
