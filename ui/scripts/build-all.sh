#!/bin/bash
# Build all MCP App views as single-file HTML bundles

set -e

cd "$(dirname "$0")/.."

echo "Building FlightFinder MCP Apps UI..."

# Clean and create dist
rm -rf dist
mkdir -p dist

# Temp directory for individual builds
TMPBUILD=$(mktemp -d)
trap "rm -rf $TMPBUILD" EXIT

# Build each view
for view in flights roundtrip hotels trip locations; do
  echo "  Building $view..."

  # Build to temp directory
  VIEW=$view npx vite build --outDir "$TMPBUILD" --emptyOutDir 2>&1 | grep -E "(building|transformed|built)" || true

  # Find and copy the output file
  output_file=$(find "$TMPBUILD" -name "*.html" -type f 2>/dev/null | head -1)
  if [ -n "$output_file" ] && [ -f "$output_file" ]; then
    cp "$output_file" "dist/$view.html"
    echo "    -> dist/$view.html ($(du -h "dist/$view.html" | cut -f1))"
  else
    echo "    ERROR: No HTML file found in build output"
    exit 1
  fi
done

echo ""
echo "Build complete! Output files:"
ls -lh dist/*.html

echo ""
echo "Total size: $(du -sh dist | cut -f1)"
