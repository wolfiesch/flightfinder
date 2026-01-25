#!/bin/bash
set -e

# One-way flight search
# Usage: ./search.sh <origin> <destination> [days_from_now]

if ! command -v flights &> /dev/null; then
    echo "Error: flights CLI not found. Install with: pip install flightfinder" >&2
    exit 1
fi

ORIGIN="${1:?Usage: search.sh <origin> <destination> [days_from_now]}"
DESTINATION="${2:-anywhere}"
DAYS="${3:-30}"

echo "Searching flights: $ORIGIN → $DESTINATION (in $DAYS days)..." >&2

flights search "$ORIGIN" -d "$DESTINATION" --days "$DAYS" --format json
