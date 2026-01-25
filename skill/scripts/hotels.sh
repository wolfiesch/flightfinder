#!/bin/bash
set -e

# Hotel search
# Usage: ./hotels.sh <city> [max_price] [min_rating]

if ! command -v flights &> /dev/null; then
    echo "Error: flights CLI not found. Install with: pip install flightfinder" >&2
    exit 1
fi

CITY="${1:?Usage: hotels.sh <city> [max_price] [min_rating]}"
MAX_PRICE="${2:-}"
MIN_RATING="${3:-}"

echo "Searching hotels in: $CITY..." >&2

CMD="flights hotels \"$CITY\" --format json"

if [ -n "$MAX_PRICE" ]; then
    CMD="$CMD --max-price $MAX_PRICE"
fi

if [ -n "$MIN_RATING" ]; then
    CMD="$CMD --min-rating $MIN_RATING"
fi

eval "$CMD"
