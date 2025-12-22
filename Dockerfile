# FlightFinder Monitor Dockerfile
# For deployment on Fly.io or other container platforms

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install the package
RUN pip install --no-cache-dir -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default environment variables (can be overridden)
ENV MONITOR_INTERVAL=300
ENV MONITOR_DAYS_AHEAD=30
ENV MONITOR_SEARCH_WINDOW=14
ENV MONITOR_HEARTBEAT_INTERVAL=3600

# Run the monitor
CMD ["python", "-m", "flightfinder.monitor"]
