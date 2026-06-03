#!/bin/bash
# Complete workflow script for publishing Jumperless to PyPI

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${MAGENTA}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║          Jumperless PyPI Publishing Workflow               ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Step 1: Version check
echo -e "${BLUE}Step 1: Checking version...${NC}"
VERSION=$(tr -d '[:space:]' < VERSION)
echo "  VERSION file:    $VERSION"
echo -e "${GREEN}✓ Release version: $VERSION${NC}"
echo ""

# Step 2: Check if bridge.py is up to date
echo -e "${BLUE}Step 2: Checking if bridge.py is up to date...${NC}"
if ! diff -q JumperlessWokwiBridge.py jumperless_pkg/bridge.py > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  bridge.py differs from JumperlessWokwiBridge.py${NC}"
    echo ""
    read -p "Update bridge.py from JumperlessWokwiBridge.py? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp JumperlessWokwiBridge.py jumperless_pkg/bridge.py
        echo -e "${GREEN}✓ bridge.py updated${NC}"
    else
        echo -e "${YELLOW}Continuing with existing bridge.py${NC}"
    fi
else
    echo -e "${GREEN}✓ bridge.py is up to date${NC}"
fi
echo ""

# Step 3: Clean and build
echo -e "${BLUE}Step 3: Building package...${NC}"
rm -rf dist/ build/ *.egg-info
"$(which python3)" -m build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi
echo ""

# Step 4: Check package integrity
echo -e "${BLUE}Step 4: Checking package integrity...${NC}"
"$(which python3)" -m twine check dist/*

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Package integrity check passed${NC}"
else
    echo -e "${RED}✗ Package integrity check failed${NC}"
    exit 1
fi
echo ""

# Step 5: Show package info
echo -e "${BLUE}Step 5: Package information${NC}"
echo "  Version:  $PYPROJECT_VERSION"
echo "  Files:"
ls -lh dist/
echo ""

# Step 6: Choose destination
echo -e "${YELLOW}Where would you like to upload?${NC}"
echo "  1) TestPyPI (recommended for first test)"
echo "  2) Production PyPI"
echo "  3) Skip upload (just build)"
echo ""
read -p "Enter choice (1-3): " -n 1 -r
echo
echo ""

case $REPLY in
    1)
        echo -e "${BLUE}Uploading to TestPyPI...${NC}"
        echo -e "${YELLOW}Note: Use __token__ as username and your TestPyPI token as password${NC}"
        echo ""
        "$(which python3)" -m twine upload --repository testpypi dist/*
        
        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✓ Upload successful!${NC}"
            echo ""
            echo -e "${BLUE}Test installation with:${NC}"
            echo -e "  ${YELLOW}pipx install --index-url https://test.pypi.org/simple/ --pip-args='--extra-index-url=https://pypi.org/simple/' jumperless${NC}"
            echo ""
            echo -e "${BLUE}Or with pip:${NC}"
            echo -e "  ${YELLOW}pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple jumperless${NC}"
        fi
        ;;
    2)
        echo -e "${RED}⚠️  UPLOADING TO PRODUCTION PYPI${NC}"
        echo -e "${YELLOW}This will make the package publicly available at https://pypi.org/project/jumperless/${NC}"
        echo ""
        read -p "Are you sure? (yes/no): " -r
        echo
        
        if [[ $REPLY == "yes" ]]; then
            echo -e "${BLUE}Uploading to PyPI...${NC}"
            echo -e "${YELLOW}Note: Use __token__ as username and your PyPI token as password${NC}"
            echo ""
            "$(which python3)" -m twine upload dist/*
            
            if [ $? -eq 0 ]; then
                echo ""
                echo -e "${GREEN}✨ SUCCESS! Package published to PyPI! ✨${NC}"
                echo ""
                echo -e "${BLUE}Users can now install with:${NC}"
                echo -e "  ${GREEN}pipx install jumperless${NC}"
                echo ""
                echo -e "${BLUE}Or with pip:${NC}"
                echo -e "  ${GREEN}pip install jumperless${NC}"
                echo ""
                echo -e "${BLUE}View on PyPI:${NC}"
                echo -e "  ${MAGENTA}https://pypi.org/project/jumperless/${NC}"
            fi
        else
            echo -e "${YELLOW}Upload cancelled${NC}"
        fi
        ;;
    3)
        echo -e "${BLUE}Upload skipped. Package built in dist/ directory.${NC}"
        ;;
    *)
        echo -e "${YELLOW}Invalid choice. Upload skipped.${NC}"
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC}"

