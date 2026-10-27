# Lightweight official Python 3.11 image
FROM python:3.11-slim

# Prevent Python from writing pyc files and buffer logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Set working directory
WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose web dashboard port
EXPOSE 5000

# Container healthcheck using the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5000}/health || exit 1

# Start the bot service & dashboard
CMD ["python", "main.py"]
