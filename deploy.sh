#!/bin/bash
set -a
source .env
set +a

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "Starting test and deployment process..."

# Run the tests with coverage
echo "Running tests with coverage..."
coverage run -m unittest
test_status=$?

if [ $test_status -ne 0 ]; then
    echo -e "${RED}Tests failed! Aborting deployment.${NC}"
    exit 1
fi

# Check coverage percentage
coverage_output=$(coverage report | tail -n 1)
coverage_percentage=$(echo $coverage_output | grep -oP '\d+%' | grep -oP '\d+')

if [ "$coverage_percentage" -lt 100 ]; then
    echo -e "${RED}Coverage is below 100%! Current coverage: ${coverage_percentage}%${NC}"
    exit 1
fi

echo -e "${GREEN}All tests passed with 100% coverage!${NC}"

echo "Cleaning up generated files..."

rm -f django_spellbook/urls_*.py django_spellbook/views_*.py

# Reset urls.py to clean state
echo "Resetting urls.py to clean state..."
cat > django_spellbook/urls.py << 'EOF'
from django.urls import path, include

urlpatterns = [
    
]
EOF

# Clean up old distribution files
echo "Cleaning up old distribution files..."
rm -rf dist/ build/ *.egg-info

# Build new distribution
echo "Building new distribution..."
python -m build
build_status=$?

if [ $build_status -ne 0 ]; then
    echo -e "${RED}Build failed! Aborting deployment.${NC}"
    exit 1
fi

# Upload to PyPI
echo "Uploading to PyPI..."
python -m twine upload dist/* -u __token__ -p "$PYPI_KEY" --verbose
upload_status=$?

if [ $upload_status -ne 0 ]; then
    echo -e "${RED}Upload to PyPI failed!${NC}"
    exit 1
fi

echo -e "${GREEN}Successfully deployed to PyPI!${NC}"