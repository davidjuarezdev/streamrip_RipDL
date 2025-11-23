# Multi-stage Dockerfile for streamrip
# Stage 1: Builder - Install Poetry and export dependencies
FROM python:3.10-slim as builder

# Install Poetry
RUN pip install --no-cache-dir poetry==1.5.1

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Export dependencies to requirements.txt (excluding dev dependencies)
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes --without dev

# Stage 2: Runtime - Install application and dependencies
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create user arguments for file permissions
ARG USER_ID=1000
ARG GROUP_ID=1000

# Create non-root user
RUN groupadd -g ${GROUP_ID} streamrip && \
    useradd -u ${USER_ID} -g ${GROUP_ID} -m -s /bin/bash streamrip

# Set working directory
WORKDIR /app

# Copy requirements from builder stage
COPY --from=builder /app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY --chown=streamrip:streamrip . .

# Install streamrip from local source
RUN pip install --no-cache-dir .

# Switch to non-root user
USER streamrip

# Create directories for config and downloads
RUN mkdir -p /home/streamrip/.config/streamrip && \
    mkdir -p /home/streamrip/downloads

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/streamrip

# Default working directory for downloads
WORKDIR /home/streamrip/downloads

# Volume mount points
VOLUME ["/home/streamrip/.config/streamrip", "/home/streamrip/downloads"]

# Default command
ENTRYPOINT ["rip"]
CMD ["--help"]
