FROM python:3.11-slim AS base

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# OpenShift runs containers with a random non-root UID by default
# Set proper permissions for OpenShift
RUN chgrp -R 0 /app && chmod -R g=u /app

# Expose port
EXPOSE 8000

# Set environment variables
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Start the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
