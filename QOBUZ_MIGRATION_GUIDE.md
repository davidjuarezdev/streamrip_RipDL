# Qobuz Service Migration Guide - Detailed Example

**Purpose**: Complete guide for migrating Qobuz from monolithic structure to modular plugin-based architecture

**Service**: Qobuz (chosen as detailed example due to complexity)

**Status**: Planning Document

---

## Table of Contents

1. [Current Qobuz Implementation Analysis](#current-qobuz-implementation-analysis)
2. [Migration Strategy](#migration-strategy)
3. [Step-by-Step Migration](#step-by-step-migration)
4. [Complete Code Examples](#complete-code-examples)
5. [Testing Strategy](#testing-strategy)
6. [Challenges and Solutions](#challenges-and-solutions)
7. [Verification Checklist](#verification-checklist)

---

## Current Qobuz Implementation Analysis

### Code Locations (Before Migration)

```
streamrip/
├── client/
│   └── qobuz.py                    # 456 lines - ALL Qobuz code
│       ├── QobuzSpoofer            # 95 lines  - App ID extraction
│       └── QobuzClient             # 312 lines - Client implementation
├── metadata/
│   └── album.py
│       └── from_qobuz()            # Qobuz-specific metadata parsing
├── config.py
│   └── QobuzConfig                 # Qobuz configuration dataclass
└── rip/
    └── parse_url.py
        └── QOBUZ_PATTERNS          # Hardcoded URL patterns
```

### Qobuz-Specific Components

#### 1. QobuzSpoofer Class (Lines 47-142)

**Purpose**: Extracts app_id and secrets from Qobuz website JavaScript

**Key Features**:
- Scrapes `https://play.qobuz.com/login`
- Extracts bundle.js URL
- Parses JavaScript to find app_id and secrets using regex
- Returns tuple of (app_id, list of secrets)

**Dependencies**:
- `aiohttp` for HTTP requests
- `re` for regex parsing
- `base64` for decoding
- SSL configuration from `utils/ssl_utils.py`

**Complexity**: High - complex regex patterns and JavaScript parsing

#### 2. QobuzClient Class (Lines 144-456)

**Purpose**: Implements Qobuz API client

**Key Methods**:

| Method | Purpose | Complexity |
|--------|---------|------------|
| `login()` | Authenticate with email/password or token | High |
| `get_metadata()` | Fetch album/track/artist/playlist metadata | Medium |
| `get_label()` | Get label metadata with pagination | Medium |
| `search()` | Search Qobuz catalog | Low |
| `get_featured()` | Get featured albums | Low |
| `get_user_favorites()` | Get user's favorites | Low |
| `get_user_playlists()` | Get user's playlists | Low |
| `get_downloadable()` | Get download URL for track | High |
| `_request_file_url()` | Request signed download URL | High |
| `_api_request()` | Make API request with rate limiting | Low |
| `_paginate()` | Paginate search results | Medium |
| `_get_app_id_and_secrets()` | Use spoofer to get credentials | Low |
| `_test_secret()` | Test if a secret is valid | Low |
| `_get_valid_secret()` | Find working secret from list | Medium |

**Authentication Flow**:
1. Check for app_id and secrets in config
2. If missing, use QobuzSpoofer to extract them
3. Store app_id and secrets in config file
4. Login with email/password or user_id/token
5. Receive user_auth_token
6. Validate secrets by testing track download
7. Set session headers with auth tokens

**Download Flow**:
1. Generate MD5 signature from track_id, quality, timestamp, and secret
2. Request file URL from API with signature
3. Return BasicDownloadable with stream URL

**Special Features**:
- MD5 signature generation for download URLs (line 429)
- Quality mapping (1→5, 2→6, 3→7, 4→27)
- Support for booklet PDFs
- User favorites and playlists
- Featured albums
- Label browsing

#### 3. QobuzConfig (config.py)

```python
@dataclass
class QobuzConfig:
    use_auth_token: bool            # Use token vs email/password
    email_or_userid: str            # Email or user ID
    password_or_token: str          # MD5 hash of password OR token
    app_id: str                     # Qobuz app ID
    quality: int                    # 1-4 (MP3 128 to FLAC 24-bit)
    download_booklets: bool         # Download PDF booklets
    secrets: list[str]              # List of app secrets
```

#### 4. Metadata Parsing (metadata/album.py)

**`from_qobuz()` method** extracts:
- Album title, tracktotal, genre
- Release date/year
- Copyright info
- Artists (albumartist, albumcomposer)
- Label
- Description
- Disc total
- Explicit content flag
- Cover art URLs

### Dependencies

**External Libraries**:
- `aiohttp` - HTTP client
- `asyncio` - Async operations

**Internal Dependencies**:
- `streamrip.config.Config` - Configuration
- `streamrip.exceptions.*` - Custom exceptions
- `streamrip.client.Client` - Base class
- `streamrip.client.downloadable.BasicDownloadable` - Download handler
- `streamrip.utils.ssl_utils` - SSL configuration

### Code Metrics

| Metric | Value |
|--------|-------|
| Total Lines | ~456 |
| Classes | 2 (QobuzSpoofer, QobuzClient) |
| Public Methods | 9 |
| Private Methods | 6 |
| Dependencies | 8 external, 5 internal |
| Complexity | High (authentication, signing) |

---

## Migration Strategy

### Goals

1. ✅ Extract all Qobuz code to `services/qobuz/` module
2. ✅ Create QobuzPlugin for service registry
3. ✅ Maintain backward compatibility
4. ✅ Preserve all functionality
5. ✅ Improve testability
6. ✅ Clean separation of concerns

### New Structure (After Migration)

```
streamrip/services/qobuz/
├── __init__.py              # Public exports
├── plugin.py                # QobuzPlugin registration
├── client.py                # QobuzClient (from qobuz.py)
├── spoofer.py               # QobuzSpoofer (extracted)
├── config.py                # QobuzConfig
├── metadata.py              # Metadata parsing (from_qobuz)
├── constants.py             # Constants (BASE_URL, FEATURED_KEYS)
└── README.md                # Service documentation
```

### File Breakdown

| File | Lines | Purpose | Source |
|------|-------|---------|--------|
| `plugin.py` | ~80 | Service registration | New |
| `client.py` | ~320 | Client implementation | From `client/qobuz.py` |
| `spoofer.py` | ~100 | App ID/secret extraction | From `client/qobuz.py` |
| `config.py` | ~30 | Configuration | From `config.py` |
| `metadata.py` | ~80 | Metadata parsing | From `metadata/album.py` |
| `constants.py` | ~30 | Constants and enums | From `client/qobuz.py` |
| `README.md` | ~50 | Documentation | New |

**Total**: ~690 lines (original 456 + new plugin/docs)

### Migration Principles

1. **No Functional Changes**: Code behavior remains identical
2. **Self-Contained**: All Qobuz code in one directory
3. **Testable**: Each component can be tested independently
4. **Documented**: Clear documentation for each module
5. **Backward Compatible**: Old imports still work (with warnings)

---

## Step-by-Step Migration

### Phase 1: Create Directory Structure (10 minutes)

```bash
# Create service directory
mkdir -p streamrip/services/qobuz

# Create test directory
mkdir -p tests/services/qobuz

# Create files
touch streamrip/services/qobuz/__init__.py
touch streamrip/services/qobuz/plugin.py
touch streamrip/services/qobuz/client.py
touch streamrip/services/qobuz/spoofer.py
touch streamrip/services/qobuz/config.py
touch streamrip/services/qobuz/metadata.py
touch streamrip/services/qobuz/constants.py
touch streamrip/services/qobuz/README.md

# Create test files
touch tests/services/qobuz/__init__.py
touch tests/services/qobuz/test_plugin.py
touch tests/services/qobuz/test_client.py
touch tests/services/qobuz/test_spoofer.py
```

**Verification**:
```bash
tree streamrip/services/qobuz
# Should show all 8 files
```

### Phase 2: Extract Constants (15 minutes)

**Task**: Move constants to `constants.py`

```python
# streamrip/services/qobuz/constants.py
"""
Qobuz service constants.
"""

# Qobuz API base URL
QOBUZ_BASE_URL = "https://www.qobuz.com/api.json/0.2"

# Featured album categories
QOBUZ_FEATURED_KEYS = {
    "most-streamed",
    "recent-releases",
    "best-sellers",
    "press-awards",
    "ideal-discography",
    "editor-picks",
    "most-featured",
    "qobuzissims",
    "new-releases",
    "new-releases-full",
    "harmonia-mundi",
    "universal-classic",
    "universal-jazz",
    "universal-jeunesse",
    "universal-chanson",
}

# Quality to format ID mapping
QUALITY_MAP = {
    1: 5,   # MP3 320kbps
    2: 6,   # FLAC 16-bit/44.1kHz
    3: 7,   # FLAC 24-bit/96kHz
    4: 27,  # FLAC 24-bit/192kHz
}

# URL patterns for Qobuz
URL_PATTERNS = [
    r'https?://(?:www\.)?qobuz\.com',
    r'https?://(?:www\.)?open\.qobuz\.com',
    r'https?://play\.qobuz\.com',
]
```

**Test**:
```python
# tests/services/qobuz/test_constants.py
from streamrip.services.qobuz.constants import (
    QOBUZ_BASE_URL,
    QOBUZ_FEATURED_KEYS,
    QUALITY_MAP,
)

def test_quality_map():
    assert QUALITY_MAP[1] == 5
    assert QUALITY_MAP[4] == 27

def test_featured_keys():
    assert "most-streamed" in QOBUZ_FEATURED_KEYS
    assert len(QOBUZ_FEATURED_KEYS) == 15
```

### Phase 3: Extract Configuration (20 minutes)

**Task**: Move QobuzConfig to `config.py`

```python
# streamrip/services/qobuz/config.py
"""
Qobuz service configuration.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class QobuzConfig:
    """
    Configuration for Qobuz music service.

    Attributes:
        use_auth_token: If True, use user_id and token for auth.
                       If False, use email and password.
        email_or_userid: Email address (for password auth) or
                        user ID (for token auth).
        password_or_token: MD5 hash of password OR user auth token.
        app_id: Qobuz application ID (auto-fetched if empty).
        quality: Download quality (1=MP3 320, 2=FLAC 16/44.1,
                3=FLAC 24/96, 4=FLAC 24/192).
        download_booklets: Download PDF booklets when available.
        secrets: List of app secrets for signing requests
                (auto-fetched if empty).
    """

    use_auth_token: bool = False
    email_or_userid: str = ""
    password_or_token: str = ""
    app_id: str = ""
    quality: int = 3
    download_booklets: bool = True
    secrets: list[str] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.secrets is None:
            self.secrets = []

        if self.quality not in (1, 2, 3, 4):
            raise ValueError(
                f"Invalid Qobuz quality: {self.quality}. "
                f"Must be 1 (MP3), 2 (FLAC 16-bit), 3 (FLAC 24/96), "
                f"or 4 (FLAC 24/192)."
            )

    def has_credentials(self) -> bool:
        """Check if credentials are configured."""
        return bool(self.email_or_userid and self.password_or_token)

    def has_app_credentials(self) -> bool:
        """Check if app_id and secrets are configured."""
        return bool(self.app_id and self.secrets)
```

**Update main config.py**:
```python
# streamrip/config.py
# Add import at top
from streamrip.services.qobuz.config import QobuzConfig

# Keep existing QobuzConfig as deprecated alias
import warnings

# When someone uses the old import path, warn them
def __getattr__(name):
    if name == 'QobuzConfig':
        warnings.warn(
            "Importing QobuzConfig from streamrip.config is deprecated. "
            "Use 'from streamrip.services.qobuz import QobuzConfig' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return QobuzConfig
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

### Phase 4: Extract Spoofer (30 minutes)

**Task**: Move QobuzSpoofer to `spoofer.py`

See complete code in [Complete Code Examples](#complete-code-examples) section.

**Key Changes**:
- Import constants from `.constants`
- Update imports to use `streamrip.core.utils.ssl_utils`
- Add better error handling and logging
- Add type hints

### Phase 5: Extract Client (45 minutes)

**Task**: Move QobuzClient to `client.py`

See complete code in [Complete Code Examples](#complete-code-examples) section.

**Key Changes**:
- Import from local modules (`.spoofer`, `.config`, `.constants`)
- Import from `streamrip.core.client` instead of `..client`
- Import from `streamrip.core.downloadable`
- Import from `streamrip.core.exceptions`
- Update quality mapping to use `QUALITY_MAP` from constants
- Add better documentation

### Phase 6: Extract Metadata Parsing (30 minutes)

**Task**: Extract `from_qobuz()` to `metadata.py`

See complete code in [Complete Code Examples](#complete-code-examples) section.

**Changes**:
- Create standalone function for Qobuz metadata parsing
- Can be called from main metadata classes
- Self-contained in Qobuz module

### Phase 7: Create Plugin (45 minutes)

**Task**: Implement QobuzPlugin for service registry

See complete code in [Complete Code Examples](#complete-code-examples) section.

**Key Features**:
- Implements `ServicePlugin` protocol
- Provides URL pattern matching
- Creates client instances
- Registers with service registry

### Phase 8: Create Package Exports (10 minutes)

**Task**: Define public API in `__init__.py`

```python
# streamrip/services/qobuz/__init__.py
"""
Qobuz music streaming service implementation.

This module provides a complete implementation for downloading
music from Qobuz, including:

- Authentication (email/password or user_id/token)
- Metadata retrieval
- High-quality FLAC downloads (up to 24-bit/192kHz)
- Booklet PDF downloads
- User favorites and playlists
- Featured albums and search

Example:
    >>> from streamrip.services.qobuz import QobuzClient, QobuzConfig
    >>> config = QobuzConfig(
    ...     email_or_userid="user@example.com",
    ...     password_or_token="hashed_password",
    ...     quality=4  # Best quality
    ... )
    >>> client = QobuzClient(config)
    >>> await client.login()
"""

from .client import QobuzClient
from .config import QobuzConfig
from .plugin import QobuzPlugin
from .spoofer import QobuzSpoofer
from .constants import (
    QOBUZ_BASE_URL,
    QOBUZ_FEATURED_KEYS,
    QUALITY_MAP,
)

__all__ = [
    "QobuzClient",
    "QobuzConfig",
    "QobuzPlugin",
    "QobuzSpoofer",
    "QOBUZ_BASE_URL",
    "QOBUZ_FEATURED_KEYS",
    "QUALITY_MAP",
]

__version__ = "1.0.0"
```

### Phase 9: Add Backward Compatibility (20 minutes)

**Task**: Keep old import paths working

```python
# streamrip/client/qobuz.py (keep this file)
"""
DEPRECATED: Qobuz client has moved to streamrip.services.qobuz

This module is kept for backward compatibility and will be removed
in v2.0. Please update your imports:

OLD: from streamrip.client.qobuz import QobuzClient
NEW: from streamrip.services.qobuz import QobuzClient
"""
import warnings

# Import from new location
from streamrip.services.qobuz import QobuzClient, QobuzSpoofer

# Issue deprecation warning
warnings.warn(
    "Importing from streamrip.client.qobuz is deprecated. "
    "Use 'from streamrip.services.qobuz import QobuzClient' instead. "
    "This compatibility shim will be removed in v2.0.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["QobuzClient", "QobuzSpoofer"]
```

### Phase 10: Update Plugin Loader (15 minutes)

**Task**: Register Qobuz plugin in loader

```python
# streamrip/plugin_system/loader.py
def load_builtin_plugins() -> int:
    """Load built-in service plugins."""
    from streamrip.services.qobuz import QobuzPlugin
    # ... other imports

    registry = get_registry()
    loaded = 0

    # Register Qobuz
    try:
        plugin = QobuzPlugin()
        registry.register(plugin)
        loaded += 1
        logger.info("✓ Loaded Qobuz plugin")
    except Exception as e:
        logger.error(f"✗ Failed to load Qobuz plugin: {e}")

    # Register other services...

    return loaded
```

### Phase 11: Write Tests (60 minutes)

See [Testing Strategy](#testing-strategy) section for complete test suite.

### Phase 12: Documentation (30 minutes)

**Task**: Create comprehensive service documentation

```markdown
# streamrip/services/qobuz/README.md

# Qobuz Service

High-quality music streaming service with lossless FLAC audio.

## Features

- **Quality**: Up to 24-bit/192kHz FLAC
- **Authentication**: Email/password or user ID/token
- **Special Features**: Booklet PDFs, user favorites, playlists
- **Catalog**: 70+ million tracks

## Configuration

```python
QobuzConfig(
    email_or_userid="your@email.com",
    password_or_token="your_password_md5_hash",
    quality=4,  # 1=MP3, 2-4=FLAC (higher=better)
    download_booklets=True
)
```

## Quality Levels

| Level | Format | Bitrate | Bitdepth | Sample Rate |
|-------|--------|---------|----------|-------------|
| 1 | MP3 | 320 kbps | - | - |
| 2 | FLAC | ~900 kbps | 16-bit | 44.1 kHz |
| 3 | FLAC | ~2000 kbps | 24-bit | 96 kHz |
| 4 | FLAC | ~4000 kbps | 24-bit | 192 kHz |

## Authentication

Qobuz requires app credentials (app_id and secrets) which are automatically
extracted from the Qobuz website if not provided.

## Known Issues

- Free accounts cannot download tracks
- Some tracks may have geographic restrictions
- Secrets may need periodic refreshing

## Support

For issues specific to Qobuz service, check:
- [Qobuz API Documentation](https://github.com/Qobuz/api-documentation)
```

### Phase 13: Run All Tests (15 minutes)

```bash
# Run Qobuz-specific tests
pytest tests/services/qobuz/ -v

# Run all tests to ensure nothing broke
pytest

# Check coverage
coverage run -m pytest tests/services/qobuz/
coverage report
```

**Expected Results**:
- ✅ All new tests pass
- ✅ All existing tests still pass
- ✅ Coverage ≥85% for new code
- ✅ No regressions

### Phase 14: Commit Changes (10 minutes)

```bash
git add streamrip/services/qobuz/
git add tests/services/qobuz/
git add streamrip/client/qobuz.py  # Updated compatibility shim
git add streamrip/plugin_system/loader.py

git commit -m "Migrate Qobuz service to modular plugin architecture

- Extract QobuzClient to services/qobuz/client.py
- Extract QobuzSpoofer to services/qobuz/spoofer.py
- Extract QobuzConfig to services/qobuz/config.py
- Create QobuzPlugin for service registry
- Add comprehensive tests
- Maintain backward compatibility with deprecation warnings
- Add service documentation

All existing tests pass. No breaking changes."
```

---

## Complete Code Examples

### 1. spoofer.py (Complete)

```python
# streamrip/services/qobuz/spoofer.py
"""
Qobuz app credentials spoofer.

Extracts app_id and secrets from Qobuz website JavaScript bundle.
This is necessary because Qobuz rotates these credentials periodically.
"""
import base64
import logging
import re
from collections import OrderedDict
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


class QobuzSpoofer:
    """
    Spoofs Qobuz app credentials from website.

    Qobuz embeds app_id and secrets in their JavaScript bundle.
    This class extracts them by:
    1. Fetching the login page
    2. Finding the bundle.js URL
    3. Downloading bundle.js
    4. Using regex to extract credentials

    The extracted credentials are used to sign API requests.
    """

    def __init__(self, verify_ssl: bool = True):
        """
        Initialize spoofer.

        Args:
            verify_ssl: Whether to verify SSL certificates
        """
        # Regex to find seed and timezone from bundle.js
        self.seed_timezone_regex = (
            r'[a-z]\.initialSeed\("(?P<seed>[\w=]+)",window\.ut'
            r"imezone\.(?P<timezone>[a-z]+)\)"
        )

        # Regex to find info and extras
        self.info_extras_regex = (
            r'name:"\w+/(?P<timezone>{timezones})",info:"'
            r'(?P<info>[\w=]+)",extras:"(?P<extras>[\w=]+)"'
        )

        # Regex to find app_id
        self.app_id_regex = (
            r'production:{api:{appId:"(?P<app_id>\d{9})",appSecret:"(\w{32})'
        )

        self.session: Optional[aiohttp.ClientSession] = None
        self.verify_ssl = verify_ssl
        self.bundle: Optional[str] = None

    async def get_app_id_and_secrets(self) -> tuple[str, list[str]]:
        """
        Extract app_id and secrets from Qobuz website.

        Returns:
            Tuple of (app_id, list of secrets)

        Raises:
            Exception: If app_id cannot be found
            AssertionError: If bundle URL not found or session not initialized
        """
        if self.session is None:
            raise RuntimeError("Spoofer must be used as async context manager")

        logger.debug("Fetching Qobuz login page")
        async with self.session.get("https://play.qobuz.com/login") as req:
            login_page = await req.text()

        # Extract bundle.js URL from login page
        bundle_url_match = re.search(
            r'<script src="(/resources/\d+\.\d+\.\d+-[a-z]\d{3}/bundle\.js)"></script>',
            login_page,
        )

        if bundle_url_match is None:
            raise Exception("Could not find bundle.js URL in login page")

        bundle_url = bundle_url_match.group(1)
        logger.debug(f"Found bundle URL: {bundle_url}")

        # Download bundle.js
        async with self.session.get("https://play.qobuz.com" + bundle_url) as req:
            self.bundle = await req.text()

        logger.debug(f"Downloaded bundle.js ({len(self.bundle)} bytes)")

        # Extract app_id
        app_id = self._extract_app_id()
        logger.info(f"Extracted app_id: {app_id}")

        # Extract secrets
        secrets = self._extract_secrets()
        logger.info(f"Extracted {len(secrets)} secrets")

        return app_id, secrets

    def _extract_app_id(self) -> str:
        """
        Extract app_id from bundle.

        Returns:
            App ID string

        Raises:
            Exception: If app_id not found
        """
        if self.bundle is None:
            raise RuntimeError("Bundle not loaded")

        match = re.search(self.app_id_regex, self.bundle)
        if match is None:
            raise Exception("Could not find app_id in bundle.js")

        return str(match.group("app_id"))

    def _extract_secrets(self) -> list[str]:
        """
        Extract secrets from bundle.

        The secrets are encoded in multiple parts (seed, info, extras)
        that must be combined and base64-decoded.

        Returns:
            List of secret strings

        Raises:
            RuntimeError: If bundle not loaded
        """
        if self.bundle is None:
            raise RuntimeError("Bundle not loaded")

        # Extract seed and timezone pairs
        seed_matches = re.finditer(self.seed_timezone_regex, self.bundle)
        secrets = OrderedDict()

        for match in seed_matches:
            seed, timezone = match.group("seed", "timezone")
            secrets[timezone] = [seed]

        """
        Qobuz uses ternary conditions that prioritize the second timezone.
        We must reorder the dict to match this behavior.
        """
        keypairs = list(secrets.items())
        if len(keypairs) >= 2:
            secrets.move_to_end(keypairs[1][0], last=False)

        # Build regex with actual timezone names
        info_extras_regex = self.info_extras_regex.format(
            timezones="|".join(timezone.capitalize() for timezone in secrets),
        )

        # Extract info and extras for each timezone
        info_extras_matches = re.finditer(info_extras_regex, self.bundle)
        for match in info_extras_matches:
            timezone, info, extras = match.group("timezone", "info", "extras")
            secrets[timezone.lower()] += [info, extras]

        # Decode secrets from base64
        for secret_pair in secrets:
            combined = "".join(secrets[secret_pair])
            # Remove last 44 characters before decoding
            decoded = base64.standard_b64decode(combined[:-44]).decode("utf-8")
            secrets[secret_pair] = decoded

        # Return as list, removing empty strings
        vals: list[str] = list(secrets.values())
        return [v for v in vals if v]

    async def __aenter__(self):
        """Async context manager entry."""
        from streamrip.core.utils.ssl_utils import get_aiohttp_connector_kwargs

        # Always use SSL verification for spoofer (security)
        connector_kwargs = get_aiohttp_connector_kwargs(verify_ssl=True)
        connector = aiohttp.TCPConnector(**connector_kwargs)

        self.session = aiohttp.ClientSession(connector=connector)
        logger.debug("QobuzSpoofer session created")
        return self

    async def __aexit__(self, *_):
        """Async context manager exit."""
        if self.session is not None:
            await self.session.close()
            logger.debug("QobuzSpoofer session closed")
        self.session = None
```

### 2. client.py (Complete - showing key parts)

```python
# streamrip/services/qobuz/client.py
"""
Qobuz API client implementation.
"""
import asyncio
import hashlib
import logging
import re
import time
from typing import Optional

import aiohttp

from streamrip.core.client import Client
from streamrip.core.downloadable import BasicDownloadable, Downloadable
from streamrip.core.exceptions import (
    AuthenticationError,
    IneligibleError,
    InvalidAppIdError,
    InvalidAppSecretError,
    MissingCredentialsError,
    NonStreamableError,
)

from .config import QobuzConfig
from .constants import QOBUZ_BASE_URL, QOBUZ_FEATURED_KEYS, QUALITY_MAP
from .spoofer import QobuzSpoofer

logger = logging.getLogger(__name__)


class QobuzClient(Client):
    """
    Client for Qobuz music streaming service.

    Qobuz provides high-quality music streaming with lossless FLAC
    audio up to 24-bit/192kHz.

    Authentication requires:
    - App credentials (app_id and secrets) - auto-fetched if not provided
    - User credentials (email/password OR user_id/token)

    Example:
        >>> config = QobuzConfig(
        ...     email_or_userid="user@example.com",
        ...     password_or_token="hashed_password",
        ...     quality=4
        ... )
        >>> client = QobuzClient(config)
        >>> await client.login()
        >>> metadata = await client.get_metadata("album_id", "album")
    """

    source = "qobuz"
    max_quality = 4

    def __init__(self, config: QobuzConfig):
        """
        Initialize Qobuz client.

        Args:
            config: Qobuz configuration object
        """
        self.config = config
        self.logged_in = False
        self.session: Optional[aiohttp.ClientSession] = None
        self.secret: Optional[str] = None

        # Create rate limiter (if rate limiting is configured)
        # Default: 60 requests per minute
        self.rate_limiter = self.get_rate_limiter(calls=60, period=60.0)

    async def login(self) -> bool:
        """
        Authenticate with Qobuz service.

        Returns:
            True if authentication successful

        Raises:
            MissingCredentialsError: If credentials not provided
            AuthenticationError: If login fails
            InvalidAppIdError: If app_id is invalid
            IneligibleError: If account is not eligible (e.g., free account)
        """
        # Create session
        self.session = await self.get_session(verify_ssl=True)

        # Check credentials
        if not self.config.has_credentials():
            raise MissingCredentialsError(
                "Qobuz requires email_or_userid and password_or_token"
            )

        if self.logged_in:
            logger.warning("Already logged in to Qobuz")
            return True

        # Get app credentials if not provided
        if not self.config.has_app_credentials():
            logger.info("App credentials not found, fetching from Qobuz website")
            self.config.app_id, self.config.secrets = await self._get_app_id_and_secrets()
            logger.info(f"Fetched app_id: {self.config.app_id}")
            # Note: Caller should save these to config file

        # Set app_id header
        self.session.headers.update({"X-App-Id": str(self.config.app_id)})

        # Build login params
        if self.config.use_auth_token:
            params = {
                "user_id": self.config.email_or_userid,
                "user_auth_token": self.config.password_or_token,
                "app_id": str(self.config.app_id),
            }
        else:
            params = {
                "email": self.config.email_or_userid,
                "password": self.config.password_or_token,
                "app_id": str(self.config.app_id),
            }

        # Login
        logger.debug(f"Logging in with params: {list(params.keys())}")
        status, resp = await self._api_request("user/login", params)

        if status == 401:
            raise AuthenticationError("Invalid Qobuz credentials")
        elif status == 400:
            raise InvalidAppIdError("Invalid Qobuz app_id")

        # Check account eligibility
        if not resp["user"]["credential"]["parameters"]:
            raise IneligibleError(
                "Free Qobuz accounts cannot download tracks. "
                "Please upgrade to a premium account."
            )

        # Set user auth token header
        user_auth_token = resp["user_auth_token"]
        self.session.headers.update({"X-User-Auth-Token": user_auth_token})

        # Find working secret
        self.secret = await self._get_valid_secret(self.config.secrets)
        logger.info("✓ Logged in to Qobuz successfully")

        self.logged_in = True
        return True

    async def get_metadata(self, item_id: str, media_type: str) -> dict:
        """
        Fetch metadata for an item.

        Args:
            item_id: Item ID (album_id, track_id, etc.)
            media_type: Type of item (album, track, artist, playlist, label)

        Returns:
            Metadata dictionary

        Raises:
            NonStreamableError: If item cannot be streamed
        """
        if media_type == "label":
            return await self.get_label(item_id)

        params = {
            "app_id": str(self.config.app_id),
            f"{media_type}_id": item_id,
            "limit": 500,
            "offset": 0,
        }

        # Add extras for certain types
        extras = {
            "artist": "albums",
            "playlist": "tracks",
            "label": "albums",
        }

        if media_type in extras:
            params["extra"] = extras[media_type]

        endpoint = f"{media_type}/get"
        status, resp = await self._api_request(endpoint, params)

        if status != 200:
            error_msg = resp.get("message", "Unknown error")
            raise NonStreamableError(f"Failed to fetch metadata: {error_msg}")

        return resp

    # ... (other methods follow similar pattern)

    async def get_downloadable(
        self,
        track_id: str,
        quality: int
    ) -> Downloadable:
        """
        Get downloadable for a track.

        Args:
            track_id: Qobuz track ID
            quality: Quality level (1-4)

        Returns:
            Downloadable object

        Raises:
            NonStreamableError: If track cannot be downloaded
            AssertionError: If not logged in or invalid quality
        """
        if not self.logged_in or self.secret is None:
            raise RuntimeError("Must login before getting downloadable")

        if not 1 <= quality <= 4:
            raise ValueError(f"Invalid quality: {quality}. Must be 1-4.")

        # Request file URL with signature
        status, resp = await self._request_file_url(track_id, quality, self.secret)

        if status != 200:
            raise NonStreamableError(f"Failed to get download URL (status {status})")

        stream_url = resp.get("url")

        if stream_url is None:
            # Check for restrictions
            restrictions = resp.get("restrictions", [])
            if restrictions:
                # Parse restriction code (CamelCase) into readable message
                code = restrictions[0].get("code", "UnknownRestriction")
                words = re.findall(r"([A-Z][a-z]+)", code)
                message = " ".join(words).lower()
                raise NonStreamableError(f"Track restricted: {message}")

            raise NonStreamableError("No download URL in response")

        # Return downloadable
        file_extension = "flac" if quality > 1 else "mp3"
        return BasicDownloadable(
            session=self.session,
            url=stream_url,
            extension=file_extension,
            source="qobuz"
        )

    async def _request_file_url(
        self,
        track_id: str,
        quality: int,
        secret: str,
    ) -> tuple[int, dict]:
        """
        Request signed file URL for track.

        Qobuz requires requests to be signed with MD5 hash of:
        track_id + quality + timestamp + secret

        Args:
            track_id: Track ID
            quality: Quality level (1-4)
            secret: App secret for signing

        Returns:
            Tuple of (status_code, response_dict)
        """
        # Map quality to format_id
        format_id = QUALITY_MAP[quality]

        # Generate signature
        unix_ts = time.time()
        sig_string = (
            f"trackgetFileUrlformat_id{format_id}intentstream"
            f"track_id{track_id}{unix_ts}{secret}"
        )
        sig_hash = hashlib.md5(sig_string.encode("utf-8")).hexdigest()

        logger.debug(f"Request signature: {sig_hash}")

        # Make request
        params = {
            "request_ts": unix_ts,
            "request_sig": sig_hash,
            "track_id": track_id,
            "format_id": format_id,
            "intent": "stream",
        }

        return await self._api_request("track/getFileUrl", params)

    async def _get_valid_secret(self, secrets: list[str]) -> str:
        """
        Find a working secret from list.

        Args:
            secrets: List of secrets to test

        Returns:
            First working secret

        Raises:
            InvalidAppSecretError: If no secrets work
        """
        async def test_secret(secret: str) -> Optional[str]:
            """Test if a secret works."""
            status, _ = await self._request_file_url("19512574", 4, secret)
            if status == 400:
                return None  # Bad secret
            if status in (200, 401):
                return secret  # Working secret
            logger.warning(f"Unexpected status {status} when testing secret")
            return None

        # Test all secrets in parallel
        results = await asyncio.gather(
            *[test_secret(secret) for secret in secrets]
        )

        working_secrets = [r for r in results if r is not None]

        if not working_secrets:
            raise InvalidAppSecretError(f"None of {len(secrets)} secrets are valid")

        logger.debug(f"Found {len(working_secrets)} working secrets")
        return working_secrets[0]

    async def _api_request(self, endpoint: str, params: dict) -> tuple[int, dict]:
        """
        Make API request to Qobuz.

        Args:
            endpoint: API endpoint (e.g., "track/get")
            params: Query parameters

        Returns:
            Tuple of (status_code, response_json)
        """
        url = f"{QOBUZ_BASE_URL}/{endpoint}"
        logger.debug(f"API request: {endpoint}")

        async with self.rate_limiter:
            async with self.session.get(url, params=params) as response:
                return response.status, await response.json()

    async def _get_app_id_and_secrets(self) -> tuple[str, list[str]]:
        """
        Use spoofer to get app credentials.

        Returns:
            Tuple of (app_id, list of secrets)
        """
        async with QobuzSpoofer(verify_ssl=True) as spoofer:
            return await spoofer.get_app_id_and_secrets()

    # ... (pagination, search, favorites methods continue)
```

### 3. plugin.py (Complete)

```python
# streamrip/services/qobuz/plugin.py
"""
Qobuz service plugin for streamrip.
"""
import re
from typing import Any, Type

from streamrip.plugin_system import ServicePlugin, PluginMetadata
from streamrip.core.client import Client

from .client import QobuzClient
from .config import QobuzConfig
from .constants import URL_PATTERNS


class QobuzPlugin:
    """
    Plugin for Qobuz music streaming service.

    Provides high-quality lossless audio downloads from Qobuz,
    including FLAC files up to 24-bit/192kHz.
    """

    def __init__(self):
        """Initialize Qobuz plugin with metadata."""
        self.metadata = PluginMetadata(
            name="qobuz",
            display_name="Qobuz",
            version="1.0.0",
            author="streamrip contributors",
            description=(
                "Download high-quality music from Qobuz. "
                "Supports FLAC up to 24-bit/192kHz, booklet PDFs, "
                "user favorites, and playlists."
            ),
            homepage="https://www.qobuz.com",
        )

    @property
    def name(self) -> str:
        """Service identifier."""
        return "qobuz"

    @property
    def display_name(self) -> str:
        """Human-readable service name."""
        return "Qobuz"

    @property
    def client_class(self) -> Type[Client]:
        """Client implementation class."""
        return QobuzClient

    @property
    def config_class(self) -> Type:
        """Configuration dataclass."""
        return QobuzConfig

    def get_url_patterns(self) -> list[str]:
        """
        Get URL patterns for Qobuz.

        Returns:
            List of regex patterns matching Qobuz URLs
        """
        return URL_PATTERNS.copy()

    def is_url_compatible(self, url: str) -> bool:
        """
        Check if URL belongs to Qobuz.

        Args:
            url: URL to check

        Returns:
            True if URL matches Qobuz patterns

        Example:
            >>> plugin = QobuzPlugin()
            >>> plugin.is_url_compatible("https://open.qobuz.com/album/123")
            True
            >>> plugin.is_url_compatible("https://tidal.com/album/456")
            False
        """
        for pattern in self.get_url_patterns():
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def create_client(self, config: Any) -> Client:
        """
        Create Qobuz client instance.

        Args:
            config: QobuzConfig instance

        Returns:
            Configured QobuzClient

        Raises:
            TypeError: If config is not QobuzConfig
        """
        if not isinstance(config, QobuzConfig):
            raise TypeError(
                f"Expected QobuzConfig, got {type(config).__name__}"
            )

        return QobuzClient(config)

    def __repr__(self) -> str:
        return f"QobuzPlugin(name={self.name}, version={self.metadata.version})"
```

---

## Testing Strategy

### Test Structure

```
tests/services/qobuz/
├── __init__.py
├── test_plugin.py           # Plugin tests
├── test_client.py           # Client tests
├── test_spoofer.py          # Spoofer tests
├── test_config.py           # Config tests
├── test_integration.py      # End-to-end tests
└── fixtures.py              # Test fixtures and mocks
```

### Test Coverage Goals

| Component | Target Coverage |
|-----------|-----------------|
| Plugin | 95% |
| Client | 85% |
| Spoofer | 80% |
| Config | 100% |
| Overall | 85%+ |

### Key Test Cases

See next section for complete test examples...

(Character limit reached - continuing in next section)
