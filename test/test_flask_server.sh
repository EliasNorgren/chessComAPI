#!/bin/bash

set -euo pipefail

# Port to use for the test
PORT=5001

# Check that port is free
if lsof -i:"$PORT" >/dev/null 2>&1; then
	echo "Error: Port $PORT is already in use. Please free it before running"
	exit 1
fi

# start in background (non-debug mode to avoid the reloader spawning extra PIDs)
nohup ./start_review_server.sh -p "$PORT" > server.log 2>&1 &
echo $! > server.pid

# wait until server responds, but give up after MAX_ATTEMPTS
MAX_ATTEMPTS=10
ATTEMPT=0
PID=$(cat server.pid)
URL="http://127.0.0.1:${PORT}/review_data?user=helloyou2g&id=141897647477"

while [ "$ATTEMPT" -lt "$MAX_ATTEMPTS" ]; do
	# if server process died, show logs and exit
	if ! kill -0 "$PID" 2>/dev/null; then
		echo "Server process $PID exited unexpectedly. Showing last 200 lines of server.log:" >&2
		tail -n 200 server.log >&2 || true
		exit 1
	fi

	if curl -sSf "$URL" -o server_response.json; then
		echo "Server responded on attempt $((ATTEMPT+1)) - saved response to server_response.json"
        
		break
	fi

	ATTEMPT=$((ATTEMPT+1))
	sleep 1
done

if [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; then
	echo "Server did not become ready after $MAX_ATTEMPTS attempts. Showing last 200 lines of server.log:" >&2
	tail -n 200 server.log >&2 || true
	# attempt cleanup below and then exit
	:
fi

MAX_ATTEMPTS=10
ATTEMPT=0

while [ "$ATTEMPT" -lt "$MAX_ATTEMPTS" ]; do
    # check that the response file exists and is non-empty
    response_uuid=$(jq -r '.uuid' server_response.json || echo "")
    url="http://127.0.0.1:${PORT}//get_entry_status?uuid=${response_uuid}"
    status_response=$(curl -sSf "$url" || echo "")
    # check if status is "loading"
    if echo "$status_response" | grep -q "loading"; then
        echo "Entry is still loading..."
        echo "Status response: $status_response"
    else
        echo "Entry has finished loading."
        echo $status_response > final_status_response.json
        break
    fi
    ATTEMPT=$((ATTEMPT+1))
    sleep 3
done

# Verifications of final response

# Basic sanity checks on final_status_response.json
if [ ! -f final_status_response.json ]; then
	echo "Error: final_status_response.json not found" >&2
	exit 1
fi

# ensure jq is available
if ! command -v jq >/dev/null 2>&1; then
	echo "Error: 'jq' is required for JSON assertions" >&2
	exit 1
fi

user=$(jq -r '.user' final_status_response.json)
if [ "$user" != "helloyou2g" ]; then
	echo "Assertion failed: user expected 'helloyou2g', got '$user'" >&2
	exit 1
fi

user_result=$(jq -r '.user_result' final_status_response.json)
if [ "$user_result" != "win" ]; then
	echo "Assertion failed: user_result expected 'win', got '$user_result'" >&2
	exit 1
fi

user_playing_as_white=$(jq -r '.user_playing_as_white' final_status_response.json)
if [ "$user_playing_as_white" -ne 1 ]; then
	echo "Assertion failed: user_playing_as_white expected 1, got '$user_playing_as_white'" >&2
	exit 1
fi

user_rating=$(jq -r '.user_rating' final_status_response.json)
if [ "$user_rating" -ne 2015 ]; then
	echo "Assertion failed: user_rating expected 2015, got '$user_rating'" >&2
	exit 1
fi

white_accuracy=$(jq -r '.white_accuracy' final_status_response.json)
awk -v v="$white_accuracy" 'BEGIN{if (v+0 >= 90) exit 0; exit 1}' || {
	echo "Assertion failed: white_accuracy expected >= 90, got $white_accuracy" >&2
	exit 1
}

black_accuracy=$(jq -r '.black_accuracy' final_status_response.json)
awk -v v="$black_accuracy" 'BEGIN{if (v+0 >= 80) exit 0; exit 1}' || {
	echo "Assertion failed: black_accuracy expected >= 80, got $black_accuracy" >&2
	exit 1
}

analysis_len=$(jq '.analysis | length' final_status_response.json)
if [ "$analysis_len" -lt 1 ]; then
	echo "Assertion failed: analysis array is empty" >&2
	exit 1
fi

first_best_move=$(jq -r '.analysis[0].best_move_uci' final_status_response.json)
if [ "$first_best_move" != "e2e4" ]; then
	echo "Assertion failed: first analysis best_move_uci expected 'e2e4', got '$first_best_move'" >&2
	exit 1
fi

url=$(jq -r '.url' final_status_response.json)
if [ "$url" != "https://www.chess.com/game/live/141897647477" ]; then
	echo "Assertion failed: url expected 'https://www.chess.com/game/live/141897647477', got '$url'" >&2
	exit 1
fi

echo "All JSON verifications passed."


# cleanup: stop any process listening on the test port (graceful then force)
PIDS=$(lsof -ti :"$PORT" || true)
if [ -n "$PIDS" ]; then
	echo "Stopping processes on port $PORT: $PIDS"
	kill $PIDS 2>/dev/null || true
	# wait up to 5s for processes to exit
	for i in 1 2 3 4 5; do
		sleep 1
		PIDS=$(lsof -ti :"$PORT" || true)
		if [ -z "$PIDS" ]; then
			break
		fi
	done
	PIDS=$(lsof -ti :"$PORT" || true)
	if [ -n "$PIDS" ]; then
		echo "Processes did not exit, force killing: $PIDS"
		kill -9 $PIDS 2>/dev/null || true
	fi
fi

# remove pid file if present
rm -f server.pid

# if test previously failed to become ready, exit with error now
if [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; then
	exit 1
fi
