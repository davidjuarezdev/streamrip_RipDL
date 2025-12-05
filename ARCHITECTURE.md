# streamrip Architecture Documentation

**Version:** 2.1.0
**Last Updated:** 2025-12-05
**Status:** Living Document

---

## Table of Contents

1. [Overview](#overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Details](#component-details)
4. [Design Patterns](#design-patterns)
5. [Data Flow](#data-flow)
6. [Concurrency Model](#concurrency-model)
7. [Error Handling](#error-handling)
8. [Configuration Management](#configuration-management)
9. [Database Design](#database-design)
10. [Testing Strategy](#testing-strategy)

---

## Overview

streamrip is an asynchronous, modular music downloader designed for high-performance concurrent downloads from multiple streaming services (Qobuz, Tidal, Deezer, SoundCloud).

### Core Principles

1. **Async-First** - Built on asyncio for maximum concurrency
2. **Modular Design** - Clear separation of concerns
3. **Extensibility** - Easy to add new streaming sources
4. **Type Safety** - Comprehensive type hints throughout
5. **Configuration-Driven** - User preferences control behavior

### Key Statistics

- **~6,254 LOC** (main codebase)
- **~1,463 LOC** (tests)
- **Python 3.10+** required
- **7 main modules** (cli, client, media, metadata, config, db, converter)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│                    (streamrip/rip/cli.py)                    │
│  Commands: url, search, file, lastfm, config, database      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                        │
│                   (streamrip/rip/main.py)                    │
│          Main class: coordinates entire workflow              │
└───┬──────────────┬──────────────┬──────────────┬────────────┘
    │              │               │               │
    ▼              ▼               ▼               ▼
┌────────┐  ┌──────────┐    ┌─────────┐    ┌──────────┐
│ Config │  │ Clients  │    │Database │    │ Progress │
│        │  │ Layer    │    │         │    │ Manager  │
└────────┘  └─────┬────┘    └─────────┘    └──────────┘
                  │
        ┌─────────┼─────────┬──────────┬──────────┐
        ▼         ▼         ▼          ▼          ▼
    ┌────────┬────────┬─────────┬───────────┬────────┐
    │ Qobuz  │ Tidal  │ Deezer  │SoundCloud│ Base   │
    │ Client │ Client │ Client  │  Client  │ Client │
    └───┬────┴───┬────┴────┬────┴─────┬────┴────┬───┘
        │        │         │          │         │
        └────────┴─────────┴──────────┴─────────┘
                         │
                         ▼
            ┌─────────────────────────┐
            │     Media Layer         │
            │  (Pending → Media)      │
            │  Album, Track,          │
            │  Playlist, Artist       │
            └────────┬────────────────┘
                     │
                     ▼
            ┌─────────────────────────┐
            │   Downloadable Layer    │
            │  Basic, Encrypted, HLS  │
            └────────┬────────────────┘
                     │
                     ▼
            ┌─────────────────────────┐
            │    File System          │
            │  Audio Files + Artwork  │
            └─────────────────────────┘
```

---

## Component Details

### 1. CLI Layer (`streamrip/rip/cli.py`)

**Purpose:** User interface and command parsing

**Technology:** Click framework with rich formatting

**Commands:**
- `url` - Download from URL(s)
- `search` - Interactive search
- `file` - Batch download from file
- `lastfm` - Last.fm playlist integration
- `config` - Configuration management
- `database` - Database browsing

**Entry Point:**
```python
# Defined in pyproject.toml
[tool.poetry.scripts]
rip = "streamrip.rip:rip"
```

### 2. Orchestration Layer (`streamrip/rip/main.py`)

**Purpose:** Coordinates the entire download pipeline

**Key Class:** `Main`

**Responsibilities:**
1. Client authentication and login
2. URL parsing → Pending items
3. Metadata resolution
4. Concurrent download coordination
5. Progress tracking
6. Database updates

**Data Pipeline:**
```
User Input → Main.add_all() → Pending items →
Main.resolve() → Media objects →
Main.rip() → Downloaded files
```

**Key Methods:**
- `add_all(urls)` - Parse URLs concurrently
- `get_logged_in_client(source)` - Ensure authenticated
- `resolve()` - Convert Pending → Media
- `rip()` - Download all media items

### 3. Client Layer (`streamrip/client/`)

**Purpose:** API communication with streaming services

**Design Pattern:** Abstract Factory + Strategy

**Base Class:** `Client` (abstract)

**Implementations:**
- `QobuzClient` - Qobuz API integration
  - Features: Dynamic credential extraction via QobuzSpoofer
  - Authentication: Email + password (MD5) or token
- `TidalClient` - Tidal API integration
  - Authentication: OAuth2 with refresh tokens
  - Quality: Up to 24-bit MQA
- `DeezerClient` - Deezer API integration
  - Authentication: ARL cookie
  - Uses deezer-py library
- `SoundcloudClient` - SoundCloud API integration
  - Authentication: Client ID + app version
  - Public content only

**Common Interface:**
```python
class Client(ABC):
    @abstractmethod
    async def login(self) -> None: ...

    @abstractmethod
    async def search(self, media_type: str, query: str, limit: int): ...

    @abstractmethod
    async def get_metadata(self, item_id: str, media_type: str): ...
```

**Features:**
- Rate limiting via `aiolimiter`
- SSL certificate handling
- Session management (aiohttp)
- Concurrent request batching

### 4. Media Layer (`streamrip/media/`)

**Purpose:** Represents downloadable content

**Design Pattern:** Two-Phase Construction + Template Method

**Phase 1: Pending** (before metadata resolution)
- `PendingSingle` - Single track
- `PendingAlbum` - Album
- `PendingPlaylist` - Playlist
- `PendingArtist` - Artist discography
- `PendingLabel` - Label catalog
- `PendingLastfmPlaylist` - Last.fm integration

**Phase 2: Media** (after metadata resolution)
- `Track` - Individual track
- `Album` - Album with tracks
- `Playlist` - Playlist with tracks
- `Artist` - Artist with albums
- `Label` - Label with releases

**Lifecycle Pattern (Template Method):**
```python
async def rip(self):
    """Standard download lifecycle."""
    await self.preprocess()   # Setup, create directories, download artwork
    await self.download()     # Download audio files
    await self.postprocess()  # Tag files, convert, update database
```

**Why Two-Phase Construction?**
1. URL parsing is fast (no API calls)
2. Metadata resolution requires API calls (slow)
3. Separating phases allows:
   - Fast initial validation
   - Concurrent metadata resolution
   - Better error handling
   - Progress tracking

### 5. Metadata Layer (`streamrip/metadata/`)

**Purpose:** Extract and normalize metadata from APIs

**Components:**
- `AlbumMetadata` - Album information
- `TrackMetadata` - Track information
- `SearchResults` - Search result formatting
- `Tagger` - Audio file tagging (FLAC, MP3, MP4)

**Supported Tags:**
- Title, Artist, Album, AlbumArtist
- Date, Genre, Label, Copyright
- Track number, Disc number
- Cover art embedding
- Custom tags (comment, isrc, etc.)

**Libraries Used:**
- `mutagen` - Audio file tagging
- `Pillow` - Image processing (artwork)

### 6. Downloadable Layer (`streamrip/client/downloadable.py`)

**Purpose:** Abstraction for different download mechanisms

**Design Pattern:** Strategy

**Implementations:**
- `BasicDownloadable` - Simple HTTP download
- `DeezerDownloadable` - Blowfish decryption for Deezer
- `TidalDownloadable` - Special handling for Tidal
- `EncryptedDownloadable` - Generic encrypted downloads
- `HLSDownloadable` - HLS stream downloads

**Key Method:**
```python
async def fast_async_download(path, url, headers, callback):
    """
    Performance-optimized download.

    Uses blocking I/O (requests) with periodic yields for performance.
    Achieves ~5x speed improvement over pure async (aiohttp).

    See ARCHITECTURE.md for rationale.
    """
```

**Performance Decision:**
- Uses blocking `requests` library
- Yields to event loop every 1MB
- Trade-off: 5x performance vs pure async
- Justification: CPU-bound with small chunks, I/O-bound with large chunks

### 7. Configuration (`streamrip/config.py`)

**Purpose:** Manage user preferences and credentials

**Format:** TOML configuration file

**Location:** `~/.config/streamrip/config.toml` (Unix) or `%APPDATA%\streamrip\config.toml` (Windows)

**Features:**
- Version tracking and automatic migration
- Session vs file config separation
- CLI argument overrides
- Nested dataclass validation

**Configuration Structure:**
```python
@dataclass
class Config:
    session: SessionConfig  # Runtime overrides
    file: FileConfig        # Persistent settings

    # Service configs
    qobuz: QobuzConfig
    tidal: TidalConfig
    deezer: DeezerConfig
    soundcloud: SoundcloudConfig

    # General settings
    downloads: DownloadsConfig
    database: DatabaseConfig
    conversion: ConversionConfig
    artwork: ArtworkConfig
```

**Context Manager Pattern:**
```python
with Config(path) as config:
    # Automatically saves on exit
    config.session.quality = 3
```

### 8. Database (`streamrip/db.py`)

**Purpose:** Track downloaded items to avoid duplicates

**Technology:** SQLite3

**Tables:**
1. **downloads** - Successfully downloaded items
   - Schema: `id TEXT UNIQUE`
2. **failed_downloads** - Failed download tracking
   - Schema: `source TEXT, media_type TEXT, id TEXT UNIQUE`

**Design Pattern:** Wrapper + Facade

**Interface:**
```python
class Database:
    def downloaded(self, item_id: str) -> bool
    def set_downloaded(self, item_id: str)
    def get_failed_downloads() -> list[tuple]
    def set_failed(source, media_type, id)
```

**Features:**
- Dummy implementation for disabled databases
- Automatic table creation
- Thread-safe (SQLite ACID properties)

### 9. Progress Display (`streamrip/progress.py`)

**Purpose:** Rich progress bars for downloads

**Technology:** Rich library (Live display + Progress bars)

**Current Implementation:**
```python
# Global singleton (to be refactored)
_p = ProgressManager()
```

**Features:**
- Multiple concurrent progress bars
- Transfer speed calculation
- Time remaining estimation
- Dynamic title display

**Future Improvement:**
Planned refactor to use dependency injection instead of global state.

### 10. Converter (`streamrip/converter.py`)

**Purpose:** Audio format conversion via FFmpeg

**Supported Codecs:**
- FLAC (lossless)
- ALAC (Apple Lossless)
- OPUS (efficient lossy)
- MP3 (universal lossy)
- VORBIS (OGG Vorbis)
- AAC (Apple AAC)

**Features:**
- Sample rate conversion
- Bit depth conversion
- Bitrate control for lossy codecs
- Metadata preservation

**Design Pattern:** Strategy

---

## Design Patterns

### 1. Abstract Factory Pattern

**Used in:** Client implementations

**Purpose:** Create related objects without specifying concrete classes

**Example:**
```python
class Client(ABC):
    """Abstract factory for streaming service clients."""

    @abstractmethod
    async def login(self): ...

    @abstractmethod
    async def search(self): ...

class QobuzClient(Client):
    """Concrete factory for Qobuz."""
    pass

class TidalClient(Client):
    """Concrete factory for Tidal."""
    pass
```

**Benefits:**
- Easy to add new streaming services
- Consistent interface across services
- Decouples client code from implementations

### 2. Template Method Pattern

**Used in:** Media.rip() lifecycle

**Purpose:** Define algorithm structure, let subclasses customize steps

**Example:**
```python
class Media(ABC):
    async def rip(self):
        """Template method defining the lifecycle."""
        await self.preprocess()   # Hook 1
        await self.download()     # Hook 2
        await self.postprocess()  # Hook 3

class Album(Media):
    async def preprocess(self):
        """Customize preprocessing for albums."""
        # Create directory structure
        # Download artwork
        pass
```

**Benefits:**
- Consistent workflow across media types
- Easy to customize specific steps
- Reduced code duplication

### 3. Strategy Pattern

**Used in:** Downloadable implementations, Converter

**Purpose:** Encapsulate algorithms, make them interchangeable

**Example:**
```python
class Downloadable(ABC):
    @abstractmethod
    async def _download(self, path, callback): ...

class BasicDownloadable(Downloadable):
    """Strategy for basic HTTP downloads."""
    pass

class DeezerDownloadable(Downloadable):
    """Strategy for encrypted Deezer downloads."""
    pass
```

**Benefits:**
- Different download mechanisms for different services
- Easy to add new download types
- Testable in isolation

### 4. Two-Phase Construction

**Used in:** Pending → Media transformation

**Purpose:** Separate object creation from initialization

**Example:**
```python
# Phase 1: Create Pending (fast, no API calls)
pending = PendingAlbum(album_id, client, config, db)

# Phase 2: Resolve to Media (slow, requires API)
album = await pending.resolve()
```

**Benefits:**
- Fast URL validation
- Concurrent metadata resolution
- Better error handling (fail early on bad URLs)
- Progress tracking between phases

### 5. Facade Pattern

**Used in:** Main class, Database class

**Purpose:** Provide simplified interface to complex subsystems

**Example:**
```python
class Main:
    """Facade for the entire download pipeline."""

    async def add_all(self, urls: list[str]):
        """Simple interface hides complexity."""
        # Handles: parsing, validation, client selection,
        # pending creation, error handling
        pass
```

**Benefits:**
- Simple API for CLI
- Hides complexity from users
- Easier to test and maintain

### 6. Dependency Injection

**Used Throughout:** Config, Client, Database passed as constructor arguments

**Purpose:** Inversion of control for better testability

**Example:**
```python
class Album:
    def __init__(self, client: Client, config: Config, db: Database):
        """Dependencies injected, not created."""
        self.client = client
        self.config = config
        self.db = db
```

**Benefits:**
- Easy to mock in tests
- Loosely coupled components
- Flexible configuration

### 7. Context Manager Protocol

**Used in:** Config, Progress Handles

**Purpose:** Resource management with automatic cleanup

**Example:**
```python
class Config:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.save()  # Automatic save on exit
```

**Benefits:**
- Automatic resource cleanup
- Exception-safe
- Pythonic API

---

## Data Flow

### Complete Download Flow

```
1. USER INPUT
   └─> CLI: rip url <URL>

2. ORCHESTRATION
   └─> Main.add_all(urls)
       ├─> parse_url(url) → ParsedURL
       ├─> get_logged_in_client(source) → Client
       └─> ParsedURL.into_pending() → Pending

3. METADATA RESOLUTION
   └─> Main.resolve()
       └─> Pending.resolve() → Media
           ├─> Client.get_metadata()
           └─> Create Media object with metadata

4. DOWNLOAD
   └─> Main.rip()
       └─> Media.rip()
           ├─> preprocess()
           │   ├─> Create directories
           │   └─> Download artwork
           ├─> download()
           │   ├─> For each track:
           │   │   ├─> Get download URL from Client
           │   │   ├─> Create Downloadable
           │   │   └─> Download audio file
           │   └─> Concurrent with semaphore limiting
           └─> postprocess()
               ├─> Tag audio files (mutagen)
               ├─> Convert if needed (FFmpeg)
               └─> Update database

5. OUTPUT
   └─> Audio files in downloads directory
```

### URL Parsing Flow

```
URL String
  │
  ├─> QobuzParser.parse() → ParsedQobuzURL?
  ├─> TidalParser.parse() → ParsedTidalURL?
  ├─> DeezerParser.parse() → ParsedDeezerURL?
  └─> SoundcloudParser.parse() → ParsedSoundcloudURL?
      │
      └─> ParsedURL
          ├─> source: str
          ├─> media_type: str
          ├─> id: str
          └─> into_pending() → Pending
```

### Authentication Flow

```
Client Initialization
  │
  ├─> Check: client.logged_in?
  │   │
  │   ├─> Yes → Use client
  │   └─> No  → Login flow:
  │           │
  │           ├─> Check: Config has credentials?
  │           │   │
  │           │   ├─> Yes → client.login()
  │           │   │         └─> API request with credentials
  │           │   │             ├─> Success → client.logged_in = True
  │           │   │             └─> Failure → Raise AuthenticationError
  │           │   │
  │           │   └─> No  → Prompter.prompt_and_login()
  │           │             ├─> Ask user for credentials
  │           │             ├─> client.login()
  │           │             └─> Prompter.save() → Update config
  │           │
  │           └─> client.logged_in = True
  │
  └─> Proceed with requests
```

---

## Concurrency Model

### AsyncIO Architecture

**Why AsyncIO?**
1. I/O-bound operations (network requests, file writes)
2. Concurrent downloads without thread overhead
3. Efficient resource utilization
4. Python's native async support

**Concurrency Layers:**

1. **Request Level** - Multiple API requests in parallel
   ```python
   await asyncio.gather(*[client.get_track(id) for id in track_ids])
   ```

2. **Download Level** - Multiple files downloading concurrently
   ```python
   semaphore = asyncio.Semaphore(4)  # Max 4 concurrent downloads
   async with semaphore:
       await downloadable.download(path, callback)
   ```

3. **Service Level** - Rate limiting per service
   ```python
   # aiolimiter ensures we don't exceed API rate limits
   async with self.rate_limiter:
       async with self.session.get(url) as response:
           ...
   ```

### Semaphore Usage

**Purpose:** Limit concurrent operations to prevent:
- Overwhelming the network
- API rate limit violations
- Memory exhaustion
- System resource saturation

**Example:**
```python
class Main:
    def __init__(self, config):
        max_concurrent = config.session.concurrent_downloads
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def download_track(self, track):
        async with self.semaphore:
            await track.download()
```

### Rate Limiting

**Library:** `aiolimiter`

**Per-Client Rate Limits:**
- Qobuz: Configurable (default: no limit)
- Tidal: Configurable (default: no limit)
- Deezer: Configurable (default: no limit)
- SoundCloud: Configurable (default: no limit)

**Implementation:**
```python
from aiolimiter import AsyncLimiter

class Client:
    def __init__(self):
        # Example: 10 requests per second
        self.rate_limiter = AsyncLimiter(10, 1.0)

    async def api_request(self, url):
        async with self.rate_limiter:
            async with self.session.get(url) as response:
                return await response.json()
```

### Async I/O Performance Trade-off

**Issue:** Pure async I/O (aiohttp + aiofiles) was CPU-bound due to excessive context switching

**Solution:** Hybrid approach in `fast_async_download()`
- Use blocking I/O (requests library)
- Yield to event loop periodically (every 1MB)
- Result: 5x performance improvement

**See:** `streamrip/client/downloadable.py:40-62`

---

## Error Handling

### Current State (As of 2.1.0)

**Challenge:** Inconsistent error handling patterns

**Patterns Found:**
1. Raise exception
2. Return None
3. Log and continue
4. Catch and re-raise

### Exception Hierarchy

**Base Exceptions:**
```python
# streamrip/exceptions.py
class AuthenticationError(Exception): ...
class MissingCredentialsError(Exception): ...
class IneligibleError(Exception): ...
class InvalidAppIdError(Exception): ...
class InvalidAppSecretError(Exception): ...
class NonStreamableError(Exception): ...
class ConversionError(Exception): ...
```

### Error Recovery

**Main.rip() with return_exceptions:**
```python
results = await asyncio.gather(
    *[item.rip() for item in self.media],
    return_exceptions=True
)

failed_items = sum(1 for r in results if isinstance(r, Exception))
```

**Benefits:**
- One track failure doesn't stop album download
- Failed items tracked in database
- User sees completion status

### Future Improvements (Planned)

**Recommended Strategy:**
1. Define clear exception hierarchy
2. Implement retry logic with exponential backoff
3. Distinguish retriable vs permanent errors
4. Add structured error logging
5. Improve user-facing error messages

**See:** `CODEBASE_REVIEW.md` Section 4 for details

---

## Configuration Management

### Configuration Layers

1. **Default Config** - Bundled template in `src/config.toml`
2. **User Config** - `~/.config/streamrip/config.toml`
3. **Session Config** - Runtime overrides from CLI arguments
4. **Environment Variables** - For testing (credentials)

### Config Loading Priority

```
CLI Arguments (highest priority)
  ↓
Session Config
  ↓
File Config
  ↓
Default Config (lowest priority)
```

### Version Migration

**Problem:** Config format changes between versions

**Solution:** Automatic migration on load

```python
def load_config(path: str) -> Config:
    config = parse_toml(path)

    if config.version < CURRENT_CONFIG_VERSION:
        config = migrate_config(config)
        save_config(config, path)

    return config
```

**Current Version:** 2.0.6

### CLI Override Mechanism

```bash
# Override quality setting
rip --quality 3 url <URL>

# CLI arg overrides file config for this session
```

**Implementation:**
```python
class Config:
    def __init__(self, file_config: FileConfig, session_config: SessionConfig):
        self.file = file_config
        self.session = session_config

    @property
    def quality(self):
        # Session overrides file
        return self.session.quality or self.file.quality
```

---

## Database Design

### Schema Design

**Philosophy:** Simple, flat schema for fast lookups

**Downloads Table:**
```sql
CREATE TABLE downloads (
    id TEXT UNIQUE NOT NULL
)
```

**Failed Downloads Table:**
```sql
CREATE TABLE failed_downloads (
    source TEXT NOT NULL,
    media_type TEXT NOT NULL,
    id TEXT UNIQUE NOT NULL
)
```

### Why SQLite?

**Advantages:**
- Serverless (no setup required)
- Cross-platform
- ACID compliant
- Fast for read-heavy workloads
- Small footprint

**Trade-offs:**
- Single-writer limitation (acceptable for this use case)
- No network access (not needed)
- Limited concurrency (sufficient for CLI tool)

### Dummy Pattern

**Purpose:** Allow disabling database without changing code

```python
class Dummy(DatabaseInterface):
    """No-op implementation."""
    def contains(self, **_): return False
    def add(self, *_): pass
    def all(self): return []
```

**Usage:**
```python
if config.database.enabled:
    db = Downloads(path)
else:
    db = Dummy()  # No database operations
```

---

## Testing Strategy

### Test Organization

```
tests/
├── fixtures/           # Reusable test fixtures
│   ├── config.py
│   ├── clients.py
│   └── util.py
├── test_config.py      # Configuration tests
├── test_parse_url.py   # URL parsing tests
├── test_qobuz_client.py # Client integration tests
├── test_ssl_verification.py # SSL tests
├── test_error_handling.py # Error handling tests
└── ...
```

### Test Types

1. **Unit Tests** - Test individual functions/classes in isolation
2. **Integration Tests** - Test interactions (e.g., client + API)
3. **End-to-End Tests** - Test complete workflows

### Current Coverage

**Strong Coverage:**
- Configuration management ✓
- URL parsing (10 tests) ✓
- SSL verification (14 tests) ✓
- Discography filtering (8 tests) ✓

**Gaps:**
- Main orchestration
- Progress display
- Database operations (remove() not tested)
- Media download flow

### Testing Async Code

**Framework:** pytest-asyncio

**Pattern:**
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

**Mocking Async:**
```python
from unittest.mock import AsyncMock

@pytest.fixture
def mock_client():
    client = AsyncMock()
    client.get_track.return_value = {"id": "123", "title": "Test"}
    return client
```

### Future Improvements

**Planned:**
- Increase coverage to 70%+
- Add property-based testing (hypothesis)
- Add performance benchmarks
- Add mutation testing
- Mock async HTTP calls comprehensively

**See:** `CODEBASE_REVIEW.md` Section 8 for details

---

## Appendix: Key Files Reference

### Entry Points
- `streamrip/rip/cli.py` - CLI commands
- `streamrip/rip/main.py` - Main orchestration
- `pyproject.toml` - Project configuration

### Core Business Logic
- `streamrip/client/*.py` - API clients
- `streamrip/media/*.py` - Media types
- `streamrip/metadata/*.py` - Metadata handling

### Utilities
- `streamrip/config.py` - Configuration
- `streamrip/db.py` - Database
- `streamrip/converter.py` - Format conversion
- `streamrip/progress.py` - Progress display
- `streamrip/exceptions.py` - Custom exceptions

### Testing
- `tests/**/*.py` - Test suite
- `tests/fixtures/**/*.py` - Test fixtures

### Configuration
- `pyproject.toml` - Poetry configuration
- `.github/workflows/*.yml` - CI/CD pipelines
- `config.toml` - Default configuration template

---

## Glossary

- **Pending** - Pre-metadata resolution state
- **Media** - Post-metadata resolution state
- **Downloadable** - Download strategy implementation
- **Client** - API wrapper for streaming service
- **Rip** - Download operation (verb)
- **Quality** - Encoding quality level (0-4)
- **ARL** - Deezer authentication cookie
- **MQA** - Master Quality Authenticated (Tidal format)

---

## Further Reading

- [CODEBASE_REVIEW.md](CODEBASE_REVIEW.md) - Comprehensive code review
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contributor guidelines
- [SECURITY.md](SECURITY.md) - Security policy
- [README.md](README.md) - User documentation
- [GAP_ANALYSIS.md](GAP_ANALYSIS.md) - Implementation gaps

---

**Document Version:** 1.0
**Last Updated:** 2025-12-05
**Maintained By:** Project contributors
