#!/bin/bash
set -e

# Round-trip flight search
# Usage: ./roundtrip.sh <origin> <destination> <days_from_now> <min_days> <max_days>

if ! command -v flights &> /dev/null; then
    echo "Error: flights CLI not found. Install with: pip install flightfinder" >&2
    exit 1
fi

ORIGIN="${1:?Usage: roundtrip.sh <origin> <destination> <days_from_now> <min_days> <max_days>}"
DESTINATION="${2:?Missing destination}"
DAYS="${3:-30}"
MIN_DAYS="${4:-7}"
MAX_DAYS="${5:-14}"

echo "Searching round-trips: $ORIGIN ⇄ $DESTINATION ($MIN_DAYS-$MAX_DAYS days)..." >&2

flights roundtrip "$ORIGIN" -d "$DESTINATION" --days "$DAYS" --min-days "$MIN_DAYS" --max-days "$MAX_DAYS" --format json
