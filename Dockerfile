FROM python:3.10-slim

# Updated Dockerfile with simplified approach
WORKDIR /app

# Install build dependencies and curl
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# First copy just the requirements file
COPY dexy/requirements.txt ./requirements.txt

# Install dependencies directly with pip instead of poetry
RUN pip install --no-cache-dir -r requirements.txt

# Add gunicorn for production
RUN pip install gunicorn

# Copy app code
COPY dexy/ .

# Set environment variables
ENV PORT=5050
ENV PYTHONUNBUFFERED=1
ENV PRODUCTION=1

# Debug logging for environment variables
RUN echo "Environment variables will be injected by Railway at runtime"
# Note: OPENAI_API_KEY should be set in Railway dashboard

# Expose port
EXPOSE 5050

# No CMD directive - we use the startCommand in railway.json 