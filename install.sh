#!/bin/bash


if command -v python3 >/dev/null 2>&1; then
    python3 --version
else
    echo "Python 3 is not installed."
    exit 1
fi

echo "Installing python requirements"
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt

echo "Creating DB"

if [ -f "SQL/chess_games.db" ]; then
    echo "SQL/chess_games.db already exists.. Exiting"
    exit 1
fi

python3 SQL/createTable.py
if [ -f "SQL/chess_games.db" ]; then
    echo "Database file created SQL/chess_games.db"
else
    echo "Error: DB file SQL/chess_games.db could not be created."
    exit 1
fi


echo "Install Done!"

echo "\nStart server with ./start_review_server.py"
