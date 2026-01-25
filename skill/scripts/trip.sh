#!/bin/bash
set -e

# Combined flight + hotel trip search
# Usage: ./trip.sh <origin> <destination> <days_from_now> <nights>

if ! command -v flights &> /dev/null; then
    echo "Error: flights CLI not found. Install with: pip install flightfinder" >&2
    exit 1
fi

ORIGIN="${1:?Usage: trip.sh <origin> <destination> <days_from_now> <nights>}"
DESTINATION="${2:?Missing destination}"
DAYS="${3:-30}"
NIGHTS="${4:-7}"

echo "Planning trip: $ORIGIN → $DESTINATION ($NIGHTS nights)..." >&2

flights trip "$ORIGIN" "$DESTINATION" --days "$DAYS" --nights "$NIGHTS" --format json
