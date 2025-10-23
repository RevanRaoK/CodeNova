#!/bin/bash

# Quick Fix Script for Test Import Issues
# This script fixes the "ModuleNotFoundError: No module named 'app'" error

echo "========================================="
echo "CodeNova Test Import Fix"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the backend directory
if [ ! -d "app" ]; then
    echo -e "${YELLOW}Warning: 'app' directory not found${NC}"
    echo "Please run this script from the backend directory:"
    echo "  cd backend"
    echo "  ./fix_test_imports.sh"
    exit 1
fi

echo -e "${BLUE}Step 1: Installing backend package in development mode...${NC}"
pip install -e .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backend package installed successfully${NC}"
else
    echo -e "${YELLOW}⚠ Package installation had issues, trying alternative fix...${NC}"
    echo ""
    echo -e "${BLUE}Setting PYTHONPATH environment variable...${NC}"
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    echo "export PYTHONPATH=\"\${PYTHONPATH}:$(pwd)\"" >> ~/.bashrc
    echo -e "${GREEN}✓ PYTHONPATH set and added to ~/.bashrc${NC}"
fi

echo ""
echo -e "${BLUE}Step 2: Verifying imports...${NC}"
python -c "from app.main import app; print('✓ Import test successful!')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All imports working correctly!${NC}"
else
    echo -e "${YELLOW}⚠ Import test failed. Trying with PYTHONPATH...${NC}"
    PYTHONPATH=. python -c "from app.main import app; print('✓ Import test successful with PYTHONPATH!')"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Imports work with PYTHONPATH set${NC}"
        echo ""
        echo "To run tests, use:"
        echo "  PYTHONPATH=. pytest tests/e2e/ -v"
        echo "  or"
        echo "  export PYTHONPATH=."
        echo "  ./tests/run_e2e_tests.sh"
    else
        echo -e "${YELLOW}⚠ Import issues persist. See TROUBLESHOOTING_IMPORTS.md${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}Step 3: Making test script executable...${NC}"
chmod +x tests/run_e2e_tests.sh
echo -e "${GREEN}✓ Test script is now executable${NC}"

echo ""
echo "========================================="
echo -e "${GREEN}Fix Complete!${NC}"
echo "========================================="
echo ""
echo "You can now run tests with:"
echo "  ./tests/run_e2e_tests.sh --e2e-only"
echo ""
echo "Or with pytest directly:"
echo "  pytest tests/e2e/ -v"
echo ""
