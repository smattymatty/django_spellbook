#!/bin/bash
set -a
source .env
set +a

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Starting test and deployment process..."

# Extract and check version FIRST
echo "Checking version..."
version=$(grep -oP "version='\K[^']+" setup.py)
if [ -z "$version" ]; then
    echo -e "${RED}ERROR: Could not extract version from setup.py${NC}"
    exit 1
fi

echo "Current version: $version"

# Check if this version already exists on PyPI using the JSON API
echo "Checking if version exists on PyPI..."
http_code=$(curl -s -o /dev/null -w "%{http_code}" "https://pypi.org/pypi/django-spellbook/$version/json")

if [ "$http_code" = "200" ]; then
    echo -e "${RED}ERROR: Version $version already exists on PyPI!${NC}"
    echo "You must increment the version in setup.py before deploying."
    echo ""
    echo "Current version: $version"
    echo "Suggestion: Update to next version (e.g., 0.2.3b2 or 0.2.4)"
    exit 1
elif [ "$http_code" = "404" ]; then
    echo -e "${GREEN}Version $version is available.${NC}"
else
    echo -e "${YELLOW}Warning: Could not verify version on PyPI (HTTP $http_code). Continuing anyway...${NC}"
fi
echo ""

# Run the tests with coverage
echo "Running tests with coverage..."
coverage run manage.py test
test_status=$?

if [ $test_status -ne 0 ]; then
    echo -e "${RED}Tests failed! Aborting deployment.${NC}"
    exit 1
fi

# Check coverage percentage
coverage_output=$(coverage report | tail -n 1)
coverage_percentage=$(echo $coverage_output | grep -oP '\d+%' | grep -oP '\d+')

if [ "$coverage_percentage" -lt 90 ]; then
    echo -e "${RED}Coverage is below 90%! Current coverage: ${coverage_percentage}%${NC}"
    exit 1
fi

echo -e "${GREEN}All tests passed with 90% coverage!${NC}"

# Detect if this is a beta release (contains 'b' followed by number)
if [[ $version =~ b[0-9]+ ]]; then
    release_type="beta"
    branch_check_required=false
else
    release_type="release"
    branch_check_required=true
fi

# Display version and get confirmation
echo ""
echo "================================================"
echo "Version: $version ($release_type)"
current_branch=$(git branch --show-current)
echo "Branch: $current_branch"

# Check branch requirement for non-beta releases
if [ "$branch_check_required" = true ]; then
    if [ "$current_branch" != "main" ]; then
        echo -e "${RED}ERROR: Release versions must be deployed from main branch.${NC}"
        echo "Current branch: $current_branch"
        echo "Aborting."
        exit 1
    fi
else
    echo "Beta release - branch check skipped."
fi

echo "================================================"
echo -n "Deploy? (y/n): "
read -r response
echo ""

if [ "$response" != "y" ]; then
    echo "Deployment cancelled."
    exit 1
fi

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