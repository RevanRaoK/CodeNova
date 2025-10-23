#!/bin/bash

# Frontend Test Runner Script
# This script runs all frontend tests with various options

set -e

echo "🧪 Frontend Test Suite Runner"
echo "=============================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_warning "node_modules not found. Installing dependencies..."
    npm install
fi

# Parse command line arguments
TEST_TYPE=${1:-all}

case $TEST_TYPE in
    "all")
        print_status "Running all tests..."
        npm test -- --run
        ;;
    
    "components")
        print_status "Running component tests..."
        npm test -- --run components/__tests__/
        ;;
    
    "forms")
        print_status "Running form component tests..."
        npm test -- --run components/forms/__tests__/
        ;;
    
    "settings")
        print_status "Running settings component tests..."
        npm test -- --run components/settings/__tests__/
        ;;
    
    "services")
        print_status "Running service tests..."
        npm test -- --run services/__tests__/
        ;;
    
    "utils")
        print_status "Running utility tests..."
        npm test -- --run utils/__tests__/
        ;;
    
    "pages")
        print_status "Running page tests..."
        npm test -- --run pages/__tests__/
        ;;
    
    "integration")
        print_status "Running integration tests..."
        npm test -- --run __tests__/integration/
        ;;
    
    "e2e")
        print_status "Running end-to-end tests..."
        npm test -- --run __tests__/e2e/
        ;;
    
    "coverage")
        print_status "Running tests with coverage..."
        npm test -- --run --coverage
        ;;
    
    "watch")
        print_status "Running tests in watch mode..."
        npm test -- --watch
        ;;
    
    "ui")
        print_status "Opening test UI..."
        npm run test:ui
        ;;
    
    *)
        echo "Usage: ./run-tests.sh [option]"
        echo ""
        echo "Options:"
        echo "  all          - Run all tests (default)"
        echo "  components   - Run component tests"
        echo "  forms        - Run form component tests"
        echo "  settings     - Run settings component tests"
        echo "  services     - Run service tests"
        echo "  utils        - Run utility tests"
        echo "  pages        - Run page tests"
        echo "  integration  - Run integration tests"
        echo "  e2e          - Run end-to-end tests"
        echo "  coverage     - Run tests with coverage report"
        echo "  watch        - Run tests in watch mode"
        echo "  ui           - Open interactive test UI"
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    print_success "Tests completed successfully!"
else
    echo "❌ Tests failed!"
    exit 1
fi
