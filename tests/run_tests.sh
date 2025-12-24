#!/bin/bash
#
# Test runner for membase test suite
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Membase Test Suite ===${NC}\n"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}pytest not found. Installing test dependencies...${NC}"
    pip install -q -r requirements.txt
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Parse arguments
COVERAGE=false
VERBOSE=false
PATTERN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --pattern|-p)
            PATTERN="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest"

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=../scripts/mb --cov-report=term --cov-report=html"
fi

if [ -n "$PATTERN" ]; then
    PYTEST_CMD="$PYTEST_CMD -k $PATTERN"
fi

# Run tests
echo -e "${GREEN}Running tests...${NC}\n"
$PYTEST_CMD

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"

    if [ "$COVERAGE" = true ]; then
        echo -e "${GREEN}Coverage report saved to htmlcov/index.html${NC}"
    fi
else
    echo -e "\n${RED}✗ Some tests failed${NC}"
fi

exit $EXIT_CODE
