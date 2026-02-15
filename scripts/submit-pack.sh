#!/usr/bin/env bash
#
# submit-pack.sh - Submit an Intelligence Pack to the hackathon showcase
#
# Usage: ./scripts/submit-pack.sh <path-to-pack> <github-username>
#
# This script:
#   1. Validates the pack structure
#   2. Copies it to showcase/<username>/<pack-name>/
#   3. Creates a SUBMISSION.md with metadata
#   4. Prints next steps for creating a PR
#
# Exit codes:
#   0 - Submission prepared successfully
#   1 - Validation failed
#   2 - Usage error

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# --- Usage ---
if [ $# -lt 2 ]; then
    echo "Usage: $0 <path-to-pack> <github-username>"
    echo ""
    echo "Example:"
    echo "  $0 ./my-awesome-pack octocat"
    echo "  $0 starters/01-smart-notes janedoe"
    exit 2
fi

PACK_DIR="$1"
USERNAME="$2"

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

# Validate username (basic check)
if [[ ! "$USERNAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo -e "${RED}Error: Invalid GitHub username '$USERNAME'.${NC}"
    echo "Username should contain only letters, numbers, hyphens, and underscores."
    exit 2
fi

PACK_NAME=$(basename "$PACK_DIR")

# Find repo root (where this script lives under scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SHOWCASE_DIR="$REPO_ROOT/showcase/$USERNAME/$PACK_NAME"

echo ""
echo -e "${BOLD}Submitting Intelligence Pack${NC}"
echo "============================================"
echo "  Pack:     $PACK_NAME"
echo "  Author:   $USERNAME"
echo "  Source:   $PACK_DIR"
echo "  Target:   showcase/$USERNAME/$PACK_NAME/"
echo "============================================"
echo ""

# --- Step 1: Validate ---
echo -e "${BLUE}Step 1: Validating pack...${NC}"
echo ""

if ! "$REPO_ROOT/scripts/validate-pack.sh" "$PACK_DIR"; then
    echo ""
    echo -e "${RED}Submission aborted: Pack validation failed.${NC}"
    echo "Fix the errors above and try again."
    exit 1
fi

echo ""

# --- Step 2: Check for existing submission ---
if [ -d "$SHOWCASE_DIR" ]; then
    echo -e "${YELLOW}Warning: showcase/$USERNAME/$PACK_NAME/ already exists.${NC}"
    echo ""
    read -rp "Overwrite existing submission? (y/N) " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[yY]$ ]]; then
        echo "Submission cancelled."
        exit 0
    fi
    rm -rf "$SHOWCASE_DIR"
fi

# --- Step 3: Copy pack to showcase ---
echo -e "${BLUE}Step 2: Copying pack to showcase...${NC}"

mkdir -p "$SHOWCASE_DIR"
cp -r "$PACK_DIR"/* "$SHOWCASE_DIR"/

# Copy hidden files if any (like .env.example), but not .git or .huitzo
for hidden in "$PACK_DIR"/.*; do
    base=$(basename "$hidden")
    case "$base" in
        .|..|.git|.huitzo|.huitzo-cache|.venv|.env|.env.local)
            continue
            ;;
        *)
            cp -r "$hidden" "$SHOWCASE_DIR"/ 2>/dev/null || true
            ;;
    esac
done

echo -e "  ${GREEN}DONE${NC}  Pack copied to showcase/$USERNAME/$PACK_NAME/"

# --- Step 4: Create SUBMISSION.md ---
echo -e "${BLUE}Step 3: Creating SUBMISSION.md...${NC}"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Extract pack info from huitzo.yaml if possible
PACK_VERSION="unknown"
PACK_DESCRIPTION=""
if command -v python3 &>/dev/null && [ -f "$SHOWCASE_DIR/huitzo.yaml" ]; then
    PACK_VERSION=$(python3 -c "
import yaml
with open('$SHOWCASE_DIR/huitzo.yaml') as f:
    data = yaml.safe_load(f)
print(data.get('version', 'unknown'))
" 2>/dev/null || echo "unknown")
    PACK_DESCRIPTION=$(python3 -c "
import yaml
with open('$SHOWCASE_DIR/huitzo.yaml') as f:
    data = yaml.safe_load(f)
print(data.get('description', ''))
" 2>/dev/null || echo "")
fi

cat > "$SHOWCASE_DIR/SUBMISSION.md" << EOF
# Submission: $PACK_NAME

## Metadata

| Field | Value |
|-------|-------|
| **Pack Name** | $PACK_NAME |
| **Author** | @$USERNAME |
| **Version** | $PACK_VERSION |
| **Submitted** | $TIMESTAMP |
| **Hackathon** | Huitzo Hackathon 2026 |

## Description

$PACK_DESCRIPTION

## Quick Start

\`\`\`bash
cd showcase/$USERNAME/$PACK_NAME
pip install -e .
huitzo pack dev
\`\`\`

## Prize Categories

<!-- Check which prizes you're targeting -->

- [ ] Best Pack (\$400)
- [ ] Most Creative (\$250)
- [ ] Most Business Friendly (\$250)

---

*Submitted via \`scripts/submit-pack.sh\` on $TIMESTAMP*
EOF

echo -e "  ${GREEN}DONE${NC}  SUBMISSION.md created"

# --- Step 5: Summary ---
echo ""
echo "============================================"
echo -e "  ${GREEN}Submission prepared!${NC}"
echo "============================================"
echo ""
echo -e "${BOLD}Next Steps:${NC}"
echo ""
echo "  1. Review your submission:"
echo -e "     ${BLUE}ls showcase/$USERNAME/$PACK_NAME/${NC}"
echo ""
echo "  2. Edit SUBMISSION.md to add your description and select prize categories:"
echo -e "     ${BLUE}nano showcase/$USERNAME/$PACK_NAME/SUBMISSION.md${NC}"
echo ""
echo "  3. Stage, commit, and push:"
echo -e "     ${BLUE}git add showcase/$USERNAME/$PACK_NAME/${NC}"
echo -e "     ${BLUE}git commit -m \"Submit $PACK_NAME by @$USERNAME\"${NC}"
echo -e "     ${BLUE}git push origin HEAD${NC}"
echo ""
echo "  4. Create a Pull Request on GitHub:"
echo -e "     ${BLUE}gh pr create --title \"[SUBMISSION] $PACK_NAME\" --template pack-submission.md${NC}"
echo ""
echo "  5. Open a Pack Submission issue on GitHub:"
echo "     https://github.com/Huitzo-Inc/hackathon-2026/issues/new?template=pack-submission.md"
echo ""
echo "============================================"
echo -e "  Good luck! We can't wait to see what you built."
echo "============================================"
echo ""
