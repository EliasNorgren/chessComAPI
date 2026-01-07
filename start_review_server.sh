#!/bin/bash

# Fail-fast options
set -euo pipefail
IFS=$'\n\t'

# Check if STOCKFISH_ENGINE_PATH is set
if [ -z "${STOCKFISH_ENGINE_PATH:-}" ]; then
    echo "Error: env STOCKFISH_ENGINE_PATH not set; it must point to a stockfish binary." >&2
    exit 1
fi

# Check if the file exists
if [ ! -f "$STOCKFISH_ENGINE_PATH" ]; then
    echo "Error: File '$STOCKFISH_ENGINE_PATH' does not exist." >&2
    exit 1
fi
echo "Stockfish engine found at: $STOCKFISH_ENGINE_PATH"

if [ ! -f ./myenv/bin/activate ]; then
    echo "Error: virtualenv activation script ./myenv/bin/activate not found. Run install.sh first." >&2
    exit 1
fi

source ./myenv/bin/activate

# Parse arguments: support -d or --debug to run server in debug mode
DEBUG_FLAG=0
PORT=5000
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -d|--debug)
            DEBUG_FLAG=1
            shift
            ;;
        -p|--port)
            if [ "$#" -lt 2 ]; then
                echo "Error: missing value for $1" >&2
                echo "Usage: $0 [-d|--debug] [-p|--port PORT]" >&2
                exit 1
            fi
            PORT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [-d|--debug] [-p|--port PORT]"
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            echo "Usage: $0 [-d|--debug] [-p|--port PORT]" >&2
            exit 1
            ;;
    esac
done

if [ "$DEBUG_FLAG" -eq 1 ]; then
    echo "Starting review server in debug mode"
    python3 src/flask_review_server.py --debug --port "$PORT"
else
    echo "Starting review server"
    python3 src/flask_review_server.py --port "$PORT"
fi
