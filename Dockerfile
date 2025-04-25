FROM python:3.10-slim

# Updated Dockerfile to use pip for dependencies
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY dexy/ ./dexy/
COPY gunicorn.conf.py .

# Install dependencies directly with pip
WORKDIR /app/dexy
RUN pip install --no-cache-dir -r requirements.txt

# Move back to app directory
WORKDIR /app

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PRODUCTION=1

# Debug logging for environment variables
RUN echo "Environment variables will be injected by Railway at runtime"
# Note: OPENAI_API_KEY should be set in Railway dashboard

# Expose port
EXPOSE 8080

# No CMD directive - we use the startCommand in railway.json 