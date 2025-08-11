#!/bin/bash

# Check if STOCKFISH_ENGINE_PATH is set
if [ -z "$STOCKFISH_ENGINE_PATH" ]; then
    echo "Error env STOCKFISH_ENGINE_PATH not set, it needs to be set and point towards a stockfish binary executable."
    exit 1
fi

# Check if the file exists
if [ ! -f "$STOCKFISH_ENGINE_PATH" ]; then
    echo "Error: File '$STOCKFISH_ENGINE_PATH' does not exist."
    exit 1
fi

echo "Stockfish engine found at: $STOCKFISH_ENGINE_PATH"

source ./myenv/bin/activate

python3 src/flask_review_server.py
