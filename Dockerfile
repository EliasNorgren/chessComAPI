FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY SQL/ ./SQL/

RUN rm -rf src/__pycache__
RUN rm -rf src/builds
RUN rm -rf SQL/chess_games.db

ENV STOCKFISH_ENGINE_PATH=src/stockfish-ubuntu-x86-64-avx2
ENV FLASK_PORT=5000

EXPOSE 5000

CMD ["python3", "src/flask_review_server.py"]
