FROM python:3.10-slim

# Updated Dockerfile to use pip for dependencies
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create data directory with proper permissions
RUN mkdir -p /data && chmod 777 /data
RUN mkdir -p /root/Downloads && chmod 777 /root/Downloads

# Copy project files
COPY dexy/ ./dexy/
COPY gunicorn.conf.py .

# Create startup script
RUN echo '#!/bin/bash\n\
python /app/dexy/init_cdp.py\n\
exec python -m gunicorn -c /app/gunicorn.conf.py server:app --pythonpath /app/dexy\n\
' > /app/start.sh && chmod +x /app/start.sh

# Install dependencies directly with pip
WORKDIR /app/dexy
RUN pip install --no-cache-dir -r requirements.txt

# Move back to app directory
WORKDIR /app

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PRODUCTION=1

# Create CDP API key file from environment variable
RUN echo 'Creating CDP key file placeholder'
RUN echo '{}' > /root/Downloads/cdp_api_key.json
RUN chmod 600 /root/Downloads/cdp_api_key.json

# Debug logging for environment variables
RUN echo "Environment variables will be injected by Railway at runtime"
# Note: OPENAI_API_KEY should be set in Railway dashboard

# Expose port
EXPOSE 8080

# Set the startup command
CMD ["/app/start.sh"] 