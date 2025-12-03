# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

Streamrip is a Python-based CLI tool for downloading high-quality music from streaming services (Qobuz, Tidal, Deezer, SoundCloud). The project uses Poetry for dependency management and async/await patterns throughout.

## Common Development Commands

### Setup and Installation
```bash
poetry install                    # Install dependencies
poetry install --with dev         # Install with dev dependencies
poetry shell                      # Activate virtual environment
```

### Running the Application
```bash
poetry run rip                    # Run CLI tool
poetry run rip --help             # Show help
poetry run rip config open        # Open config file
```

### Testing
```bash
poetry run pytest                 # Run all tests
poetry run pytest tests/test_specific.py  # Run specific test file
poetry run pytest -v              # Verbose test output
poetry run pytest -x              # Stop on first failure
```

### Code Quality and Formatting
```bash
ruff check .                      # Lint with Ruff
ruff format .                     # Format with Ruff
black .                          # Format with Black (alternative)
isort .                          # Sort imports
```

### Development Testing
```bash
# Test with different qualities
poetry run rip --quality 2 url <url>
poetry run rip --codec mp3 url <url>

# Interactive search testing
poetry run rip search qobuz album "test query"
poetry run rip search tidal playlist "test"
```

## Architecture Overview

### Core Structure
- **`streamrip/rip/`**: CLI interface and main entry points
  - `cli.py`: Click-based CLI commands and options
  - `main.py`: Core application logic and download coordination
  - `parse_url.py`: URL parsing for different streaming services

- **`streamrip/client/`**: Service-specific API clients
  - `client.py`: Abstract base client class with rate limiting
  - `qobuz.py`, `tidal.py`, `deezer.py`, `soundcloud.py`: Service implementations
  - `downloadable.py`: Downloadable media representation

- **`streamrip/media/`**: Media object representations
  - `track.py`, `album.py`, `playlist.py`, `artist.py`: Media type classes
  - `media.py`: Base media class with async download logic

- **`streamrip/metadata/`**: Metadata handling and tagging
  - `tagger.py`: Audio file tagging with mutagen
  - `covers.py`: Album artwork handling
  - Various metadata classes for different media types

### Key Design Patterns

#### Async/Await Architecture
The entire application is built on asyncio with concurrent downloads:
- `aiohttp` for HTTP requests with rate limiting via `aiolimiter`
- `aiofiles` for async file operations
- Semaphore-based concurrency control in `media/semaphore.py`

#### Configuration Management
- TOML-based configuration in `config.py` with dataclasses
- Version-aware config with migration support
- Service-specific config classes (QobuzConfig, TidalConfig, etc.)

#### Client Pattern
Abstract `Client` base class with service-specific implementations:
- Authentication handling per service
- Quality mapping and format selection
- Rate limiting and request management

## Configuration

### Config File Location
Default: `~/.config/streamrip/config.toml` (or OS-specific app directory)

### Key Config Sections
- **Downloads**: Path templates, folder structure, concurrent downloads
- **Conversion**: ffmpeg integration, codec settings
- **Services**: API credentials and service-specific settings (qobuz, tidal, deezer, soundcloud)
- **Database**: Download tracking and duplicate prevention

## Testing Strategy

### Test Structure
- `tests/fixtures/`: Test configuration and utilities
- Service-specific tests require valid credentials in environment variables
- Async test support via pytest-asyncio
- Mock objects for API responses

### Environment Variables for Testing
```bash
QOBUZ_EMAIL=your_email
QOBUZ_PASSWORD=your_password
# Other service credentials as needed
```

## Error Handling

### Common Issues
- **Authentication**: Invalid credentials or expired tokens
- **Network**: Rate limiting, connection timeouts
- **Quality**: Requested quality not available for track/service
- **Filesystem**: Invalid paths, permissions, disk space

### Client Error Patterns
Each client handles service-specific errors and maps to common exceptions:
- Connection failures retry with exponential backoff
- Quality fallback when requested quality unavailable
- Token refresh for expired authentication

## Development Notes

- **Async Context**: All I/O operations use async/await
- **Rate Limiting**: Configurable per-service rate limiting via `aiolimiter`
- **Concurrency**: Semaphore-controlled concurrent downloads
- **Logging**: Rich-based logging with different levels per module
- **Type Hints**: Extensive type annotations throughout codebase