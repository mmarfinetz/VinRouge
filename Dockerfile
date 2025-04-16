FROM python:3.10-slim

# Updated Dockerfile with fixed poetry paths
WORKDIR /app

# Install build dependencies and curl
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy poetry files
COPY dexy/pyproject.toml ./pyproject.toml
COPY dexy/poetry.lock ./poetry.lock

# Configure poetry to not create virtual environments
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

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