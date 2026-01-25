#!/bin/bash
set -e

# Airport/city location lookup
# Usage: ./location.sh <query>

if ! command -v flights &> /dev/null; then
    echo "Error: flights CLI not found. Install with: pip install flightfinder" >&2
    exit 1
fi

QUERY="${1:?Usage: location.sh <query>}"

echo "Looking up: $QUERY..." >&2

flights location "$QUERY" --format json
