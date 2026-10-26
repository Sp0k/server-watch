FROM python:3.13-slim-bookworm

# Configure Python for container execution
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STATE_FILE=/data/watch_state.json

# Install trusted CA certificates for SMTP over TLS
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Application directory
WORKDIR /app

# Copy application source files
COPY main.py checker.py monitor.py notifier.py ./

# Create persistent data directory
RUN mkdir -p /data

# Start the monitor
CMD ["python", "main.py"]
