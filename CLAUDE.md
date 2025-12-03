# CLAUDE.md - AI Assistant Guide for streamrip

This document provides comprehensive guidance for AI assistants working on the streamrip codebase.

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Codebase Structure](#codebase-structure)
3. [Architecture & Design Patterns](#architecture--design-patterns)
4. [Development Workflow](#development-workflow)
5. [Testing Strategy](#testing-strategy)
6. [Key Conventions](#key-conventions)
7. [Common Tasks](#common-tasks)
8. [Dependencies & External Tools](#dependencies--external-tools)
9. [Troubleshooting](#troubleshooting)

---

## Repository Overview

**Project**: streamrip - A scriptable stream downloader for Qobuz, Tidal, Deezer, and SoundCloud
**Language**: Python 3.10+
**Package Manager**: Poetry
**License**: GPL-3.0-only
**Current Version**: 2.1.0

### Key Features
- Fast, concurrent downloads powered by `aiohttp` and `asyncio`
- Downloads tracks, albums, playlists, discographies, and labels
- Supports Qobuz, Tidal, Deezer, SoundCloud
- Spotify/Apple Music playlist support via Last.fm
- Automatic format conversion (FLAC, ALAC, MP3, AAC, OGG)
- Download tracking database (deduplication)
- Rich terminal UI with progress bars
- Highly configurable via TOML

### Important Links
- Main repo: https://github.com/nathom/streamrip
- Development branch: `dev` (target for PRs)
- Issues: Use proper templates (Bug Report or Feature Request)

---

## Codebase Structure

### Directory Layout

```
streamrip_RipDL/
├── streamrip/                  # Main source code (~6,254 lines)
│   ├── rip/                    # CLI and application entry point
│   │   ├── cli.py              # Click-based CLI commands
│   │   ├── main.py             # Main orchestration class
│   │   ├── user_paths.py       # Path resolution utilities
│   │   └── prompt.py           # Interactive prompts
│   ├── media/                  # Media type implementations
│   │   ├── media.py            # Abstract base classes
│   │   ├── track.py            # Track & PendingTrack
│   │   ├── album.py            # Album & PendingAlbum
│   │   ├── artist.py           # Artist/discography
│   │   ├── playlist.py         # Playlist support
│   │   └── label.py            # Label support
│   ├── client/                 # Streaming service clients
│   │   ├── client.py           # Abstract Client base
│   │   ├── qobuz.py            # Qobuz API client
│   │   ├── tidal.py            # Tidal API client
│   │   ├── deezer.py           # Deezer API client
│   │   ├── soundcloud.py       # SoundCloud API client
│   │   └── downloadable.py     # Download implementations
│   ├── metadata/               # Metadata & tagging
│   │   ├── metadata.py         # TrackMetadata/AlbumMetadata
│   │   ├── covers.py           # Cover art handling
│   │   └── util.py             # Metadata utilities
│   ├── utils/                  # General utilities
│   │   ├── types.py            # Type definitions
│   │   ├── util.py             # Helper functions
│   │   └── parsing.py          # URL parsing
│   ├── config.py               # Configuration management
│   ├── config.toml             # Default config template
│   ├── db.py                   # SQLite database wrapper
│   ├── converter.py            # FFmpeg audio conversion
│   ├── progress.py             # Rich progress bars
│   ├── exceptions.py           # Custom exceptions
│   └── __init__.py             # Package exports
├── tests/                      # pytest test suite
│   ├── fixtures/               # Test fixtures
│   │   ├── clients.py
│   │   ├── config.py
│   │   └── util.py
│   ├── test_*.py               # Test modules
│   └── test_config.toml        # Test configuration
├── .github/workflows/          # CI/CD pipelines
│   ├── pytest.yml              # Test workflow
│   ├── ruff.yml                # Linting workflow
│   ├── codeql-analysis.yml     # Security analysis
│   └── poetry-publish.yml      # PyPI publishing
├── pyproject.toml              # Poetry configuration
├── poetry.lock                 # Dependency lock file
└── README.md                   # User documentation
```

### Core Module Responsibilities

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `streamrip.rip.main` | Orchestrates entire download pipeline | `Main` |
| `streamrip.rip.cli` | Click-based CLI interface | Commands: `url`, `search`, `config`, etc. |
| `streamrip.config` | Configuration management | `Config`, `QobuzConfig`, `TidalConfig`, etc. |
| `streamrip.media.*` | Media type abstractions | `Track`, `Album`, `Artist`, `Playlist` |
| `streamrip.client.*` | Streaming service APIs | `QobuzClient`, `TidalClient`, etc. |
| `streamrip.metadata.*` | Metadata extraction & tagging | `TrackMetadata`, `AlbumMetadata` |
| `streamrip.db` | Download tracking database | `Downloads` |
| `streamrip.converter` | Audio format conversion | `FLAC`, `MP3`, `ALAC`, etc. |
| `streamrip.progress` | Terminal UI components | `get_progress_bar` |

---

## Architecture & Design Patterns

### 1. Two-Phase Resolution Pattern

The core download flow follows a two-phase pattern:

```
URL → Pending → Media → Downloaded Files
```

**Phase 1: Pending** (metadata not yet fetched)
- `PendingTrack`, `PendingAlbum`, `PendingArtist`, etc.
- Lightweight objects created from URLs
- Contain only source ID and type

**Phase 2: Media** (metadata resolved, ready to download)
- `Track`, `Album`, `Artist`, etc.
- Full metadata fetched from API
- Ready for download/tagging

**Example Flow**:
```python
# URL parsing creates Pending object
pending = into_pending("https://qobuz.com/album/...")

# Resolve fetches metadata → Media object
album = await pending.resolve()

# Download executes
await album.rip()
```

### 2. Async/Await Throughout

**All I/O operations are async:**
- HTTP requests via `aiohttp`
- File operations via `aiofiles`
- Concurrent downloads via `asyncio.gather()`
- Rate limiting via `aiolimiter`

**Key Async Patterns**:
```python
# Async context managers
async with Main(config) as main:
    await main.add_all(urls)
    await main.resolve()
    await main.rip()

# Concurrent operations
await asyncio.gather(
    track1.download(),
    track2.download(),
    track3.download()
)
```

### 3. Abstract Base Classes

**Client Hierarchy**:
```
Client (ABC)
├── QobuzClient
├── TidalClient
├── DeezerClient
└── SoundcloudClient
```

**Media Hierarchy**:
```
Media (ABC)                 Pending (ABC)
├── Track                   ├── PendingTrack
├── Album                   ├── PendingAlbum
├── Artist                  ├── PendingArtist
├── Playlist                ├── PendingPlaylist
└── Label                   └── PendingLabel
```

**Downloadable Hierarchy**:
```
Downloadable (ABC)
├── BasicDownloadable
├── DeezerDownloadable (Blowfish encryption)
├── TidalDownloadable (AES decryption)
└── SoundcloudDownloadable (HLS/m3u8)
```

### 4. Configuration System

**Two-tier configuration**:
- `config.file`: Persistent settings from config.toml
- `config.session`: Runtime overrides (from CLI flags)

**Dataclass-based sections**:
```python
@dataclass(slots=True)
class QobuzConfig:
    quality: int
    email: str
    password: str
    app_id: str
    secrets: list[str]
```

**Versioned with auto-migration**:
- Current version: 2.0.6
- Old configs auto-update on load

### 5. Download Pipeline

Each Media type implements three-phase download:

```python
async def rip(self):
    await self.preprocess()   # Create dirs, download covers
    await self.download()     # Get audio files
    await self.postprocess()  # Tag, convert, update DB
```

**Concurrency Control**:
- Global semaphore limits concurrent downloads (`max_connections`)
- Per-service rate limiting (`requests_per_minute`)
- Can disable concurrency for sequential downloads

---

## Development Workflow

### Setup

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Clone repository
git clone https://github.com/nathom/streamrip.git
cd streamrip

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run in development mode
poetry run rip --help
```

### Code Quality Tools

**Linter**: Ruff (fast Python linter)
```bash
poetry run ruff check .
poetry run ruff format .
```

**Ruff Configuration** (in `pyproject.toml`):
```toml
[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "I", "ASYNC", "N", "RUF", "ERA001"]
fixable = ["ALL"]
```

**Formatter**: Ruff (replaces Black)
- Double quotes for strings
- Space indentation
- Respect magic trailing commas

**Import Sorting**: Ruff with isort rules

### Git Workflow

1. **Target branch**: Always open PRs to `dev` (NOT `main`)
2. **Commit style**: Clear, descriptive messages
3. **Documentation**: Document functions and obscure code
4. **Testing**: Add tests for new features

### CI/CD Pipelines

**pytest.yml** (runs on push/PR to main/dev):
- Python 3.10
- Poetry 1.5.1
- Runs full test suite

**ruff.yml** (runs on all pushes/PRs):
- Linting check
- Format check

**codeql-analysis.yml**:
- Security scanning

**poetry-publish.yml**:
- Publishes to PyPI on releases

---

## Testing Strategy

### Framework

- **pytest** (^7.4)
- **pytest-asyncio** (^0.21.1) - async test support
- **pytest-mock** (^3.11.1) - mocking

### Test Organization

```
tests/
├── fixtures/           # Reusable test fixtures
│   ├── clients.py      # Mock client fixtures
│   ├── config.py       # Test configs
│   └── util.py         # Test helpers
├── test_*.py           # Test modules (one per feature)
├── test_config.toml    # Test configuration
└── *.json / *.flac     # Test data files
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_config.py

# Run with verbose output
poetry run pytest -v

# Run with debug logging
poetry run pytest --log-cli-level=DEBUG
```

### pytest Configuration

```toml
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q"
testpaths = ["tests"]
log_level = "DEBUG"
asyncio_mode = 'auto'  # Auto-detect async tests
log_cli = true
```

### Writing Tests

**Example async test**:
```python
import pytest

@pytest.mark.asyncio
async def test_download_track(qobuz_client, test_config):
    track = await qobuz_client.get_track("12345678")
    assert track.id == "12345678"
    assert track.title is not None
```

**Use fixtures from `tests/fixtures/`**:
- `test_config`: Test configuration
- `qobuz_client`, `tidal_client`, etc.: Mock clients

### Test Coverage Areas

- `test_config.py`: Config loading, updating, migration
- `test_parse_url.py`: URL parsing for all services
- `test_track.py`: Track download logic
- `test_album.py`: Album download coordination
- `test_qobuz_client.py`: Qobuz API interactions
- `test_tagger.py`: Audio file tagging
- `test_covers.py`: Cover art handling
- `test_error_handling.py`: Exception handling
- `test_discography_filter.py`: Artist filtering
- `test_ssl_verification.py`: SSL/TLS handling

---

## Key Conventions

### Code Style

1. **Type Hints**: Use comprehensive type annotations
   ```python
   async def download(self, url: str, path: Path) -> None:
   ```

2. **Dataclasses**: Prefer dataclasses with `slots=True`
   ```python
   @dataclass(slots=True)
   class TrackMetadata:
       title: str
       artist: str
       album: str
   ```

3. **Docstrings**: Document public APIs and complex logic
   ```python
   def parse_url(url: str) -> URL:
       """Parse a streaming service URL into a URL object.

       Args:
           url: The URL to parse

       Returns:
           A URL object with source, media_type, and id

       Raises:
           InvalidURL: If URL is malformed
       """
   ```

4. **Error Handling**: Use custom exceptions from `exceptions.py`
   - `NonStreamable`: Item can't be downloaded
   - `MissingCredentials`: Auth required
   - `InvalidQuality`: Unsupported quality
   - `AuthenticationError`: Login failed

5. **Async Best Practices**:
   - Always await async functions
   - Use `async with` for context managers
   - Use `asyncio.gather()` for concurrent operations
   - Use `aiofiles` for file I/O

### Naming Conventions

- **Classes**: PascalCase (`QobuzClient`, `TrackMetadata`)
- **Functions/methods**: snake_case (`download_track`, `parse_url`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_QUALITY`, `DEFAULT_CODEC`)
- **Private members**: Leading underscore (`_client`, `_validate`)
- **Type variables**: PascalCase with T suffix (`MediaT`, `ConfigT`)

### File Organization

- **One class per file** (for major classes)
- **Related functions grouped** in utility modules
- **Imports sorted** (stdlib, third-party, local)
- **Max line length**: 88 characters (Black default)

### Config File Paths

**Default locations** (via `appdirs`):
- Linux: `~/.config/streamrip/`
- macOS: `~/Library/Application Support/streamrip/`
- Windows: `%APPDATA%\streamrip\`

**Key files**:
- `config.toml`: User configuration
- `downloads.db`: Downloaded tracks database
- `failed_downloads.db`: Failed download tracking

---

## Common Tasks

### Adding a New Streaming Source

1. **Create client** in `streamrip/client/`:
   ```python
   # streamrip/client/newsource.py
   from .client import Client

   class NewsourceClient(Client):
       source = "newsource"

       async def get_track(self, track_id: str) -> dict:
           # Implement API calls
           pass
   ```

2. **Add config section** in `streamrip/config.py`:
   ```python
   @dataclass(slots=True)
   class NewsourceConfig:
       quality: int = 2
       api_key: str = ""
   ```

3. **Update URL parsing** in `streamrip/utils/parsing.py`:
   ```python
   URL_REGEX.update({
       "newsource": {
           "track": r"newsource\.com/track/(\w+)",
           "album": r"newsource\.com/album/(\w+)",
       }
   })
   ```

4. **Add tests** in `tests/test_newsource_client.py`

5. **Update README.md** with new source

### Modifying the CLI

CLI commands are in `streamrip/rip/cli.py` using Click.

**Adding a new command**:
```python
@cli.command()
@click.argument("arg1")
@click.option("--opt1", help="Description")
@coro  # Decorator for async functions
async def newcommand(ctx, arg1, opt1):
    """Command description for help."""
    cfg = ctx.obj
    async with Main(cfg) as main:
        # Implementation
        pass
```

**Adding a global option**:
```python
@cli.command()
@global_opts  # Inherits all global options
@click.option("--new-opt", help="New option")
@coro
async def command(ctx, new_opt, **kwargs):
    pass
```

### Adding a New Config Option

1. **Add to dataclass** in `config.py`:
   ```python
   @dataclass(slots=True)
   class DownloadsConfig:
       folder: str
       new_option: bool = True  # Add here with default
   ```

2. **Add to default config** in `config.toml`:
   ```toml
   [downloads]
   folder = "~/StreamripDownloads"
   new_option = true
   ```

3. **Update version** if breaking change:
   ```python
   CONFIG_VERSION = "2.0.7"  # Increment
   ```

4. **Add migration** if needed in `config.py`:
   ```python
   def _update_config(self):
       # Handle old configs
       if old_version < "2.0.7":
           # Add new_option if missing
   ```

### Debugging Tips

**Enable debug logging**:
```bash
poetry run rip --verbose url <url>
```

**Use ipdb for debugging**:
```python
import ipdb; ipdb.set_trace()
```

**Check logs** in progress bars:
- Errors show in red
- Warnings show in yellow
- Info shows in blue

**Test specific service**:
```bash
# Test Qobuz
poetry run pytest tests/test_qobuz_client.py -v

# Test URL parsing
poetry run pytest tests/test_parse_url.py::test_qobuz_url -v
```

---

## Dependencies & External Tools

### Core Runtime Dependencies

**HTTP & Async I/O**:
- `aiohttp` (^3.9): Async HTTP client
- `aiofiles` (^0.7): Async file operations
- `aiodns` (^3.0.0): Async DNS resolution
- `aiolimiter` (^1.1.0): Rate limiting

**Audio & Metadata**:
- `mutagen` (^1.45.1): Audio tagging (ID3, FLAC, MP4)
- `Pillow` (>=9,<11): Image processing for covers

**Streaming Services**:
- `deezer-py` (1.3.6): Deezer API client
- `pycryptodomex` (^3.10.1): Encryption (Blowfish/AES)
- `m3u8` (^0.9.0): HLS playlist parsing

**Configuration**:
- `tomlkit` (^0.7.2): TOML parsing with comments
- `pathvalidate` (^2.4.1): Path sanitization
- `appdirs` (^1.4.4): Platform-specific paths

**CLI & UI**:
- `click`: CLI framework (via click-help-colors)
- `click-help-colors` (^0.9.2): Colored help
- `rich` (^13.6.0): Terminal UI, progress bars
- `simple-term-menu` (^1.2.1): Interactive menus (Linux/Mac)
- `pick` (^2): Interactive menus (Windows)

### External Tools (Required)

**FFmpeg**: Audio conversion and concatenation
```bash
# Linux
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from ffmpeg.org
```

**Used for**:
- Format conversion (FLAC → MP3, etc.)
- Sample rate conversion
- Bit depth conversion
- HLS stream concatenation (SoundCloud)

### Development Dependencies

```bash
poetry install  # Installs all dev dependencies
```

- `pytest` (^7.4): Testing framework
- `pytest-asyncio` (^0.21.1): Async test support
- `pytest-mock` (^3.11.1): Mocking
- `ruff` (^0.1): Linter & formatter
- `black` (^24): Code formatter
- `isort` (^5.9.3): Import sorting
- `flake8` (^3.9.2): Style checker

### Dependency Management

**Adding a dependency**:
```bash
poetry add package-name

# Development dependency
poetry add --group dev package-name
```

**Updating dependencies**:
```bash
poetry update

# Update specific package
poetry update package-name
```

**Lock file**:
- Always commit `poetry.lock` changes
- Ensures reproducible builds

---

## Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Ensure in Poetry shell
poetry shell

# Or prefix with poetry run
poetry run python script.py
```

**2. SSL Certificate Errors**
```bash
# Disable SSL verification (not recommended)
rip --no-ssl-verify url <url>

# Install certifi extra
poetry install -E ssl
```

**3. FFmpeg Not Found**
```bash
# Check FFmpeg installation
which ffmpeg
ffmpeg -version

# Install if missing (see External Tools section)
```

**4. Test Failures**
```bash
# Run with full output
poetry run pytest -vv

# Check specific test
poetry run pytest tests/test_file.py::test_name -vv
```

**5. Config Issues**
```bash
# Reset config to defaults
rip config reset -y

# Open config in editor
rip config open

# Show config path
rip config path
```

**6. Authentication Errors**

For Qobuz/Tidal/Deezer, you need valid credentials:
```bash
# Open config and add credentials
rip config open

# Test with a track
rip url <track-url>
```

**7. Rate Limiting**

If hitting rate limits:
```toml
# In config.toml
[downloads]
requests_per_minute = 30  # Reduce from default 60
```

### Performance Optimization

**Increase concurrency**:
```toml
[downloads]
max_connections = 10  # Default is 6
```

**Disable unnecessary features**:
```toml
[metadata]
set_playlist_to_album = false

[database]
downloads_enabled = false  # Skip DB logging
```

**Use lower quality for testing**:
```bash
rip --quality 1 url <url>  # 320k instead of lossless
```

### Debugging Client Issues

**Enable verbose logging**:
```bash
rip --verbose url <url>
```

**Check API responses**:
```python
# In client code, add logging
import logging
logger = logging.getLogger(__name__)

logger.debug(f"API response: {response}")
```

**Test client in isolation**:
```python
import asyncio
from streamrip.client import QobuzClient
from streamrip.config import Config

async def test():
    cfg = Config.defaults()
    client = QobuzClient(cfg.qobuz)
    await client.login()
    track = await client.get_track("12345678")
    print(track)

asyncio.run(test())
```

---

## Quick Reference

### Useful Commands

```bash
# Development
poetry install              # Install dependencies
poetry shell                # Activate virtualenv
poetry run pytest           # Run tests
poetry run ruff check .     # Lint code
poetry run ruff format .    # Format code

# Usage
rip url <url>               # Download URL
rip search qobuz album <query>  # Interactive search
rip config open             # Edit config
rip database browse         # View downloads

# Testing specific components
pytest tests/test_config.py -v
pytest tests/test_parse_url.py::test_qobuz_url
pytest -k "test_download" --log-cli-level=DEBUG
```

### File Locations

| File | Location | Purpose |
|------|----------|---------|
| Config | `~/.config/streamrip/config.toml` | User settings |
| Database | `~/.config/streamrip/downloads.db` | Downloaded tracks |
| Logs | Terminal output (via Rich) | Debug info |
| Downloads | `~/StreamripDownloads/` (default) | Music files |

### Quality Levels

| ID | Quality | Formats | Sources |
|----|---------|---------|---------|
| 0 | 128 kbps | MP3/AAC | Deezer, Tidal, SoundCloud |
| 1 | 320 kbps | MP3/AAC | All sources |
| 2 | 16/44.1 | FLAC | Qobuz, Tidal, Deezer |
| 3 | 24/96 | FLAC/MQA | Qobuz, Tidal |
| 4 | 24/192 | FLAC | Qobuz only |

### Important Classes

| Class | File | Purpose |
|-------|------|---------|
| `Main` | `rip/main.py` | Orchestrates downloads |
| `Config` | `config.py` | Configuration management |
| `Client` | `client/client.py` | Base API client |
| `Track` | `media/track.py` | Track download logic |
| `Album` | `media/album.py` | Album coordination |
| `Downloads` | `db.py` | Database wrapper |

---

## Final Notes

### When Making Changes

1. **Read before modifying**: Always read files before editing
2. **Follow existing patterns**: Match the codebase style
3. **Add tests**: Test new features and bug fixes
4. **Document**: Add docstrings for public APIs
5. **Run linter**: `poetry run ruff check .` before committing
6. **Run tests**: `poetry run pytest` before pushing
7. **Target dev branch**: PRs go to `dev`, not `main`

### Code Review Checklist

- [ ] Type hints on all function signatures
- [ ] Docstrings for public APIs
- [ ] Tests for new functionality
- [ ] No hardcoded credentials or paths
- [ ] Async/await used correctly
- [ ] Error handling with custom exceptions
- [ ] Logging at appropriate levels
- [ ] Ruff passes without errors
- [ ] Tests pass

### Getting Help

- **Wiki**: https://github.com/nathom/streamrip/wiki
- **Issues**: Use proper templates (Bug Report/Feature Request)
- **Code**: Check existing implementations for patterns
- **Tests**: Review `tests/` for usage examples

---

**Last Updated**: 2025-11-23
**Version**: 2.1.0
**For**: AI assistants (Claude, etc.)
