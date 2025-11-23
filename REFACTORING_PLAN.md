# Comprehensive Refactoring Plan for Streamrip

**Version:** 1.0
**Date:** 2025-11-23
**Current Version:** 2.1.0
**Target Version:** 3.0.0

---

## Executive Summary

This document outlines a comprehensive refactoring plan for the Streamrip music downloader. The project is a well-structured Python CLI tool with ~7,400 lines of code across 58 Python files. While the codebase demonstrates good async architecture and modular design, several critical issues affect testability, maintainability, and reliability.

**Key Issues Identified:**
1. Global state management (progress manager, semaphore)
2. Sync/async code mixing causing potential event loop blocking
3. Inconsistent error handling and type safety
4. Tight coupling between configuration and clients
5. Large files requiring decomposition
6. Missing dependency injection patterns

**Estimated Scope:** This is a major refactoring that should be treated as a v3.0.0 release due to breaking changes.

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Refactoring Objectives](#2-refactoring-objectives)
3. [Phase 1: Foundation & Infrastructure](#3-phase-1-foundation--infrastructure)
4. [Phase 2: Core Architecture Improvements](#4-phase-2-core-architecture-improvements)
5. [Phase 3: Client Layer Refactoring](#5-phase-3-client-layer-refactoring)
6. [Phase 4: Media Layer Refactoring](#6-phase-4-media-layer-refactoring)
7. [Phase 5: Configuration & Dependency Injection](#7-phase-5-configuration--dependency-injection)
8. [Phase 6: Testing & Quality Assurance](#8-phase-6-testing--quality-assurance)
9. [Phase 7: Documentation & Polish](#9-phase-7-documentation--polish)
10. [Migration Guide](#10-migration-guide)
11. [Success Metrics](#11-success-metrics)
12. [Risk Assessment](#12-risk-assessment)

---

## 1. Current State Analysis

### 1.1 Repository Structure

```
streamrip/
├── rip/                    # CLI entry point (4 files, ~1,242 lines)
│   ├── cli.py             # Click-based CLI (481 lines)
│   ├── main.py            # Download orchestration (306 lines)
│   ├── parse_url.py       # URL parsing (237 lines)
│   └── prompter.py        # Credential management (218 lines)
├── client/                 # API clients (5 files, ~1,777 lines)
│   ├── qobuz.py           # Qobuz API (455 lines)
│   ├── tidal.py           # Tidal OAuth (359 lines)
│   ├── soundcloud.py      # SoundCloud API (303 lines)
│   ├── downloadable.py    # Download abstraction (434 lines)
│   └── deezer.py          # Deezer API (226 lines)
├── media/                  # Media types (8 files, ~1,800 lines)
│   ├── album.py           # Album downloads (520 lines)
│   ├── playlist.py        # Playlists (410 lines)
│   ├── track.py           # Single tracks (268 lines)
│   ├── artist.py          # Artist discography (208 lines)
│   └── ...
├── metadata/              # Metadata handling (6 files, ~1,400 lines)
├── config.py              # Configuration (476 lines)
├── converter.py           # FFmpeg wrapper (292 lines)
├── db.py                  # Database layer (196 lines)
├── progress.py            # Progress UI (114 lines) ⚠️ GLOBAL STATE
└── exceptions.py          # Custom exceptions
```

**Total:** 7,437 lines of Python code

### 1.2 Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.10+ |
| CLI Framework | Click | Latest |
| Async Runtime | asyncio | Built-in |
| HTTP Client | aiohttp + requests* | ^3.9 |
| UI/Progress | Rich | ^13.6 |
| Config Format | TOML (tomlkit) | ^0.7 |
| Audio Tags | mutagen | ^1.45 |
| Database | sqlite3 | Built-in |
| Testing | pytest, pytest-asyncio | ^7.4 |
| Linting | ruff, black | ^0.1 |

*⚠️ Problematic mixing of sync `requests` in async context

### 1.3 Critical Issues

#### 🔴 **Priority 1: Global State Management**

**Files Affected:**
- `streamrip/progress.py:91` - Global `_p` ProgressManager instance
- `streamrip/media/semaphore.py:7` - Global `_global_semaphore`

**Problem:**
```python
# progress.py
_p = ProgressManager()  # Module-level global

def get_progress_callback(enabled: bool, total: int, desc: str):
    global _p  # Accessed via global keyword
    return _p.get_callback(total, desc)
```

**Impact:**
- Not thread-safe or process-safe
- Impossible to test in isolation
- State persists across test runs
- Cannot run multiple Main instances simultaneously
- Violates dependency inversion principle

**Solution:** Dependency injection pattern (see Phase 1)

---

#### 🔴 **Priority 1: Sync/Async Code Mixing**

**File:** `streamrip/client/downloadable.py:40-63`

**Problem:**
```python
async def fast_async_download(path, url, headers, callback):
    # Using blocking requests.get() inside async function
    with requests.get(url, stream=True) as resp:  # ❌ BLOCKING
        for chunk in resp.iter_content(chunk_size=chunk_size):
            file.write(chunk)  # ❌ BLOCKING I/O
            if counter % yield_every == 0:
                await asyncio.sleep(0)  # Too late, already blocked
```

**Impact:**
- Blocks the event loop during downloads
- Defeats the purpose of async/await
- Limits concurrent download performance
- Can cause timeouts in other async operations

**Justification in Comments:**
> "Using aiofiles/aiohttp resulted in a yield to the event loop for every 1KB"

**Analysis:**
- The comment suggests aiohttp was too slow
- Current solution trades correctness for perceived speed
- Need to benchmark proper async implementation with tuned buffer sizes

**Solution:** Replace with `aiohttp` using larger chunk sizes (see Phase 2)

---

#### 🟡 **Priority 2: Error Handling**

**Problem:** Overly broad exception catching throughout codebase

**Examples:**
```python
# rip/main.py - Too generic
try:
    await media.rip()
except Exception as e:  # ❌ Catches everything
    logger.error("Download failed: %s", e)

# parse_url.py - Generic exception
if parsed is None:
    raise Exception(f"Unable to parse url {url}")  # ❌ Should be custom type
```

**Impact:**
- Masks underlying bugs
- Difficult to debug failures
- Cannot distinguish between error types
- Swallows unexpected errors

**Solution:** Create exception hierarchy (see Phase 1)

---

#### 🟡 **Priority 2: Type Safety**

**Problem:** Inconsistent type hint usage

**Issues:**
1. Mix of `Optional[X]` and `X | None` syntax
2. Some files use `from __future__ import annotations`, others don't
3. `Any` type used liberally in `cli.py`
4. No mypy enforcement in CI
5. Abstract methods sometimes lack return type hints

**Examples:**
```python
# Inconsistent Optional syntax
def foo(x: Optional[str]) -> int: ...  # Old style
def bar(x: str | None) -> int: ...     # New style (3.10+)

# Missing type hints
def _add_by_id_client(self, client: Client, media_type: str, id: str):
    # No return type hint
```

**Solution:** Standardize on Python 3.10+ union syntax, add mypy (see Phase 1)

---

#### 🟡 **Priority 2: Configuration Coupling**

**Problem:** Clients directly access nested config structures

**Example:**
```python
# client/qobuz.py
class QobuzClient(Client):
    def __init__(self, config: Config):
        self.global_config = config  # Stores entire config
        # Later accesses deep paths:
        if config.session.downloads.verify_ssl:
            ...
```

**Impact:**
- Changes to config structure break clients
- Difficult to test clients in isolation
- Violates interface segregation principle
- Tight coupling across layers

**Solution:** Pass only required config sections (see Phase 5)

---

#### 🟢 **Priority 3: Code Organization**

**Large Files Requiring Decomposition:**

| File | Lines | Suggested Split |
|------|-------|-----------------|
| `metadata/album.py` | 520 | Split into album_metadata.py, album_formatter.py |
| `rip/cli.py` | 481 | Split into cli_commands.py, cli_utils.py |
| `config.py` | 476 | Split into config_schema.py, config_loader.py |
| `client/qobuz.py` | 455 | Extract spoofer to qobuz_auth.py |
| `client/downloadable.py` | 434 | Split by download type |
| `media/album.py` | 520 | Extract concurrent logic to album_downloader.py |

---

### 1.4 Code Quality Metrics

**Static Analysis Results:**

```bash
# Lines of code
find streamrip -name "*.py" | xargs wc -l
Total: 7,437 lines

# TODO/FIXME count
grep -r "TODO\|FIXME" streamrip/*.py
Total: 13 unresolved TODOs

# Test coverage (estimated)
Tests: 14 test files, ~1,200 lines
Coverage: ~60% (no integration tests)
```

**Key TODOs to Address:**
1. `converter.py:161` - Error handling for lossy codecs
2. `filepath_utils.py:8` - Waiting for pathvalidate release
3. `parse_url.py:235` - Missing URL types
4. `deezer.py:57` - Async integration for deezer-py
5. `downloadable.py:338` - Progress bar for HLS streams

---

## 2. Refactoring Objectives

### 2.1 Primary Goals

1. **Eliminate Global State**
   - Remove all module-level singletons
   - Implement dependency injection
   - Make code testable in isolation

2. **Fix Async/Await Correctness**
   - Replace blocking `requests` with `aiohttp`
   - Ensure no blocking I/O in async context
   - Benchmark and validate performance

3. **Improve Error Handling**
   - Create comprehensive exception hierarchy
   - Replace generic exceptions with specific types
   - Add proper error recovery mechanisms

4. **Enhance Type Safety**
   - Add complete type hints to all functions
   - Enable strict mypy checking
   - Standardize on Python 3.10+ syntax

5. **Decouple Configuration**
   - Use dependency injection for config
   - Pass only required config sections
   - Create immutable config objects

6. **Improve Testability**
   - Add integration tests
   - Increase test coverage to >80%
   - Make all components mockable

### 2.2 Secondary Goals

1. Break down large files into focused modules
2. Resolve all TODO/FIXME comments
3. Standardize docstring format (Google style)
4. Add comprehensive logging
5. Improve CLI user experience
6. Add performance benchmarks

### 2.3 Non-Goals

❌ **NOT in scope for this refactoring:**
- Adding new streaming service support
- Changing configuration file format
- Rewriting in another language
- Major UI/UX redesign
- Adding GUI interface

---

## 3. Phase 1: Foundation & Infrastructure

**Duration:** 2-3 weeks
**Risk Level:** Low
**Breaking Changes:** None

### 3.1 Exception Hierarchy

**Objective:** Create a well-designed exception hierarchy

**Current State:**
- Generic `Exception` used throughout
- No custom exception types for specific errors
- Error context often lost

**Implementation:**

```python
# streamrip/exceptions.py - REFACTORED

class StreamripError(Exception):
    """Base exception for all streamrip errors."""
    pass


# Network & API Errors
class NetworkError(StreamripError):
    """Base for all network-related errors."""
    pass


class APIError(NetworkError):
    """API returned an error response."""
    def __init__(self, source: str, status_code: int, message: str):
        self.source = source
        self.status_code = status_code
        super().__init__(f"{source} API error {status_code}: {message}")


class AuthenticationError(APIError):
    """Authentication failed."""
    pass


class RateLimitError(APIError):
    """Rate limit exceeded."""
    def __init__(self, source: str, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(source, 429, "Rate limit exceeded")


# Parsing Errors
class ParseError(StreamripError):
    """Failed to parse input."""
    pass


class URLParseError(ParseError):
    """Failed to parse URL."""
    def __init__(self, url: str, reason: str | None = None):
        self.url = url
        msg = f"Cannot parse URL: {url}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)


# Download Errors
class DownloadError(StreamripError):
    """Download failed."""
    pass


class NonStreamableError(DownloadError):
    """Media is not streamable (already defined, keep as-is)."""
    pass


class DecryptionError(DownloadError):
    """Failed to decrypt media."""
    pass


# Metadata Errors
class MetadataError(StreamripError):
    """Metadata operation failed."""
    pass


class TaggingError(MetadataError):
    """Failed to tag audio file."""
    def __init__(self, path: str, reason: str):
        self.path = path
        super().__init__(f"Cannot tag {path}: {reason}")


# Config Errors
class ConfigError(StreamripError):
    """Configuration error."""
    pass


class OutdatedConfigError(ConfigError):
    """Config version is outdated (already defined, keep as-is)."""
    pass


# Conversion Errors
class ConversionError(StreamripError):
    """Audio conversion failed."""
    def __init__(self, source_path: str, target_codec: str, reason: str):
        self.source_path = source_path
        self.target_codec = target_codec
        super().__init__(f"Cannot convert {source_path} to {target_codec}: {reason}")
```

**Migration Tasks:**

1. Replace all `raise Exception()` with appropriate custom exceptions
2. Update exception handlers to catch specific types
3. Add error context to all exceptions
4. Document exception contracts in docstrings

**Files to Update:**
- `rip/parse_url.py` - Use `URLParseError`
- `rip/main.py` - Catch specific error types
- `client/*.py` - Use `APIError`, `AuthenticationError`
- `metadata/tagger.py` - Use `TaggingError`
- `converter.py` - Use `ConversionError`

---

### 3.2 Type System Modernization

**Objective:** Full type hint coverage with mypy enforcement

**Tasks:**

1. **Standardize Import Style**
   ```python
   # Add to ALL files
   from __future__ import annotations

   # Use Python 3.10+ union syntax
   def foo(x: str | None) -> int: ...  # ✅
   def bar(x: Optional[str]) -> int: ... # ❌
   ```

2. **Add Missing Type Hints**
   - All function signatures
   - All class attributes
   - All module-level variables

3. **Configure Mypy**
   ```toml
   # pyproject.toml - ADD THIS SECTION
   [tool.mypy]
   python_version = "3.10"
   warn_return_any = true
   warn_unused_configs = true
   disallow_untyped_defs = true
   disallow_incomplete_defs = true
   check_untyped_defs = true
   disallow_untyped_calls = true
   no_implicit_optional = true
   warn_redundant_casts = true
   warn_unused_ignores = true
   warn_no_return = true
   strict_equality = true

   [[tool.mypy.overrides]]
   module = [
       "mutagen.*",
       "deezer.*",
       "m3u8.*",
       "tomlkit.*",
   ]
   ignore_missing_imports = true
   ```

4. **Add to CI Pipeline**
   ```yaml
   # .github/workflows/ci.yml
   - name: Type check with mypy
     run: poetry run mypy streamrip
   ```

**Files Requiring Major Type Work:**
- `rip/cli.py` - Many `Any` types
- `client/downloadable.py` - Callback types unclear
- `media/*.py` - Abstract methods need full signatures

---

### 3.3 Testing Infrastructure

**Objective:** Improve test infrastructure and coverage

**Current Coverage:** ~60% (estimated)
**Target Coverage:** >80%

**Tasks:**

1. **Add Coverage Reporting**
   ```toml
   # pyproject.toml
   [tool.poetry.dev-dependencies]
   pytest-cov = "^4.1.0"

   [tool.pytest.ini_options]
   addopts = "--cov=streamrip --cov-report=html --cov-report=term"
   ```

2. **Create Test Fixtures**
   ```python
   # tests/conftest.py - NEW FILE
   import pytest
   from streamrip.config import Config
   from streamrip.progress import ProgressManager

   @pytest.fixture
   def mock_config():
       """Provides isolated config for testing."""
       return Config.defaults()

   @pytest.fixture
   def progress_manager():
       """Provides fresh ProgressManager for each test."""
       return ProgressManager()

   @pytest.fixture
   def mock_client(mocker):
       """Provides mocked client for testing."""
       # ... implementation
   ```

3. **Add Integration Tests**
   ```python
   # tests/integration/test_download_flow.py - NEW FILE
   """End-to-end download flow tests."""

   async def test_full_album_download(tmp_path, mock_config):
       """Test complete album download pipeline."""
       # ... implementation

   async def test_error_recovery(tmp_path, mock_config):
       """Test error handling and recovery."""
       # ... implementation
   ```

---

### 3.4 Logging Improvements

**Objective:** Standardize logging across the application

**Current Issues:**
- Inconsistent logger naming
- Module-level `logger` variables (global state)
- Missing structured logging

**Implementation:**

```python
# streamrip/logging_config.py - NEW FILE
import logging
import sys
from typing import Any

def setup_logging(level: str = "INFO") -> None:
    """Configure application-wide logging."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
        ],
    )

def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given module."""
    return logging.getLogger(f"streamrip.{name}")


# Usage in modules:
# Instead of: logger = logging.getLogger("streamrip")
# Use: logger = get_logger(__name__)
```

**Tasks:**
1. Replace all `logging.getLogger("streamrip")` with `get_logger(__name__)`
2. Add structured logging for key events
3. Add debug logging for troubleshooting
4. Remove module-level logger globals

---

## 4. Phase 2: Core Architecture Improvements

**Duration:** 3-4 weeks
**Risk Level:** Medium-High
**Breaking Changes:** Yes (internal APIs)

### 4.1 Dependency Injection for ProgressManager

**Objective:** Eliminate global `_p` singleton

**Current Implementation:**
```python
# streamrip/progress.py - CURRENT
_p = ProgressManager()  # Global singleton

def get_progress_callback(enabled: bool, total: int, desc: str):
    global _p
    return _p.get_callback(total, desc)
```

**Refactored Implementation:**

```python
# streamrip/progress.py - REFACTORED

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol


class ProgressCallback(Protocol):
    """Protocol for progress callbacks."""
    def __call__(self, bytes_downloaded: int) -> None: ...


class ProgressHandle(Protocol):
    """Context manager for progress tracking."""
    def __enter__(self) -> ProgressCallback: ...
    def __exit__(self, *args) -> None: ...


class ProgressReporter:
    """Interface for progress reporting."""

    def get_callback(self, total: int, desc: str) -> ProgressHandle:
        """Get a progress callback for tracking downloads."""
        raise NotImplementedError

    def add_title(self, title: str) -> None:
        """Add a title to the progress display."""
        raise NotImplementedError

    def remove_title(self, title: str) -> None:
        """Remove a title from the progress display."""
        raise NotImplementedError

    def cleanup(self) -> None:
        """Clean up progress display resources."""
        raise NotImplementedError


class RichProgressReporter(ProgressReporter):
    """Rich-based progress reporter implementation."""

    def __init__(self):
        self.started = False
        # ... (rest of current ProgressManager implementation)

    # ... implement all methods


class NoOpProgressReporter(ProgressReporter):
    """No-op progress reporter for headless/testing."""

    @dataclass(slots=True)
    class _NoOpHandle:
        def __enter__(self) -> Callable[[int], None]:
            return lambda _: None

        def __exit__(self, *_) -> None:
            pass

    def get_callback(self, total: int, desc: str) -> ProgressHandle:
        return self._NoOpHandle()

    def add_title(self, title: str) -> None:
        pass

    def remove_title(self, title: str) -> None:
        pass

    def cleanup(self) -> None:
        pass


# Factory function
def create_progress_reporter(enabled: bool) -> ProgressReporter:
    """Create appropriate progress reporter based on config."""
    if enabled:
        return RichProgressReporter()
    return NoOpProgressReporter()
```

**Migration:**

```python
# streamrip/rip/main.py - UPDATED
class Main:
    def __init__(self, config: Config, progress: ProgressReporter | None = None):
        self.config = config
        self.progress = progress or create_progress_reporter(
            config.session.downloads.progress_bars
        )
        # ... rest of initialization

    async def cleanup(self):
        self.progress.cleanup()
        # ... rest of cleanup


# streamrip/media/track.py - UPDATED
class Track(Media):
    def __init__(
        self,
        client: Client,
        meta: TrackMetadata,
        config: Config,
        db: Database,
        progress: ProgressReporter,  # ⬅️ INJECTED
    ):
        self.progress = progress
        # ...

    async def download(self):
        # Instead of: from ..progress import get_progress_callback
        # Use: self.progress.get_callback(...)
        with self.progress.get_callback(total, desc) as callback:
            await downloadable.download(path, callback)
```

**Benefits:**
- ✅ Testable in isolation
- ✅ Can inject mock progress for tests
- ✅ No global state
- ✅ Can run multiple Main instances
- ✅ Clear dependency graph

**Files to Update:**
1. `streamrip/progress.py` - Implement new design
2. `streamrip/rip/main.py` - Accept progress in __init__
3. `streamrip/media/track.py` - Accept progress in __init__
4. `streamrip/media/album.py` - Pass progress to tracks
5. `streamrip/media/playlist.py` - Pass progress to tracks
6. All test files - Use NoOpProgressReporter

---

### 4.2 Dependency Injection for Global Semaphore

**Objective:** Eliminate global `_global_semaphore`

**Current Implementation:**
```python
# streamrip/media/semaphore.py - CURRENT
_global_semaphore: None | tuple[int, asyncio.Semaphore] = None

def global_download_semaphore(c: DownloadsConfig):
    global _global_semaphore
    # ... creates global semaphore
    assert max_connections == _global_semaphore[0]  # ❌ ASSERTION
    return _global_semaphore[1]
```

**Refactored Implementation:**

```python
# streamrip/concurrency.py - NEW FILE (rename from semaphore.py)

from __future__ import annotations

import asyncio
from contextlib import AbstractAsyncContextManager, nullcontext
from dataclasses import dataclass


@dataclass(frozen=True)
class ConcurrencyConfig:
    """Configuration for download concurrency."""
    enabled: bool
    max_connections: int

    @classmethod
    def from_downloads_config(cls, config: DownloadsConfig) -> ConcurrencyConfig:
        return cls(
            enabled=config.concurrency,
            max_connections=config.max_connections,
        )


class ConcurrencyLimiter:
    """Manages concurrency limits for downloads."""

    def __init__(self, config: ConcurrencyConfig):
        self.config = config
        self._semaphore: asyncio.Semaphore | None = None

    def acquire(self) -> AbstractAsyncContextManager:
        """Get a context manager for acquiring the semaphore."""
        if not self.config.enabled or self.config.max_connections < 0:
            return nullcontext()

        if self.config.max_connections == 0:
            raise ValueError("max_connections cannot be 0")

        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.config.max_connections)

        return self._semaphore

    @property
    def max_concurrent(self) -> int | None:
        """Maximum concurrent downloads, or None if unlimited."""
        if not self.config.enabled or self.config.max_connections < 0:
            return None
        return self.config.max_connections
```

**Migration:**

```python
# streamrip/rip/main.py - UPDATED
from ..concurrency import ConcurrencyConfig, ConcurrencyLimiter

class Main:
    def __init__(
        self,
        config: Config,
        progress: ProgressReporter | None = None,
        limiter: ConcurrencyLimiter | None = None,
    ):
        self.config = config
        self.progress = progress or create_progress_reporter(...)
        self.limiter = limiter or ConcurrencyLimiter(
            ConcurrencyConfig.from_downloads_config(config.session.downloads)
        )
        # ...

    async def rip(self):
        for media in self.media:
            async with self.limiter.acquire():
                await media.rip()


# streamrip/media/album.py - UPDATED
class Album(Media):
    def __init__(
        self,
        # ... other params
        limiter: ConcurrencyLimiter,
    ):
        self.limiter = limiter

    async def download(self):
        # Pass limiter to tracks
        tracks = [
            Track(..., limiter=self.limiter)
            for track_meta in self.meta.tracks
        ]

        async with self.limiter.acquire():
            await asyncio.gather(*[track.rip() for track in tracks])
```

**Benefits:**
- ✅ No global state or assertions
- ✅ Clear ownership and lifecycle
- ✅ Can inject different limiters for testing
- ✅ Immutable configuration
- ✅ Type-safe

---

### 4.3 Fix Async/Await Correctness

**Objective:** Replace blocking `requests` with `aiohttp`

**Current Problem:**
```python
# client/downloadable.py:40 - CURRENT
async def fast_async_download(path, url, headers, callback):
    with requests.get(url, stream=True) as resp:  # ❌ BLOCKING
        for chunk in resp.iter_content(chunk_size=chunk_size):
            file.write(chunk)  # ❌ BLOCKING I/O
```

**Refactored Implementation:**

```python
# client/downloadable.py - REFACTORED

async def async_download(
    path: str,
    url: str,
    headers: dict[str, str],
    session: aiohttp.ClientSession,
    callback: Callable[[int], None],
    chunk_size: int = 2**17,  # 131 KB
) -> None:
    """Download file using async I/O.

    Args:
        path: Destination file path
        url: URL to download from
        headers: HTTP headers
        session: aiohttp session
        callback: Called with bytes downloaded
        chunk_size: Size of chunks to download (default 128KB)

    Raises:
        DownloadError: If download fails
    """
    try:
        async with session.get(url, headers=headers) as resp:
            resp.raise_for_status()

            async with aiofiles.open(path, "wb") as file:
                async for chunk in resp.content.iter_chunked(chunk_size):
                    await file.write(chunk)
                    callback(len(chunk))

    except aiohttp.ClientError as e:
        raise DownloadError(f"Failed to download {url}: {e}") from e
    except IOError as e:
        raise DownloadError(f"Failed to write to {path}: {e}") from e


class BasicDownloadable(Downloadable):
    async def _download(self, path: str, callback: Callable[[int], None]):
        """Download using pure async implementation."""
        await async_download(
            path=path,
            url=self.url,
            headers=self.session.headers,
            session=self.session,
            callback=callback,
            chunk_size=2**17,  # Tuned for performance
        )
```

**Performance Benchmarking:**

Before replacing, create benchmarks:

```python
# tests/benchmark_download.py - NEW FILE
import asyncio
import time
import aiohttp
import requests
from streamrip.client.downloadable import async_download

async def benchmark_aiohttp(url: str, chunk_size: int):
    """Benchmark aiohttp download."""
    start = time.time()
    async with aiohttp.ClientSession() as session:
        await async_download("/tmp/test.dat", url, {}, session, lambda _: None, chunk_size)
    return time.time() - start

async def benchmark_requests_sync(url: str, chunk_size: int):
    """Benchmark requests (sync) download."""
    start = time.time()
    with requests.get(url, stream=True) as resp:
        with open("/tmp/test2.dat", "wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                f.write(chunk)
    return time.time() - start

# Run with different chunk sizes: 2**10, 2**14, 2**17, 2**20
# Compare download speeds for large files (100MB+)
```

**Migration Tasks:**
1. Create benchmark suite
2. Test different chunk sizes (128KB - 1MB)
3. Implement async_download()
4. Replace fast_async_download() calls
5. Remove requests dependency from downloadable.py
6. Verify performance matches or exceeds original

**Files to Update:**
- `client/downloadable.py` - Implement async_download
- `pyproject.toml` - Move requests to optional deps or remove

---

## 5. Phase 3: Client Layer Refactoring

**Duration:** 2-3 weeks
**Risk Level:** Medium
**Breaking Changes:** Internal only

### 5.1 Client Configuration Decoupling

**Objective:** Clients should only receive config they need

**Current Problem:**
```python
# client/qobuz.py - CURRENT
class QobuzClient(Client):
    def __init__(self, config: Config):
        self.global_config = config  # ❌ Entire config tree
        # Later:
        self.session = config.session.qobuz
        verify_ssl = config.session.downloads.verify_ssl
```

**Refactored Implementation:**

```python
# client/client.py - ADD CONFIG PROTOCOLS

from typing import Protocol

class ClientSessionConfig(Protocol):
    """Config required by all clients."""
    verify_ssl: bool
    max_connections: int


class QobuzSessionConfig(Protocol):
    """Config specific to Qobuz client."""
    use_auth_token: bool
    email_or_userid: str
    password_or_token: str
    app_id: str
    quality: int
    download_booklets: bool
    secrets: list[str]


# client/qobuz.py - REFACTORED
class QobuzClient(Client):
    def __init__(
        self,
        session_config: QobuzSessionConfig,
        client_config: ClientSessionConfig,
    ):
        self.session_config = session_config
        self.client_config = client_config
        # Only has access to what it needs
```

**Benefits:**
- ✅ Testable with minimal config
- ✅ Clear dependencies
- ✅ Config changes don't ripple
- ✅ Follows Interface Segregation Principle

**Files to Update:**
- `client/client.py` - Add config protocols
- `client/qobuz.py` - Use specific configs
- `client/tidal.py` - Use specific configs
- `client/deezer.py` - Use specific configs
- `client/soundcloud.py` - Use specific configs
- `rip/main.py` - Pass specific config sections

---

### 5.2 Client Factory Pattern

**Objective:** Centralize client creation logic

**Implementation:**

```python
# client/factory.py - NEW FILE

from __future__ import annotations

from typing import Protocol

from ..config import Config
from .client import Client
from .qobuz import QobuzClient
from .tidal import TidalClient
from .deezer import DeezerClient
from .soundcloud import SoundcloudClient


class ClientFactory:
    """Factory for creating authenticated clients."""

    def __init__(self, config: Config):
        self.config = config
        self._clients: dict[str, Client] = {}

    def create(self, source: str) -> Client:
        """Create or retrieve a client for the given source.

        Args:
            source: One of "qobuz", "tidal", "deezer", "soundcloud"

        Returns:
            Client instance for the source

        Raises:
            ValueError: If source is unknown
        """
        if source in self._clients:
            return self._clients[source]

        if source == "qobuz":
            client = QobuzClient(
                session_config=self.config.session.qobuz,
                client_config=self.config.session.downloads,
            )
        elif source == "tidal":
            client = TidalClient(
                session_config=self.config.session.tidal,
                client_config=self.config.session.downloads,
            )
        elif source == "deezer":
            client = DeezerClient(
                session_config=self.config.session.deezer,
                client_config=self.config.session.downloads,
            )
        elif source == "soundcloud":
            client = SoundcloudClient(
                session_config=self.config.session.soundcloud,
                client_config=self.config.session.downloads,
            )
        else:
            raise ValueError(f"Unknown source: {source}")

        self._clients[source] = client
        return client

    def get_available_sources(self) -> list[str]:
        """Return list of available sources."""
        return ["qobuz", "tidal", "deezer", "soundcloud"]
```

**Usage:**

```python
# rip/main.py - UPDATED
class Main:
    def __init__(self, config: Config, ...):
        self.client_factory = ClientFactory(config)

    async def get_logged_in_client(self, source: str) -> Client:
        client = self.client_factory.create(source)
        if not client.logged_in:
            # ... login logic
        return client
```

---

### 5.3 Downloadable Refactoring

**Objective:** Break down large downloadable.py file

**Current Structure:**
```
client/downloadable.py (434 lines)
├── fast_async_download() - helper
├── Downloadable - abstract base
├── BasicDownloadable
├── EncryptedDownloadable
├── DeezerDownloadable
├── HLSDownloadable
└── ... various helpers
```

**Refactored Structure:**

```
client/download/
├── __init__.py
├── base.py              # Downloadable ABC
├── basic.py             # BasicDownloadable
├── encrypted.py         # EncryptedDownloadable, DeezerDownloadable
├── hls.py               # HLSDownloadable
├── helpers.py           # Shared utilities
└── crypto.py            # Decryption logic
```

**Implementation:**

```python
# client/download/base.py - NEW FILE
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Callable

import aiohttp


@dataclass(frozen=True)
class DownloadInfo:
    """Information about a downloadable resource."""
    url: str
    extension: str
    source: str
    size: int | None = None


class Downloadable(abc.ABC):
    """Abstract base for downloadable media."""

    def __init__(self, session: aiohttp.ClientSession, info: DownloadInfo):
        self.session = session
        self.info = info

    @abc.abstractmethod
    async def download(self, path: str, callback: Callable[[int], None]) -> None:
        """Download the media to the given path.

        Args:
            path: Destination file path
            callback: Called with bytes downloaded

        Raises:
            DownloadError: If download fails
        """
        raise NotImplementedError

    async def get_size(self) -> int:
        """Get the size of the downloadable in bytes."""
        if self.info.size is not None:
            return self.info.size

        async with self.session.head(self.info.url) as response:
            response.raise_for_status()
            content_length = response.headers.get("Content-Length", 0)
            return int(content_length)


# client/download/basic.py - NEW FILE
from .base import Downloadable, DownloadInfo
from .helpers import async_download


class BasicDownloadable(Downloadable):
    """Simple HTTP download."""

    async def download(self, path: str, callback: Callable[[int], None]) -> None:
        await async_download(
            path=path,
            url=self.info.url,
            headers=dict(self.session.headers),
            session=self.session,
            callback=callback,
        )
```

---

## 6. Phase 4: Media Layer Refactoring

**Duration:** 2 weeks
**Risk Level:** Low
**Breaking Changes:** None

### 6.1 Media Factory Pattern

**Objective:** Centralize media object creation

**Implementation:**

```python
# media/factory.py - NEW FILE

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Client
    from ..config import Config
    from ..db import Database
    from ..progress import ProgressReporter
    from ..concurrency import ConcurrencyLimiter
    from .media import Media, Pending

from .album import Album, PendingAlbum
from .track import Track, PendingSingle
from .playlist import Playlist, PendingPlaylist
from .artist import Artist, PendingArtist
from .label import Label, PendingLabel


class MediaFactory:
    """Factory for creating media objects."""

    def __init__(
        self,
        config: Config,
        db: Database,
        progress: ProgressReporter,
        limiter: ConcurrencyLimiter,
    ):
        self.config = config
        self.db = db
        self.progress = progress
        self.limiter = limiter

    def create_pending(
        self,
        media_type: str,
        id: str,
        client: Client,
    ) -> Pending:
        """Create a pending media object.

        Args:
            media_type: Type of media (track, album, playlist, artist, label)
            id: Media ID
            client: Client to fetch metadata from

        Returns:
            Pending media object

        Raises:
            ValueError: If media_type is unknown
        """
        pending_classes = {
            "track": PendingSingle,
            "album": PendingAlbum,
            "playlist": PendingPlaylist,
            "artist": PendingArtist,
            "label": PendingLabel,
        }

        pending_class = pending_classes.get(media_type)
        if pending_class is None:
            raise ValueError(f"Unknown media type: {media_type}")

        return pending_class(
            id=id,
            client=client,
            config=self.config,
            db=self.db,
        )

    def create_track(self, client: Client, meta: TrackMetadata) -> Track:
        """Create a Track instance with injected dependencies."""
        return Track(
            client=client,
            meta=meta,
            config=self.config,
            db=self.db,
            progress=self.progress,
            limiter=self.limiter,
        )

    def create_album(self, client: Client, meta: AlbumMetadata) -> Album:
        """Create an Album instance with injected dependencies."""
        return Album(
            client=client,
            meta=meta,
            config=self.config,
            db=self.db,
            progress=self.progress,
            limiter=self.limiter,
            track_factory=self.create_track,
        )

    # ... similar methods for playlist, artist, label
```

---

### 6.2 Decompose Large Media Files

**Objective:** Break down album.py and playlist.py

**Current:**
```
media/album.py (520 lines)
├── AlbumMetadata
├── Album (main class)
├── PendingAlbum
└── Various helpers
```

**Refactored:**
```
media/
├── album/
│   ├── __init__.py
│   ├── metadata.py      # AlbumMetadata
│   ├── album.py         # Album class
│   ├── pending.py       # PendingAlbum
│   └── downloader.py    # Concurrent download logic
├── track/
│   ├── metadata.py
│   ├── track.py
│   └── pending.py
└── ...
```

---

## 7. Phase 5: Configuration & Dependency Injection

**Duration:** 1-2 weeks
**Risk Level:** Low
**Breaking Changes:** None (config file format unchanged)

### 7.1 Config Schema Separation

**Objective:** Separate schema from loading logic

**Current:**
```
config.py (476 lines)
├── Dataclass definitions
├── TOML loading
├── Version migration
└── Validation
```

**Refactored:**
```
config/
├── __init__.py
├── schema.py            # Dataclass definitions
├── loader.py            # TOML loading and validation
├── migration.py         # Version migration logic
└── defaults.py          # Default values
```

---

### 7.2 Immutable Configuration

**Objective:** Make config objects immutable

**Implementation:**

```python
# config/schema.py
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)  # ⬅️ frozen=True
class QobuzConfig:
    use_auth_token: bool
    email_or_userid: str
    password_or_token: str
    app_id: str
    quality: int
    download_booklets: bool
    secrets: tuple[str, ...]  # ⬅️ tuple instead of list
```

**Benefits:**
- ✅ Cannot be accidentally modified
- ✅ Can be safely shared across threads
- ✅ Easier to reason about
- ✅ Hashable (can be used as dict keys)

---

## 8. Phase 6: Testing & Quality Assurance

**Duration:** 2-3 weeks
**Risk Level:** Low
**Breaking Changes:** None

### 8.1 Integration Tests

**Objective:** Add end-to-end integration tests

**Test Scenarios:**

```python
# tests/integration/test_download_flow.py - NEW FILE

class TestDownloadFlow:
    """Integration tests for complete download flows."""

    async def test_single_track_download(self, tmp_path, mock_api):
        """Test downloading a single track end-to-end."""
        # Setup
        config = Config.defaults()
        main = Main(config)

        # Execute
        await main.add("https://qobuz.com/track/12345")
        await main.resolve()
        await main.rip()

        # Verify
        assert (tmp_path / "Artist" / "Album" / "01 Track.flac").exists()

    async def test_album_download_with_artwork(self, tmp_path, mock_api):
        """Test album download includes cover art."""
        # ...

    async def test_error_recovery_network_failure(self, tmp_path, mock_api):
        """Test recovery from network errors."""
        # Simulate network failure during download
        # Verify retry logic works
        # ...

    async def test_concurrent_downloads(self, tmp_path, mock_api):
        """Test multiple concurrent downloads."""
        # ...
```

---

### 8.2 Property-Based Testing

**Objective:** Use Hypothesis for property-based tests

**Implementation:**

```python
# tests/test_filepath_utils.py - ADD HYPOTHESIS

from hypothesis import given, strategies as st
from streamrip.filepath_utils import sanitize_filename

@given(st.text())
def test_sanitize_filename_never_crashes(filename: str):
    """Sanitization should never crash regardless of input."""
    result = sanitize_filename(filename)
    assert isinstance(result, str)

@given(st.text(min_size=1))
def test_sanitize_filename_not_empty(filename: str):
    """Sanitization should never produce empty string from non-empty input."""
    result = sanitize_filename(filename)
    assert len(result) > 0

@given(st.text())
def test_sanitize_filename_no_path_traversal(filename: str):
    """Sanitized filenames should not contain path traversal."""
    result = sanitize_filename(filename)
    assert ".." not in result
    assert "/" not in result  # Unix
    assert "\\" not in result  # Windows
```

---

### 8.3 Performance Testing

**Objective:** Establish performance benchmarks

**Implementation:**

```python
# tests/benchmark/ - NEW DIRECTORY
# tests/benchmark/test_download_speed.py

import pytest
import time

@pytest.mark.benchmark
class TestDownloadPerformance:
    """Performance benchmarks for downloads."""

    async def test_concurrent_download_speed(self, benchmark):
        """Benchmark concurrent download throughput."""

        async def download_10_tracks():
            # Download 10 concurrent tracks
            # ...

        result = await benchmark(download_10_tracks)
        # Assert reasonable performance
        assert result.duration < 10.0  # Should take < 10s

    async def test_metadata_fetch_speed(self, benchmark):
        """Benchmark metadata fetching."""
        # ...
```

---

## 9. Phase 7: Documentation & Polish

**Duration:** 1 week
**Risk Level:** None
**Breaking Changes:** None

### 9.1 API Documentation

**Objective:** Generate comprehensive API documentation

**Tasks:**

1. **Standardize Docstrings (Google Style)**
   ```python
   def download(self, path: str, callback: Callable[[int], None]) -> None:
       """Download the media to the given path.

       This method downloads the audio file to the specified path and
       calls the callback function with the number of bytes downloaded
       for progress tracking.

       Args:
           path: Destination file path. Must be writable.
           callback: Function called with bytes downloaded after each chunk.

       Returns:
           None

       Raises:
           DownloadError: If the download fails due to network issues.
           IOError: If the destination path is not writable.

       Example:
           >>> async with aiohttp.ClientSession() as session:
           ...     dl = BasicDownloadable(session, info)
           ...     await dl.download("/tmp/song.flac", lambda n: print(n))
       """
   ```

2. **Generate Sphinx Documentation**
   ```bash
   # Install sphinx
   poetry add --dev sphinx sphinx-rtd-theme sphinx-autodoc-typehints

   # Generate docs
   cd docs
   sphinx-quickstart
   sphinx-apidoc -o source/ ../streamrip
   make html
   ```

3. **Add Architecture Diagrams**
   ```markdown
   # docs/architecture.md

   ## System Architecture

   ```mermaid
   graph TD
       A[CLI] --> B[Main]
       B --> C[ClientFactory]
       B --> D[MediaFactory]
       C --> E[QobuzClient]
       C --> F[TidalClient]
       D --> G[Album]
       D --> H[Track]
       G --> H
       H --> I[Downloadable]
   ```
   ```

---

### 9.2 Developer Guide

**Objective:** Create comprehensive developer documentation

**Contents:**

```markdown
# docs/DEVELOPER_GUIDE.md - NEW FILE

# Developer Guide

## Getting Started

### Prerequisites
- Python 3.10+
- Poetry 1.2+

### Setup
```bash
git clone https://github.com/nathom/streamrip
cd streamrip
poetry install
poetry run pytest
```

## Architecture Overview

### Component Diagram
[Diagram showing Main → Clients → Media → Downloadable]

### Key Abstractions

#### Client
Clients handle authentication and API communication for streaming services.

- **QobuzClient**: Qobuz API with app ID spoofing
- **TidalClient**: Tidal OAuth2 authentication
- **DeezerClient**: Deezer with ARL cookie auth
- **SoundcloudClient**: SoundCloud progressive web scraping

#### Media
Media objects represent downloadable content.

- **Track**: Single audio file
- **Album**: Collection of tracks with artwork
- **Playlist**: Ordered list of tracks
- **Artist**: Artist discography
- **Label**: Label catalog

#### Downloadable
Downloadable objects handle the actual file download.

- **BasicDownloadable**: Simple HTTP download
- **EncryptedDownloadable**: Download with decryption
- **HLSDownloadable**: HTTP Live Streaming

### Data Flow

1. User provides URL
2. URL parsed into ParsedURL
3. ParsedURL creates PendingMedia
4. PendingMedia resolves to Media (fetches metadata)
5. Media.rip() downloads files
6. Files are tagged and converted

## Adding a New Client

[Step-by-step guide]

## Testing

### Running Tests
```bash
poetry run pytest
```

### Writing Tests
[Guidelines]

## Contributing

[Contribution guidelines]
```

---

### 9.3 Resolve TODOs

**Objective:** Address all TODO/FIXME comments

**TODO List:**

| File | Line | TODO | Priority | Action |
|------|------|------|----------|--------|
| converter.py | 161 | Add error handling for lossy codecs | High | Implement try/catch with ConversionError |
| parse_url.py | 235 | Implement rest of URL types | Medium | Add missing URL patterns |
| deezer.py | 57 | Async integration for deezer-py | High | Open PR to deezer-py or fork |
| downloadable.py | 338 | Progress bar for HLS | Low | Implement chunk-based progress |
| filepath_utils.py | 8 | Remove workaround after pathvalidate release | Low | Wait for upstream fix |
| client/soundcloud.py | 86 | Implement pagination | Medium | Add pagination support |
| client/tidal.py | 90 | Make token refresh concurrent | Low | Use asyncio.gather |
| client/deezer.py | 118 | Use limit parameter | Low | Implement limit |
| client/deezer.py | 148 | Optimize batch ID requests | Medium | Use batch API endpoint |
| metadata/tagger.py | 177 | Verify MP4 tagging | Medium | Add integration test |
| metadata/util.py | 39 | Should quality 0 be supported? | Low | Document decision |

---

## 10. Migration Guide

### 10.1 For End Users

**Configuration File:**
- ✅ **No changes required** - Config file format remains the same
- Config version will be bumped to 3.0.0 automatically

**CLI Interface:**
- ✅ **No changes required** - All CLI commands remain the same
- Behavior is identical

**Database:**
- ✅ **No migration required** - Database schema unchanged

### 10.2 For Developers/Contributors

**Breaking Changes:**

1. **Progress is now injected**
   ```python
   # OLD
   from streamrip.progress import get_progress_callback
   callback = get_progress_callback(True, total, desc)

   # NEW
   # Progress is injected via constructor
   def __init__(self, ..., progress: ProgressReporter):
       self.progress = progress
   callback = self.progress.get_callback(total, desc)
   ```

2. **Semaphore is now injected**
   ```python
   # OLD
   from streamrip.media.semaphore import global_download_semaphore
   semaphore = global_download_semaphore(config)

   # NEW
   # Limiter is injected via constructor
   def __init__(self, ..., limiter: ConcurrencyLimiter):
       self.limiter = limiter
   async with self.limiter.acquire():
       await download()
   ```

3. **Exception hierarchy changed**
   ```python
   # OLD
   raise Exception("Failed to parse URL")

   # NEW
   raise URLParseError(url, "Invalid format")
   ```

4. **Client initialization changed**
   ```python
   # OLD
   client = QobuzClient(config)  # Full config

   # NEW
   client = QobuzClient(
       session_config=config.session.qobuz,
       client_config=config.session.downloads,
   )
   ```

---

## 11. Success Metrics

### 11.1 Code Quality Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Test Coverage | ~60% | >80% | pytest-cov |
| Type Coverage | ~40% | >95% | mypy --strict |
| Cyclomatic Complexity | Variable | <10 per function | radon cc |
| Lines per File | Up to 520 | <300 | wc -l |
| TODO Count | 13 | 0 | grep -r TODO |
| Ruff Violations | ? | 0 | ruff check |

### 11.2 Performance Metrics

| Metric | Current | Target | Test |
|--------|---------|--------|------|
| Single Track Download | Baseline | Same or better | Benchmark test |
| Concurrent Downloads (10 tracks) | Baseline | 10-20% faster | Benchmark test |
| Memory Usage | Baseline | <10% increase | Memory profiler |
| Startup Time | Baseline | No regression | CLI startup time |

### 11.3 Maintainability Metrics

| Metric | Target |
|--------|--------|
| All public APIs documented | 100% |
| All functions have type hints | 100% |
| All modules have docstrings | 100% |
| Architecture diagrams created | Yes |
| Developer guide written | Yes |

---

## 12. Risk Assessment

### 12.1 High-Risk Changes

| Change | Risk | Mitigation |
|--------|------|------------|
| Replacing requests with aiohttp | Performance regression | Extensive benchmarking before/after |
| Removing global state | Regression in functionality | Comprehensive integration tests |
| Client initialization changes | Breaks third-party code | Deprecation warnings + migration guide |

### 12.2 Medium-Risk Changes

| Change | Risk | Mitigation |
|--------|------|------------|
| Breaking up large files | Import errors | Comprehensive test suite |
| Exception hierarchy | Catching wrong exception types | Search all exception handlers |
| Config refactoring | Config loading failures | Extensive config tests |

### 12.3 Low-Risk Changes

| Change | Risk | Mitigation |
|--------|------|------------|
| Adding type hints | Type errors | mypy validation |
| Documentation | None | N/A |
| Code formatting | Minimal | Automated with black/ruff |

---

## 13. Implementation Timeline

### Overview (12-14 weeks total)

```
Phase 1: Foundation          ████░░░░░░░░░░  2-3 weeks
Phase 2: Core Architecture   ░░░░████████░░  3-4 weeks
Phase 3: Client Layer        ░░░░░░░░████░░  2-3 weeks
Phase 4: Media Layer         ░░░░░░░░░░██░░  2 weeks
Phase 5: Config & DI         ░░░░░░░░░░░██░  1-2 weeks
Phase 6: Testing & QA        ░░░░░░░░░░░░██  2-3 weeks
Phase 7: Documentation       ░░░░░░░░░░░░░█  1 week
```

### Detailed Schedule

**Weeks 1-3: Phase 1**
- Week 1: Exception hierarchy, type system setup
- Week 2: Testing infrastructure, logging improvements
- Week 3: Mypy integration, CI updates

**Weeks 4-7: Phase 2**
- Week 4: Design dependency injection system
- Week 5: Implement ProgressReporter injection
- Week 6: Implement ConcurrencyLimiter injection
- Week 7: Replace requests with aiohttp, benchmark

**Weeks 8-10: Phase 3**
- Week 8: Client config decoupling
- Week 9: Client factory pattern
- Week 10: Downloadable refactoring

**Weeks 11-12: Phase 4**
- Week 11: Media factory pattern
- Week 12: Decompose large media files

**Weeks 13-14: Phase 5**
- Week 13: Config schema separation
- Week 14: Immutable configuration

**Weeks 15-17: Phase 6**
- Week 15: Integration tests
- Week 16: Property-based testing
- Week 17: Performance testing

**Week 18: Phase 7**
- Week 18: API docs, developer guide, resolve TODOs

---

## 14. Conclusion

This refactoring plan addresses critical architectural issues in Streamrip while maintaining backward compatibility for end users. The phased approach allows for incremental progress with continuous testing and validation.

**Key Benefits:**
- ✅ Eliminates global state for better testability
- ✅ Fixes async/await correctness issues
- ✅ Improves type safety with full mypy coverage
- ✅ Decouples configuration from business logic
- ✅ Enhances maintainability through dependency injection
- ✅ Increases test coverage to >80%
- ✅ Provides comprehensive documentation

**Next Steps:**
1. Review and approve this plan
2. Create tracking issues for each phase
3. Set up project board for task management
4. Begin Phase 1 implementation
5. Regular check-ins and progress reviews

**Questions or Concerns:**
Please open an issue on GitHub or discuss in the project's communication channels.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-23
**Author:** Claude (Anthropic)
**Status:** Proposed
