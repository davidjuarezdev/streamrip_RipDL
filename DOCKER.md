# Docker Deployment Guide for streamrip

This guide covers running streamrip in containerized environments using Docker and Docker Compose.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Building the Image](#building-the-image)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Volume Mounts](#volume-mounts)
- [User Permissions](#user-permissions)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker Engine 20.10+ or Docker Desktop
- Docker Compose 2.0+ (optional, for easier usage)
- At least 1GB free disk space for the image
- Additional space for music downloads

## Quick Start

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/nathom/streamrip.git
   cd streamrip
   ```

2. **Create required directories**:
   ```bash
   mkdir -p config downloads
   ```

3. **Build the Docker image**:
   ```bash
   docker-compose build
   ```

4. **Run streamrip**:
   ```bash
   docker-compose run --rm streamrip --help
   ```

## Building the Image

### Using Docker Compose (Recommended)

```bash
# Build with your user ID to avoid permission issues
USER_ID=$(id -u) GROUP_ID=$(id -g) docker-compose build
```

### Using Docker CLI

```bash
# Build with default user (UID 1000, GID 1000)
docker build -t streamrip:latest .

# Build with your specific user ID
docker build \
  --build-arg USER_ID=$(id -u) \
  --build-arg GROUP_ID=$(id -g) \
  -t streamrip:latest .
```

## Usage Examples

### With Docker Compose

#### Download a URL
```bash
docker-compose run --rm streamrip url "https://www.qobuz.com/us-en/album/..."
```

#### Interactive Search
```bash
docker-compose run --rm streamrip search qobuz album "fleetwood mac rumours"
```

#### Download with Specific Quality
```bash
docker-compose run --rm streamrip --quality 3 url "https://tidal.com/browse/album/..."
```

#### Download Entire Discography
```bash
docker-compose run --rm streamrip search qobuz artist "pink floyd" --download-discography
```

### With Docker CLI

```bash
# Download a URL
docker run -it --rm \
  -v $(pwd)/config:/home/streamrip/.config/streamrip \
  -v $(pwd)/downloads:/home/streamrip/downloads \
  streamrip:latest url "https://www.qobuz.com/us-en/album/..."

# Interactive search
docker run -it --rm \
  -v $(pwd)/config:/home/streamrip/.config/streamrip \
  -v $(pwd)/downloads:/home/streamrip/downloads \
  streamrip:latest search tidal album "artist name"
```

## Configuration

### First-Time Setup

On first run, streamrip will create a default configuration file. To set it up:

1. **Generate config file**:
   ```bash
   docker-compose run --rm streamrip config --setup
   ```

2. **Edit the configuration**:
   ```bash
   # The config file is created at ./config/config.toml
   nano config/config.toml
   ```

3. **Add your credentials** for each service you want to use:
   - **Qobuz**: Email/password or auth token
   - **Tidal**: OAuth tokens (run `rip login tidal` in container)
   - **Deezer**: ARL cookie
   - **SoundCloud**: client_id and app_version

### Configuration File Location

- **Host**: `./config/config.toml`
- **Container**: `/home/streamrip/.config/streamrip/config.toml`

### Login to Services

```bash
# Login to Tidal (interactive OAuth)
docker-compose run --rm streamrip login tidal

# Login to Qobuz
docker-compose run --rm streamrip login qobuz

# Login to Deezer
docker-compose run --rm streamrip login deezer
```

## Volume Mounts

The container uses two main volume mounts:

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `./config` | `/home/streamrip/.config/streamrip` | Configuration files, credentials, and download database |
| `./downloads` | `/home/streamrip/downloads` | Downloaded music files |

### Custom Volume Paths

Edit `docker-compose.yml` to use different paths:

```yaml
volumes:
  - /path/to/your/config:/home/streamrip/.config/streamrip
  - /path/to/your/music:/home/streamrip/downloads
```

## User Permissions

### Why User Permissions Matter

By default, files created in Docker containers are owned by root. This can cause permission issues when accessing downloaded files from your host system.

### Setting Your User ID

The Dockerfile supports build arguments to match your host user:

```bash
# Automatic (recommended)
USER_ID=$(id -u) GROUP_ID=$(id -g) docker-compose build

# Manual
docker build \
  --build-arg USER_ID=1000 \
  --build-arg GROUP_ID=1000 \
  -t streamrip:latest .
```

### Fixing Permission Issues

If you encounter permission problems:

```bash
# Option 1: Rebuild with correct user ID
USER_ID=$(id -u) GROUP_ID=$(id -g) docker-compose build --no-cache

# Option 2: Fix ownership of existing files
sudo chown -R $(id -u):$(id -g) config downloads
```

## Advanced Usage

### Running as a Daemon (Background Service)

While streamrip is primarily a CLI tool, you can create a wrapper service:

```yaml
# docker-compose.daemon.yml
version: '3.8'
services:
  streamrip-watch:
    build: .
    volumes:
      - ./config:/home/streamrip/.config/streamrip
      - ./downloads:/home/streamrip/downloads
      - ./queue:/home/streamrip/queue
    command: /bin/bash -c "while true; do sleep 60; done"
    restart: unless-stopped
```

### Batch Processing

Create a file with URLs and process them:

```bash
# Create urls.txt with one URL per line
cat > urls.txt << EOF
https://www.qobuz.com/us-en/album/...
https://tidal.com/browse/album/...
EOF

# Process all URLs
docker-compose run --rm streamrip file urls.txt
```

### Using Environment Variables for Config

```bash
# Set environment variables
export STREAMRIP_CONFIG=/home/streamrip/.config/streamrip/config.toml

# Use in docker-compose.yml
environment:
  - STREAMRIP_CONFIG=${STREAMRIP_CONFIG}
```

### Custom Configuration Path

```bash
docker-compose run --rm \
  -v $(pwd)/custom-config.toml:/home/streamrip/custom-config.toml \
  streamrip --config /home/streamrip/custom-config.toml url "..."
```

### Multi-Platform Builds

Build for multiple architectures (requires Docker Buildx):

```bash
# Create builder
docker buildx create --name streamrip-builder --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t streamrip:latest \
  --load \
  .
```

## Troubleshooting

### Issue: "Permission denied" when accessing downloads

**Solution**: Rebuild the image with your user ID:
```bash
USER_ID=$(id -u) GROUP_ID=$(id -g) docker-compose build
```

### Issue: "Config file not found"

**Solution**: Run initial setup:
```bash
docker-compose run --rm streamrip config --setup
```

### Issue: Interactive menus not working

**Solution**: Ensure TTY is enabled (already configured in docker-compose.yml):
```bash
docker-compose run --rm streamrip search ...
# Or with docker:
docker run -it --rm ... streamrip search ...
```

### Issue: "ffmpeg not found"

**Solution**: This should not occur as ffmpeg is installed in the Dockerfile. If it does:
```bash
# Rebuild the image
docker-compose build --no-cache
```

### Issue: Downloads are slow

**Solution**:
- Check your internet connection
- Verify no rate limiting in config.toml
- Consider increasing concurrent downloads in config

### Issue: "Authentication failed"

**Solution**:
1. Check credentials in `config/config.toml`
2. Re-run login for the service:
   ```bash
   docker-compose run --rm streamrip login [service]
   ```
3. For Tidal, tokens expire after 1 week - login again

### Issue: Container can't reach internet

**Solution**: Check Docker network settings:
```bash
# Test connectivity
docker-compose run --rm streamrip sh -c "ping -c 3 google.com"

# If using custom networks, ensure proper DNS
docker-compose run --rm streamrip sh -c "cat /etc/resolv.conf"
```

### Viewing Logs

```bash
# See container logs
docker-compose logs streamrip

# Follow logs in real-time
docker-compose logs -f streamrip
```

### Cleaning Up

```bash
# Remove stopped containers
docker-compose down

# Remove images
docker rmi streamrip:latest

# Remove all (containers, images, volumes)
docker-compose down -v --rmi all
```

## Performance Optimization

### Image Size Optimization

The multi-stage build already optimizes image size. Current size is approximately:
- Base image (python:3.10-slim): ~130 MB
- With ffmpeg and dependencies: ~250-300 MB

### Build Cache

```bash
# Use BuildKit for better caching
DOCKER_BUILDKIT=1 docker build -t streamrip:latest .

# Clear build cache if needed
docker builder prune
```

### Download Performance

- Adjust `concurrent_downloads` in config.toml
- Use SSD storage for download directory
- Ensure sufficient network bandwidth

## Security Considerations

1. **Credentials Storage**: The `config/config.toml` file contains sensitive API tokens
   - Keep this directory secure
   - Add `config/` to `.gitignore`
   - Consider using Docker secrets for production

2. **Network Security**: Container needs outbound internet access
   - No inbound ports are required
   - Consider using a firewall for additional security

3. **User Isolation**: Running as non-root user (streamrip)
   - Reduces security risk
   - Prevents privilege escalation

## Additional Resources

- [streamrip Documentation](https://github.com/nathom/streamrip)
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## Support

For issues specific to:
- **streamrip functionality**: Open an issue on the [streamrip GitHub](https://github.com/nathom/streamrip/issues)
- **Docker setup**: Check this guide first, then open an issue with Docker-specific details
