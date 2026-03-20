FROM python:3.12-slim

WORKDIR /app

# Copy bot and config
COPY cadence.py ./
COPY config.json ./
COPY .env ./

# Create directories
RUN mkdir -p logs commands

# Copy optional files if they exist (won't fail if missing)
COPY commands/ ./commands/ 2>/dev/null || true

# Default: run the listener
CMD ["python3", "cadence.py", "listen"]
