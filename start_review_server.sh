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

# Parse arguments: support -d or --debug to run server in debug mode
DEBUG_FLAG=0
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -d|--debug)
            DEBUG_FLAG=1
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [-d|--debug]"
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: $0 [-d|--debug]"
            exit 1
            ;;
    esac
done

if [ "$DEBUG_FLAG" -eq 1 ]; then
    echo "Starting review server in debug mode"
    python3 src/flask_review_server.py --debug
else
    echo "Starting review server"
    python3 src/flask_review_server.py
fi
