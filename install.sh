#!/bin/bash

# Fail-fast options: exit on error, undefined var, or failed pipe
set -euo pipefail
IFS=$'\n\t'

if command -v python3 >/dev/null 2>&1; then
    python3 --version
else
    echo "Python 3 is not installed." >&2
    exit 1
fi

echo "Installing python requirements"
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt


echo "Initializing submodules"
git submodule update --init --recursive


echo "Installing submodule requirements"
# if the submodule folder exists, install its requirements; otherwise fail
if [ -f "src/stockfish_fork/requirements.txt" ]; then
    pip install -r src/stockfish_fork/requirements.txt
else
    echo "Warning: src/stockfish_fork/requirements.txt not found" >&2
    # fail because downstream steps expect the submodule
    exit 1
fi


echo "Creating DB"

if [ -f "SQL/chess_games.db" ]; then
    echo "SQL/chess_games.db already exists.. Exiting"
    exit 1
fi

python3 SQL/createTable.py
if [ -f "SQL/chess_games.db" ]; then
    echo "Database file created SQL/chess_games.db"
else
    echo "Error: DB file SQL/chess_games.db could not be created." >&2
    exit 1
fi


echo "Install Done!"

echo "\nStart server with ./start_review_server.sh"
