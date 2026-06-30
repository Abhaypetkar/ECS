# Use Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Expose the port
EXPOSE 5000

# Environment variables (can be overridden)
ENV MAX_WORKERS=3
ENV INSTANCE_ID=default

# Run with Gunicorn for production (multi-worker!)
# --workers=3  -> 3 worker processes (multi-threading/processing)
# --threads=2  -> 2 threads per worker
# This means each container can handle 6 concurrent requests
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--threads", "2", "--timeout", "120", "app:app"]
