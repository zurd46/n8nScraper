#!/bin/bash
# Test Docker build without actually building

echo "=========================================="
echo "Testing Docker Build Context"
echo "=========================================="
echo ""

echo "Files that will be copied to Docker image:"
echo "(excluding .dockerignore patterns)"
echo ""

# Simulate docker build context
echo "Checking .dockerignore patterns..."
if [ -f .dockerignore ]; then
    echo "✓ .dockerignore found"
    echo ""
    echo "Excluded patterns:"
    cat .dockerignore | grep -v "^#" | grep -v "^$"
    echo ""
else
    echo "⚠ No .dockerignore file"
fi

echo "=========================================="
echo "Files to be copied (from Dockerfile):"
echo "=========================================="
echo ""

echo "1. requirements.txt"
test -f requirements.txt && echo "   ✓ Found" || echo "   ✗ Missing!"

echo ""
echo "2. Python files (*.py)"
ls -1 *.py 2>/dev/null || echo "   ✗ No .py files!"

echo ""
echo "3. utils/ directory"
test -d utils && echo "   ✓ Found" || echo "   ✗ Missing!"

echo ""
echo "4. scripts/ directory"
test -d scripts && echo "   ✓ Found" || echo "   ✗ Missing!"

echo ""
echo "5. docker-entrypoint.sh"
test -f docker-entrypoint.sh && echo "   ✓ Found" || echo "   ✗ Missing!"

echo ""
echo "=========================================="
echo "Checking for potential issues..."
echo "=========================================="

# Check for symlinks
echo ""
echo "Checking for symlinks (potential issues):"
if command -v find &> /dev/null; then
    symlinks=$(find . -maxdepth 2 -type l 2>/dev/null | wc -l)
    if [ "$symlinks" -eq 0 ]; then
        echo "✓ No symlinks found in top-level directories"
    else
        echo "⚠ Found $symlinks symlink(s):"
        find . -maxdepth 2 -type l 2>/dev/null
    fi
else
    echo "⚠ find command not available, skipping symlink check"
fi

echo ""
echo "=========================================="
echo "Build Test Summary"
echo "=========================================="
echo ""
echo "To build the image:"
echo "  docker-compose -f docker-compose.nas.yml build"
echo ""
echo "To test build without cache:"
echo "  docker-compose -f docker-compose.nas.yml build --no-cache"
echo ""
