#!/bin/bash
# Test the Jumperless package locally before publishing to PyPI

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing Jumperless Package Locally${NC}"
echo ""

# Check if package is built
if [ ! -d "dist" ]; then
    echo -e "${YELLOW}No dist/ directory found. Building package first...${NC}"
    ./build_package.sh
    echo ""
fi

# Create test virtual environment
TEST_VENV="test-jumperless-install"
echo -e "${YELLOW}Creating test virtual environment: $TEST_VENV${NC}"
python3 -m venv $TEST_VENV
source $TEST_VENV/bin/activate

echo -e "${GREEN}✓ Virtual environment created${NC}"
echo ""

# Install the package from local wheel
echo -e "${YELLOW}Installing jumperless from local build...${NC}"
WHEEL_FILE=$(ls dist/*.whl | head -1)
pip install "$WHEEL_FILE"
echo -e "${GREEN}✓ Package installed${NC}"
echo ""

# Show installed package info
echo -e "${BLUE}Installed package info:${NC}"
pip show jumperless
echo ""

# Check if command is available
echo -e "${YELLOW}Testing 'jumperless' command availability...${NC}"
if command -v jumperless &> /dev/null; then
    echo -e "${GREEN}✓ 'jumperless' command is available${NC}"
    echo ""
    echo -e "${BLUE}Command location:${NC}"
    which jumperless
    echo ""
else
    echo -e "${RED}✗ 'jumperless' command not found${NC}"
    echo ""
fi

# Show entry points
echo -e "${BLUE}Entry points registered:${NC}"
python3 -c "import pkg_resources; print([ep for ep in pkg_resources.iter_entry_points('console_scripts') if 'jumperless' in ep.name])"
echo ""

echo -e "${YELLOW}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  Test environment ready!                               ║${NC}"
echo -e "${YELLOW}║                                                        ║${NC}"
echo -e "${YELLOW}║  You can now run:                                     ║${NC}"
echo -e "${YELLOW}║    ${GREEN}jumperless${YELLOW}                                        ║${NC}"
echo -e "${YELLOW}║                                                        ║${NC}"
echo -e "${YELLOW}║  When done testing:                                   ║${NC}"
echo -e "${YELLOW}║    ${BLUE}deactivate${YELLOW}                                       ║${NC}"
echo -e "${YELLOW}║    ${BLUE}rm -rf $TEST_VENV${YELLOW}                  ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Virtual environment activated. Type 'deactivate' to exit.${NC}"
echo ""

