# StreamRip Codebase Review - Educational Guide

## 📚 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Deep Dive](#architecture-deep-dive)
3. [Design Patterns](#design-patterns)
4. [Code Organization](#code-organization)
5. [Key Concepts](#key-concepts)
6. [Best Practices Demonstrated](#best-practices-demonstrated)
7. [Learning Opportunities](#learning-opportunities)

---

## Project Overview

### What is StreamRip?
StreamRip is a **scriptable stream downloader** for multiple music streaming services (Qobuz, Tidal, Deezer, and SoundCloud). It's a command-line application built with Python 3.10+ that demonstrates professional-grade software engineering practices.

### Key Features
- **Asynchronous downloads** using `aiohttp` for high performance
- **Concurrent processing** with proper rate limiting
- **Database tracking** to avoid duplicate downloads
- **Flexible configuration** via TOML files
- **Audio conversion** using ffmpeg
- **Rich CLI interface** using Click and Rich libraries

### Tech Stack
- **Language**: Python 3.10+
- **Async Framework**: `asyncio`, `aiohttp`
- **CLI Framework**: `click`, `rich`
- **Audio Processing**: `mutagen` (tagging), `ffmpeg` (conversion)
- **Configuration**: `tomlkit` (TOML parsing)
- **Build System**: Poetry
- **Testing**: pytest with async support

---

## Architecture Deep Dive

### High-Level Architecture

StreamRip uses a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│             CLI Layer (cli.py)                   │
│  - Command parsing                               │
│  - User interaction                              │
│  - Configuration loading                         │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│        Orchestration Layer (main.py)            │
│  - Main workflow coordination                   │
│  - URL parsing & resolution                     │
│  - Download queue management                    │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌────────▼──────────┐
│  Client Layer  │   │   Media Layer     │
│  (client/)     │   │   (media/)        │
│  - API calls   │   │   - Download      │
│  - Auth        │   │   - Tagging       │
│  - Rate limit  │   │   - Conversion    │
└────────────────┘   └───────────────────┘
```

### Data Flow Pipeline

Understanding the data flow is crucial to understanding StreamRip:

```
User Input (URL)
    │
    ▼
Parse URL → Extract (source, media_type, id)
    │
    ▼
Create Pending Object (e.g., PendingAlbum)
    │
    ▼
Resolve → Fetch Metadata from API
    │
    ▼
Create Media Object (e.g., Album)
    │
    ▼
Download → Get Downloadable URLs
    │
    ▼
Save & Tag Audio Files
```

**Why this pipeline?**
- **Separation of concerns**: Each stage has a single responsibility
- **Lazy loading**: Metadata isn't fetched until needed
- **Error handling**: Each stage can fail independently
- **Testability**: Each stage can be tested in isolation

---

## Design Patterns

### 1. Abstract Base Classes (ABC)

**Location**: `streamrip/media/media.py`, `streamrip/client/client.py`

**Why?** Defines contracts that all implementations must follow.

```python
class Media(ABC):
    async def rip(self):
        await self.preprocess()    # Setup
        await self.download()       # Core work
        await self.postprocess()    # Cleanup
```

**Educational Points:**
- **Template Method Pattern**: `rip()` defines the algorithm skeleton
- All Media types (Track, Album, Playlist) follow the same lifecycle
- Forces consistent behavior across different media types
- Makes code predictable and maintainable

**Concrete Implementations:**
- `Track`: Downloads a single audio file
- `Album`: Downloads multiple tracks
- `Playlist`: Downloads multiple albums/tracks
- `Artist`: Downloads an artist's discography

### 2. Pending/Resolved Pattern

**Custom Pattern** for handling asynchronous metadata resolution.

```python
class Pending(ABC):
    """A request to download Media whose metadata hasn't been fetched."""

    @abstractmethod
    async def resolve(self) -> Media | None:
        """Fetch metadata and resolve into downloadable Media object."""
```

**Why this pattern exists:**
1. **Lazy Loading**: Don't fetch metadata until needed
2. **Batch Processing**: Can queue many URLs before fetching
3. **Error Handling**: Resolution can fail without breaking the pipeline
4. **Memory Efficiency**: Metadata isn't loaded all at once

**Example Flow:**
```python
# Create pending object (fast, no API calls)
pending_album = PendingAlbum(id="123", client=qobuz_client, ...)

# Later, resolve it (makes API call)
album = await pending_album.resolve()

# Now we can download
if album:
    await album.rip()
```

### 3. Strategy Pattern (Client Implementations)

**Location**: `streamrip/client/`

Each streaming service (Qobuz, Tidal, Deezer) has different APIs but the same interface:

```python
class Client(ABC):
    @abstractmethod
    async def get_metadata(self, item: str, media_type): ...

    @abstractmethod
    async def search(self, media_type: str, query: str): ...

    @abstractmethod
    async def get_downloadable(self, item: str, quality: int): ...
```

**Why?**
- **Polymorphism**: Main code doesn't care which service is used
- **Extensibility**: Easy to add new services
- **Testing**: Can mock clients easily

### 4. Dataclasses with Slots

**Location**: Throughout the codebase

```python
@dataclass(slots=True)
class Track(Media):
    meta: TrackMetadata
    downloadable: Downloadable
    config: Config
    folder: str
    cover_path: str | None
    db: Database
```

**Why `slots=True`?**
- **Memory Efficiency**: Reduces memory usage by ~40%
- **Faster Attribute Access**: No `__dict__` lookup
- **Better Type Safety**: Can't add arbitrary attributes

**Trade-off**: Can't add dynamic attributes (usually a good constraint!)

### 5. Context Managers

**Location**: `streamrip/rip/cli.py`, `streamrip/client/client.py`

```python
async with Main(cfg) as main:
    await main.add_all(urls)
    await main.resolve()
    await main.rip()
```

**Why?**
- **Resource Management**: Ensures cleanup (close HTTP sessions, etc.)
- **Error Safety**: Cleanup happens even if exceptions occur
- **Clear Lifecycle**: Entry and exit points are explicit

### 6. Semaphore for Concurrency Control

**Location**: `streamrip/media/semaphore.py`

```python
async with global_download_semaphore(config.session.downloads):
    await downloadable.download(path, callback)
```

**Why?**
- **Rate Limiting**: Prevents overwhelming the API
- **Resource Control**: Limits concurrent downloads
- **Politeness**: Respects service limits

**How it works:**
- Semaphore acts as a "ticket booth"
- Only N downloads can run simultaneously
- Others wait in queue until a slot opens

---

## Code Organization

### Directory Structure Explained

```
streamrip/
├── client/              # API client implementations
│   ├── client.py        # Base Client ABC
│   ├── qobuz.py         # Qobuz-specific implementation
│   ├── tidal.py         # Tidal-specific implementation
│   ├── deezer.py        # Deezer-specific implementation
│   └── downloadable.py  # Download URL abstractions
│
├── media/               # Media types (Track, Album, etc.)
│   ├── media.py         # Base Media ABC
│   ├── track.py         # Track implementation
│   ├── album.py         # Album implementation
│   ├── playlist.py      # Playlist implementation
│   └── artwork.py       # Cover art downloading
│
├── metadata/            # Metadata handling & tagging
│   ├── track.py         # Track metadata
│   ├── album.py         # Album metadata
│   ├── tagger.py        # File tagging logic
│   └── covers.py        # Cover art processing
│
├── rip/                 # CLI & orchestration
│   ├── cli.py           # Click command definitions
│   ├── main.py          # Main orchestration logic
│   ├── parse_url.py     # URL parsing
│   └── prompter.py      # Interactive prompts
│
├── config.py            # Configuration management
├── db.py                # SQLite database wrapper
├── converter.py         # Audio format conversion
├── exceptions.py        # Custom exceptions
└── progress.py          # Progress bar handling
```

**Organizational Principles:**
1. **Feature-based**: Each directory represents a major feature
2. **Layered**: Higher-level modules import from lower-level ones
3. **No circular dependencies**: Clean dependency graph
4. **Single Responsibility**: Each file has one clear purpose

---

## Key Concepts

### 1. Async/Await Everywhere

StreamRip is **fully asynchronous** using Python's `asyncio`:

```python
async def download(self):
    async with global_download_semaphore(self.config.session.downloads):
        await self.downloadable.download(self.download_path, callback)
```

**Why async?**
- **I/O Bound Operations**: Downloading files is network I/O
- **Concurrency**: Can download multiple files simultaneously
- **Efficiency**: While waiting for one download, start another

**Key Async Patterns in StreamRip:**

**1. Gather for Parallelism:**
```python
results = await asyncio.gather(
    *[_resolve_and_download(p) for p in self.tracks],
    return_exceptions=True
)
```
- Runs all track downloads concurrently
- `return_exceptions=True` prevents one failure from stopping others

**2. Create_task for Background Work:**
```python
version_coro = asyncio.create_task(
    latest_streamrip_version(verify_ssl=cfg.session.downloads.verify_ssl)
)
```
- Starts version check in background
- Main work continues without blocking

### 2. Configuration Management

**Location**: `streamrip/config.py`, `streamrip/config.toml`

StreamRip uses **TOML** for human-readable configuration:

```toml
[qobuz]
quality = 3  # 24-bit audio
email_or_userid = "user@example.com"
```

**Design Decisions:**
1. **Dataclasses for Config**: Type-safe, auto-completion friendly
2. **Default Config**: Bundled with package
3. **User Override**: User config in `~/.config/streamrip/`
4. **Version Tracking**: Config version for migration

**Config Loading Flow:**
```python
config = Config(config_path)
with config as cfg:  # Context manager
    # Config is active here
    async with Main(cfg) as main:
        await main.rip()
# Config saved automatically on exit
```

### 3. Database Design

**Location**: `streamrip/db.py`

StreamRip uses **SQLite** to track downloads:

**Two tables:**
1. **Downloads**: Stores IDs of downloaded items
2. **Failed**: Stores failed download attempts

**Why SQLite?**
- **Embedded**: No separate database server
- **Portable**: Single file
- **Fast**: Efficient for read-heavy workloads
- **ACID**: Transactional guarantees

**Pattern Used:**
```python
class DatabaseBase(DatabaseInterface):
    """Base class with common SQLite operations"""

class Downloads(DatabaseBase):
    """Concrete implementation for downloads table"""
    name = "downloads"
    structure = {"id": ["text", "unique"]}

class Dummy(DatabaseInterface):
    """Null object pattern - when DB is disabled"""
```

**Null Object Pattern** (`Dummy` class):
- Same interface as real database
- Does nothing
- Avoids `if db is None` checks everywhere

### 4. Error Handling Strategy

StreamRip has **granular error handling**:

**Custom Exceptions:**
```python
class NonStreamableError(Exception):
    """Item is not streamable."""

class AuthenticationError(Exception):
    """Authentication failed."""

class IneligibleError(Exception):
    """Account not eligible to stream."""
```

**Why custom exceptions?**
- **Specificity**: Different errors need different handling
- **User Messages**: Can provide helpful context
- **Recovery**: Can retry or fallback based on error type

**Error Handling Levels:**

**1. Track Level:**
```python
try:
    await track.rip()
except Exception as e:
    logger.error(f"Error downloading track: {e}")
    # Continue with next track
```

**2. Album Level:**
```python
results = await asyncio.gather(*tasks, return_exceptions=True)
for result in results:
    if isinstance(result, Exception):
        logger.error(f"Album track processing error: {result}")
```

**3. CLI Level:**
```python
except aiohttp.ClientConnectorCertificateError as e:
    console.print(f"[red]SSL Certificate verification error: {e}[/red]")
    print_ssl_error_help()
```

**Philosophy**: Fail gracefully at the lowest level possible.

### 5. Metadata Extraction

**Location**: `streamrip/metadata/`

Each service returns different JSON structures. StreamRip normalizes them:

```python
class TrackMetadata:
    @classmethod
    def from_resp(cls, album: AlbumMetadata, source: str, resp: dict):
        """Extract metadata from API response."""
        # Different parsing logic per source
        if source == "qobuz":
            return cls._from_qobuz(album, resp)
        elif source == "tidal":
            return cls._from_tidal(album, resp)
        # ...
```

**Why?**
- **Abstraction**: Rest of code doesn't know about API differences
- **Validation**: Can check for required fields
- **Defaults**: Can provide fallback values

---

## Best Practices Demonstrated

### 1. Type Hints Everywhere

```python
async def get_downloadable(self, item: str, quality: int) -> Downloadable:
    """Returns a downloadable URL for the item."""
```

**Benefits:**
- **IDE Support**: Auto-completion, inline docs
- **Type Checking**: Catch errors before runtime
- **Documentation**: Types serve as inline docs
- **Refactoring Safety**: IDE can track usages

### 2. Logging Strategy

```python
logger = logging.getLogger("streamrip")
logger.debug("Added url=%s", url)
logger.error(f"Error downloading track '{self.meta.title}': {e}")
```

**Logging Levels Used:**
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `ERROR`: Error events that might still allow the app to continue

**Why not print?**
- **Configurable**: Can change verbosity
- **Structured**: Can route to files, services
- **Levels**: Different severity levels

### 3. Separation of CLI and Business Logic

**CLI Layer** (`rip/cli.py`):
- Handles command parsing
- User input/output
- Configuration loading

**Business Logic** (`rip/main.py`, `media/`, `client/`):
- Core download logic
- API interactions
- File operations

**Why?**
- **Testability**: Can test business logic without CLI
- **Reusability**: Business logic can be used in other contexts
- **Clarity**: Each layer has clear responsibilities

### 4. Dependency Injection

```python
class Track(Media):
    def __init__(
        self,
        meta: TrackMetadata,
        downloadable: Downloadable,
        config: Config,
        folder: str,
        cover_path: str | None,
        db: Database,
    ):
```

**Why inject dependencies?**
- **Testing**: Can pass mock objects
- **Flexibility**: Can change implementations
- **Explicit**: All dependencies are visible

### 5. Configuration Over Code

StreamRip uses **declarative configuration**:

```python
# Bad: Hardcoded
MAX_DOWNLOADS = 5

# Good: Configurable
max_downloads = config.session.downloads.concurrent_downloads
```

**Benefits:**
- **User Control**: Users can customize behavior
- **No Recompilation**: Change settings without code changes
- **Environment-Specific**: Different configs for different setups

### 6. Retry Logic

```python
try:
    await self.downloadable.download(self.download_path, callback)
    retry = False
except Exception as e:
    logger.error(f"Error downloading, retrying: {e}")
    retry = True

if retry:
    # Try again
```

**Why retry?**
- **Network Flakiness**: Temporary failures are common
- **User Experience**: Automatic recovery is better
- **But**: Limits retries to avoid infinite loops

### 7. Progress Feedback

Uses `rich` library for beautiful CLI output:

```python
with get_progress_callback(
    self.config.session.cli.progress_bars,
    await self.downloadable.size(),
    f"Track {self.meta.tracknumber}",
) as callback:
    await self.downloadable.download(self.download_path, callback)
```

**Why?**
- **User Feedback**: Users know what's happening
- **Debugging**: Can see where things slow down
- **Professional**: Polished user experience

### 8. Resource Cleanup

**Always** cleans up resources:

```python
async def __aenter__(self):
    # Setup
    self.session = aiohttp.ClientSession()
    return self

async def __aexit__(self, *_):
    # Cleanup
    if self.session is not None:
        await self.session.close()
```

**Why context managers?**
- **Guaranteed Cleanup**: Even on exceptions
- **No Resource Leaks**: Prevents memory/connection leaks
- **Clear Lifecycle**: Obvious when resources are active

---

## Learning Opportunities

### For Beginners

**1. Start Here:**
- `streamrip/exceptions.py` - Simple custom exceptions
- `streamrip/db.py` - Clean OOP with SQLite
- `streamrip/media/media.py` - ABC basics

**2. Concepts to Learn:**
- **Abstract Base Classes (ABC)**: Defining interfaces
- **Type Hints**: Making code self-documenting
- **Context Managers**: Resource management
- **Logging**: Better than print statements

### For Intermediate Developers

**1. Study These:**
- `streamrip/media/track.py` - Async lifecycle management
- `streamrip/client/client.py` - Strategy pattern
- `streamrip/rip/main.py` - Orchestration logic

**2. Concepts to Learn:**
- **Async/Await**: Concurrency without threading
- **Dataclasses**: Clean data containers
- **Design Patterns**: Strategy, Template Method, Pending/Resolved
- **Error Handling**: Graceful degradation

### For Advanced Developers

**1. Deep Dive:**
- `streamrip/client/qobuz.py` - Complex API interaction (see QobuzSpoofer)
- `streamrip/metadata/tagger.py` - Audio file manipulation
- `streamrip/converter.py` - FFmpeg integration

**2. Concepts to Master:**
- **Rate Limiting**: aiolimiter, semaphores
- **Binary Protocols**: Audio file formats
- **Process Management**: Subprocess handling
- **Security**: SSL, authentication, secrets

### Suggested Learning Path

**Week 1-2: Understanding the Flow**
1. Read `README.md` - Understand what the tool does
2. Run the tool - Experience it as a user
3. Trace one download from CLI to file:
   - Start at `rip/cli.py::url()`
   - Follow to `rip/main.py::add()` and `resolve()`
   - See `media/track.py::rip()`

**Week 3-4: Design Patterns**
1. Identify all ABC classes - Why are they abstract?
2. Map the Pending → Media pattern
3. Compare Qobuz vs Tidal clients - How do they differ?
4. Study error handling - Where are exceptions caught?

**Week 5-6: Async Mastery**
1. Count all `async`/`await` keywords
2. Find all `asyncio.gather()` calls - Why are they needed?
3. Understand the semaphore usage
4. Try adding a new async operation

**Week 7-8: Extending**
1. Add a new command to the CLI
2. Implement a mock client for testing
3. Add a new metadata field
4. Write tests for a component

---

## Code Quality Highlights

### What Makes This Codebase Good?

**✅ Consistent Style:**
- Uses `black` formatter (see `pyproject.toml`)
- Uses `ruff` linter
- Type hints throughout

**✅ Good Documentation:**
- Docstrings on complex functions
- README with examples
- Configuration documentation

**✅ Error Handling:**
- Specific exceptions
- Graceful degradation
- User-friendly messages

**✅ Testing:**
- Unit tests in `tests/`
- Fixtures for reusable test data
- Async test support

**✅ Maintainability:**
- Clear module boundaries
- No circular dependencies
- Configuration version tracking

### Potential Improvements (Learning Exercise)

These aren't necessarily problems, but areas to explore:

**1. More Type Strictness:**
```python
# Current
def format_folder_path(self, formatter: str) -> str:
    pass

# Could be
from typing import Literal
FormatString = str  # NewType
def format_folder_path(self, formatter: FormatString) -> str:
    pass
```

**2. More Comprehensive Error Types:**
```python
# Could add
class NetworkError(Exception): pass
class RateLimitError(Exception): pass
class QuotaExceededError(Exception): pass
```

**3. Metrics/Observability:**
```python
# Could track
- Download speeds
- Success/failure rates
- API response times
```

**4. Plugin Architecture:**
- Currently adding a service requires modifying core code
- Could use plugin system for extensibility

---

## Common Patterns to Notice

### Pattern 1: "Try-Resolve-Handle"

Throughout the codebase:
```python
try:
    resp = await self.client.get_metadata(self.id, "track")
except NonStreamableError as e:
    logger.error(f"Track {self.id} not available: {e}")
    return None

meta = TrackMetadata.from_resp(album, source, resp)
if meta is None:
    logger.error(f"Track {self.id} not available")
    return None

return Track(meta, ...)
```

**Pattern**: Try → Parse → Validate → Create or None

### Pattern 2: "Batch Gather"

```python
results = await asyncio.gather(
    *[_resolve_and_download(p) for p in self.tracks],
    return_exceptions=True
)
```

**Pattern**: Create all tasks → Gather → Handle results

### Pattern 3: "Config Cascade"

```python
quality = self.config.session.get_source(source).quality
```

**Pattern**: Global config → Session config → Source config

### Pattern 4: "Database Check-Skip-Mark"

```python
if self.db.downloaded(self.id):
    logger.info("Skipping, already downloaded")
    return None

# ... do work ...

self.db.set_downloaded(self.meta.info.id)
```

**Pattern**: Check DB → Skip if exists → Mark when done

---

## Architecture Decisions & Trade-offs

### Decision 1: Async Over Threading

**Choice**: Used `asyncio` instead of `threading`

**Why?**
- ✅ Better for I/O-bound operations
- ✅ Lower memory overhead
- ✅ Easier to reason about (no locks needed)
- ✅ Better error handling

**Trade-off**:
- ❌ Can't use blocking libraries easily
- ❌ Requires `async`/`await` everywhere
- ❌ Slightly steeper learning curve

### Decision 2: SQLite Over JSON

**Choice**: Used SQLite for download tracking

**Why?**
- ✅ ACID transactions
- ✅ Efficient queries
- ✅ No data corruption
- ✅ Can handle large datasets

**Trade-off**:
- ❌ Binary file (not human-readable)
- ❌ Schema changes need migration
- ❌ Slightly more complex than JSON

### Decision 3: CLI Over GUI

**Choice**: Command-line interface only

**Why?**
- ✅ Scriptable/automatable
- ✅ Lower complexity
- ✅ Cross-platform (terminal is universal)
- ✅ Lower resource usage

**Trade-off**:
- ❌ Less user-friendly for non-technical users
- ❌ No visual feedback (beyond text)

### Decision 4: Dependency Injection Over Singletons

**Choice**: Pass dependencies explicitly

**Why?**
- ✅ Testable (can inject mocks)
- ✅ Explicit dependencies
- ✅ No global state

**Trade-off**:
- ❌ More verbose initialization
- ❌ Many parameters to pass around

---

## Testing Strategy

### Test Organization

```
tests/
├── fixtures/           # Reusable test data & mocks
│   ├── clients.py      # Mock clients
│   └── config.py       # Test configs
├── test_track.py       # Track download tests
├── test_config.py      # Config loading tests
└── test_parse_url.py   # URL parsing tests
```

### Testing Approach

**1. Fixtures for Reusability:**
```python
@pytest.fixture
def qobuz_client():
    """Provides a configured Qobuz client for tests."""
    config = Config("tests/test_config.toml")
    return QobuzClient(config)
```

**2. Async Test Support:**
```python
@pytest.mark.asyncio
async def test_download_track(qobuz_client):
    """Test that a track downloads successfully."""
    track = await qobuz_client.get_metadata("123", "track")
    assert track is not None
```

**3. Mock External Services:**
- Don't make real API calls in tests
- Use recorded responses
- Mock the HTTP client

---

## Final Thoughts

### What Makes This Codebase Educational?

**1. Real-World Complexity:**
- Not a toy project
- Handles actual production concerns
- Deals with external APIs, errors, rate limits

**2. Modern Python:**
- Uses Python 3.10+ features
- Type hints throughout
- Async/await patterns
- Dataclasses with slots

**3. Good Engineering:**
- Clear architecture
- Design patterns
- Error handling
- Configuration management
- Testing

**4. Room for Growth:**
- Can add new features
- Can improve existing code
- Can learn by extending

### How to Use This Codebase for Learning

**Passive Learning:**
1. Read the code
2. Follow the data flow
3. Identify patterns
4. Understand decisions

**Active Learning:**
1. Add logging to trace execution
2. Add a new command
3. Implement a mock client
4. Write tests for untested code
5. Add a new metadata field
6. Improve error messages

**Mastery:**
1. Refactor a module
2. Add a new streaming service
3. Implement caching
4. Add metrics/monitoring
5. Create a plugin system

---

## Quick Reference

### Key Files to Start With

| File | Purpose | Complexity |
|------|---------|------------|
| `streamrip/media/media.py` | Core abstractions | ⭐ Easy |
| `streamrip/db.py` | Database wrapper | ⭐ Easy |
| `streamrip/exceptions.py` | Custom exceptions | ⭐ Easy |
| `streamrip/media/track.py` | Track download logic | ⭐⭐ Medium |
| `streamrip/media/album.py` | Album download logic | ⭐⭐ Medium |
| `streamrip/client/client.py` | Client abstraction | ⭐⭐ Medium |
| `streamrip/rip/main.py` | Main orchestration | ⭐⭐⭐ Advanced |
| `streamrip/client/qobuz.py` | Qobuz API client | ⭐⭐⭐ Advanced |
| `streamrip/metadata/tagger.py` | Audio file tagging | ⭐⭐⭐ Advanced |

### Design Patterns Used

- ✅ Abstract Base Class (ABC)
- ✅ Template Method
- ✅ Strategy
- ✅ Dependency Injection
- ✅ Context Manager
- ✅ Null Object
- ✅ Pending/Resolved (Custom)

### Python Features Demonstrated

- ✅ Async/Await (`asyncio`, `aiohttp`)
- ✅ Type Hints (PEP 484)
- ✅ Dataclasses (PEP 557)
- ✅ Context Managers (`__enter__`/`__exit__`)
- ✅ Abstract Base Classes (`abc.ABC`)
- ✅ Decorators (`@abstractmethod`, `@dataclass`)
- ✅ Generators (limited use)
- ✅ Union Types (`str | None`)

### External Libraries Worth Learning

- `aiohttp` - Async HTTP client
- `click` - CLI framework
- `rich` - Terminal formatting
- `mutagen` - Audio metadata
- `tomlkit` - TOML parsing
- `pytest` - Testing framework
- `aiolimiter` - Async rate limiting

---

## Conclusion

StreamRip demonstrates **professional Python development** with:
- Clean architecture
- Modern async patterns
- Proper error handling
- Good testing practices
- Comprehensive configuration
- User-friendly CLI

It's an excellent codebase to learn from because it:
- Solves real problems
- Uses modern Python features
- Demonstrates design patterns
- Has room for experimentation
- Is actively maintained

**Happy Learning! 🎓**

---

*This educational review was created to help developers understand the architecture and design decisions in the StreamRip codebase. For questions or improvements, please refer to the project's GitHub repository.*
