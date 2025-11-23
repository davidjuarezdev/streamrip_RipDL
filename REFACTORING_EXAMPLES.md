# Monorepo Refactoring - Concrete Examples

This document provides concrete code examples showing how the refactoring will work.

---

## Table of Contents

1. [Before and After Structure](#before-and-after-structure)
2. [Example: Plugin Implementation](#example-plugin-implementation)
3. [Example: Using the Plugin System](#example-using-the-plugin-system)
4. [Example: Creating a Custom Service](#example-creating-a-custom-service)
5. [Example: Migration Path](#example-migration-path)

---

## Before and After Structure

### Current Structure (Before)

```
streamrip/
├── client/
│   ├── client.py              # Abstract Client + service logic mixed
│   ├── qobuz.py               # 800+ lines
│   ├── tidal.py               # 600+ lines
│   ├── deezer.py              # 500+ lines
│   ├── soundcloud.py          # 400+ lines
│   └── downloadable.py        # All downloadables
├── metadata/
│   ├── album.py               # Has from_qobuz(), from_tidal(), etc.
│   ├── track.py               # Service-specific parsing
│   └── covers.py              # Service-specific extraction
├── rip/
│   ├── main.py                # Hardcoded services dict
│   └── parse_url.py           # Hardcoded regex patterns
└── config.py                  # All service configs in one file
```

**Problems**:
- 😞 Everything mixed together
- 😞 Can't easily add new service
- 😞 Hard to find service-specific code
- 😞 Tight coupling between services

### New Structure (After)

```
streamrip/
├── core/                           # 🎯 Pure abstractions
│   ├── client.py
│   ├── downloadable.py
│   ├── media.py
│   ├── metadata.py
│   ├── exceptions.py
│   └── utils/
│
├── plugin_system/                  # 🔌 Plugin infrastructure
│   ├── registry.py
│   ├── interface.py
│   └── loader.py
│
├── services/                       # 📦 Self-contained services
│   ├── qobuz/
│   │   ├── plugin.py               # QobuzPlugin
│   │   ├── client.py               # QobuzClient
│   │   ├── downloadable.py         # QobuzDownloadable
│   │   ├── metadata.py             # Qobuz parsing
│   │   ├── config.py               # QobuzConfig
│   │   └── utils.py                # Qobuz-specific utils
│   ├── tidal/                      # Same structure
│   ├── deezer/                     # Same structure
│   └── soundcloud/                 # Same structure
│
└── rip/
    ├── main.py                     # Uses plugin registry
    └── url_parser.py               # Uses plugin patterns
```

**Benefits**:
- ✅ Clear separation of concerns
- ✅ Each service is self-contained
- ✅ Easy to add new services
- ✅ Can be tested independently
- ✅ Future-proof for extraction

---

## Example: Plugin Implementation

### Complete SoundCloud Plugin

```python
# streamrip/services/soundcloud/plugin.py
"""
SoundCloud service plugin - demonstrates plugin interface implementation.
"""
import re
from typing import Type, Any
from streamrip.plugin_system import ServicePlugin, PluginMetadata
from streamrip.core.client import Client
from .client import SoundcloudClient
from .config import SoundcloudConfig


class SoundcloudPlugin:
    """
    Plugin for SoundCloud music service.

    This class acts as the entry point for the SoundCloud service,
    providing metadata and factory methods for creating clients.
    """

    def __init__(self):
        """Initialize plugin with metadata."""
        self.metadata = PluginMetadata(
            name="soundcloud",
            display_name="SoundCloud",
            version="1.0.0",
            author="streamrip contributors",
            description="Download tracks and playlists from SoundCloud",
            homepage="https://soundcloud.com",
        )

    @property
    def name(self) -> str:
        """Unique service identifier."""
        return "soundcloud"

    @property
    def display_name(self) -> str:
        """Human-readable service name."""
        return "SoundCloud"

    @property
    def client_class(self) -> Type[Client]:
        """Client implementation class."""
        return SoundcloudClient

    @property
    def config_class(self) -> Type:
        """Configuration dataclass."""
        return SoundcloudConfig

    def get_url_patterns(self) -> list[str]:
        """
        Regex patterns for detecting SoundCloud URLs.

        Returns:
            List of regex patterns that match SoundCloud URLs
        """
        return [
            r'https?://(?:www\.)?soundcloud\.com',
            r'https?://(?:www\.)?on\.soundcloud\.com',
            r'https?://api\.soundcloud\.com',
        ]

    def is_url_compatible(self, url: str) -> bool:
        """
        Check if a URL belongs to SoundCloud.

        Args:
            url: URL to check

        Returns:
            True if URL matches SoundCloud patterns
        """
        for pattern in self.get_url_patterns():
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def create_client(self, config: Any) -> Client:
        """
        Create SoundCloud client instance.

        Args:
            config: SoundcloudConfig instance

        Returns:
            Configured SoundcloudClient

        Raises:
            TypeError: If config is not SoundcloudConfig
        """
        if not isinstance(config, SoundcloudConfig):
            raise TypeError(
                f"Expected SoundcloudConfig, got {type(config).__name__}"
            )

        return SoundcloudClient(config)

    def __repr__(self) -> str:
        return f"SoundcloudPlugin(name={self.name}, version={self.metadata.version})"
```

### SoundCloud Config

```python
# streamrip/services/soundcloud/config.py
"""
SoundCloud service configuration.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SoundcloudConfig:
    """
    Configuration for SoundCloud service.

    Attributes:
        client_id: SoundCloud API client ID (auto-extracted if None)
        app_version: SoundCloud app version (auto-extracted if None)
        quality: Download quality (0 = best available)
    """

    client_id: Optional[str] = None
    app_version: Optional[str] = None
    quality: int = 0

    def __post_init__(self):
        """Validate configuration."""
        if self.quality not in [0]:
            raise ValueError(f"Invalid quality for SoundCloud: {self.quality}")
```

### SoundCloud Client (Simplified)

```python
# streamrip/services/soundcloud/client.py
"""
SoundCloud client implementation.
"""
import logging
from typing import Any, Optional
from streamrip.core.client import Client
from streamrip.core.exceptions import AuthenticationError
from .config import SoundcloudConfig
from .downloadable import SoundcloudDownloadable

logger = logging.getLogger(__name__)


class SoundcloudClient(Client):
    """
    Client for SoundCloud API.

    SoundCloud doesn't require traditional authentication.
    Client ID and app version are extracted from the website.
    """

    source = "soundcloud"
    max_quality = 0

    def __init__(self, config: SoundcloudConfig):
        """
        Initialize SoundCloud client.

        Args:
            config: SoundCloud configuration
        """
        self.config = config
        self.client_id = config.client_id
        self.app_version = config.app_version
        self.session = None
        self.logged_in = False

    async def login(self) -> bool:
        """
        Initialize SoundCloud client (no auth required).

        Returns:
            True if initialization successful
        """
        try:
            # Create session
            self.session = await self.get_session()

            # Extract client_id and app_version if not provided
            if not self.client_id or not self.app_version:
                await self._refresh_tokens()

            self.logged_in = True
            logger.info("SoundCloud client initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize SoundCloud client: {e}")
            return False

    async def _refresh_tokens(self):
        """Extract client_id and app_version from SoundCloud website."""
        # Implementation: scrape from soundcloud.com
        pass

    async def get_metadata(self, item_id: str, media_type: str) -> dict[str, Any]:
        """
        Fetch metadata for SoundCloud item.

        Args:
            item_id: SoundCloud item ID
            media_type: Type of item (track, playlist, etc.)

        Returns:
            Metadata dictionary
        """
        # Implementation
        pass

    async def search(
        self,
        media_type: str,
        query: str,
        limit: int = 100
    ) -> dict[str, Any]:
        """
        Search SoundCloud.

        Args:
            media_type: Type to search for
            query: Search query
            limit: Maximum results

        Returns:
            Search results
        """
        # Implementation
        pass

    async def get_downloadable(self, item: Any, quality: int) -> SoundcloudDownloadable:
        """
        Get downloadable for SoundCloud track.

        Args:
            item: Track item
            quality: Quality level (ignored for SoundCloud)

        Returns:
            SoundcloudDownloadable instance
        """
        # Implementation
        return SoundcloudDownloadable(
            session=self.session,
            url=item['download_url'],
        )
```

---

## Example: Using the Plugin System

### How Main Application Uses Plugins

```python
# streamrip/rip/main.py
"""
Main application using plugin system.
"""
from typing import Dict, Optional
import logging
from streamrip.plugin_system import get_registry, PluginLoader
from streamrip.core.client import Client
from streamrip.config import Config

logger = logging.getLogger(__name__)


class Main:
    """Main application orchestrator."""

    def __init__(self, config: Config):
        """
        Initialize application.

        Args:
            config: Application configuration
        """
        self.config = config
        self.registry = get_registry()
        self.clients: Dict[str, Client] = {}

        # Load all plugins
        self._load_plugins()

        # Initialize clients
        self._initialize_clients()

    def _load_plugins(self):
        """Load all available service plugins."""
        builtin_count, external_count = PluginLoader.load_all_plugins()

        logger.info(
            f"Loaded {builtin_count} built-in services and "
            f"{external_count} external services"
        )

        # Log available services
        services = self.registry.list_services()
        logger.debug(f"Available services: {', '.join(services)}")

    def _initialize_clients(self):
        """Initialize clients for configured services."""
        for service_name in self.registry.list_services():
            # Check if service is configured
            service_config = getattr(self.config, service_name, None)

            if service_config is None:
                logger.debug(f"Service '{service_name}' not configured, skipping")
                continue

            # Create client via plugin
            try:
                client = self.registry.create_client(service_name, service_config)

                if client:
                    self.clients[service_name] = client
                    logger.debug(f"✓ Initialized {service_name} client")

            except Exception as e:
                logger.error(
                    f"✗ Failed to initialize {service_name} client: {e}",
                    exc_info=True
                )

    async def add(self, url: str):
        """
        Add item from URL.

        Args:
            url: URL to download from

        Raises:
            ValueError: If service not detected or not available
            RuntimeError: If authentication fails
        """
        # Detect service from URL using plugin system
        service_name = self.registry.detect_service_from_url(url)

        if not service_name:
            available = ', '.join(self.registry.list_services())
            raise ValueError(
                f"Could not detect service from URL: {url}\n"
                f"Available services: {available}"
            )

        logger.info(f"Detected service: {service_name}")

        # Check if service is available
        if service_name not in self.clients:
            raise ValueError(
                f"Service '{service_name}' is not installed or configured.\n"
                f"Configured services: {', '.join(self.clients.keys())}"
            )

        # Get authenticated client
        client = await self.get_logged_in_client(service_name)

        if not client:
            raise RuntimeError(f"Failed to authenticate with {service_name}")

        # Continue with download logic...
        logger.info(f"Ready to download from {service_name}")

    async def get_logged_in_client(self, source: str) -> Optional[Client]:
        """
        Get authenticated client for a service.

        Args:
            source: Service name

        Returns:
            Authenticated client or None if authentication fails
        """
        if source not in self.clients:
            logger.error(f"Service '{source}' not available")
            return None

        client = self.clients[source]

        # Login if needed
        if not client.logged_in:
            logger.debug(f"Authenticating with {source}...")
            success = await client.login()

            if not success:
                logger.error(f"Authentication failed for {source}")
                return None

            logger.debug(f"✓ Authenticated with {source}")

        return client

    def list_available_services(self) -> list[str]:
        """
        Get list of available and configured services.

        Returns:
            List of service names
        """
        return list(self.clients.keys())
```

### Example Usage

```python
# Example: Using streamrip with plugin system

from streamrip import Main
from streamrip.config import Config

# Create config
config = Config()

# Initialize app (plugins auto-discovered)
app = Main(config)

# Check what services are available
print("Available services:", app.list_available_services())
# Output: Available services: ['qobuz', 'tidal', 'deezer', 'soundcloud']

# Add URL (service auto-detected)
await app.add("https://soundcloud.com/artist/track")
# Output: Detected service: soundcloud
#         Ready to download from soundcloud

# Download
await app.rip()
```

---

## Example: Creating a Custom Service

### Example: Creating a YouTube Music Plugin

This example shows how an external developer could create a plugin for a new service.

#### 1. Project Structure

```
streamrip-youtube-music/         # Your plugin package
├── pyproject.toml
├── README.md
├── streamrip_youtube_music/
│   ├── __init__.py
│   ├── plugin.py               # Plugin implementation
│   ├── client.py               # YouTubeMusicClient
│   ├── downloadable.py
│   ├── metadata.py
│   └── config.py
└── tests/
    └── test_plugin.py
```

#### 2. Plugin Implementation

```python
# streamrip_youtube_music/plugin.py
"""
YouTube Music plugin for streamrip.
"""
import re
from typing import Type
from streamrip.plugin_system import ServicePlugin, PluginMetadata
from streamrip.core.client import Client
from .client import YouTubeMusicClient
from .config import YouTubeMusicConfig


class YouTubeMusicPlugin:
    """Plugin for YouTube Music service."""

    def __init__(self):
        self.metadata = PluginMetadata(
            name="youtube_music",
            display_name="YouTube Music",
            version="1.0.0",
            author="Your Name",
            description="Download music from YouTube Music",
            homepage="https://music.youtube.com",
        )

    @property
    def name(self) -> str:
        return "youtube_music"

    @property
    def display_name(self) -> str:
        return "YouTube Music"

    @property
    def client_class(self) -> Type[Client]:
        return YouTubeMusicClient

    @property
    def config_class(self) -> Type:
        return YouTubeMusicConfig

    def get_url_patterns(self) -> list[str]:
        return [
            r'music\.youtube\.com',
            r'youtube\.com/playlist',
        ]

    def is_url_compatible(self, url: str) -> bool:
        for pattern in self.get_url_patterns():
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def create_client(self, config: YouTubeMusicConfig) -> Client:
        return YouTubeMusicClient(config)
```

#### 3. Client Implementation

```python
# streamrip_youtube_music/client.py
"""
YouTube Music client implementation.
"""
from streamrip.core.client import Client
from .config import YouTubeMusicConfig


class YouTubeMusicClient(Client):
    """Client for YouTube Music."""

    source = "youtube_music"
    max_quality = 2  # 0=128k, 1=256k, 2=best

    def __init__(self, config: YouTubeMusicConfig):
        self.config = config
        # Initialize using ytmusicapi library
        # ...

    async def login(self) -> bool:
        """Authenticate with YouTube Music."""
        # Implementation
        pass

    async def get_metadata(self, item_id: str, media_type: str):
        """Fetch metadata."""
        # Implementation
        pass

    async def search(self, media_type: str, query: str, limit: int = 100):
        """Search YouTube Music."""
        # Implementation
        pass

    async def get_downloadable(self, item, quality: int):
        """Get downloadable for track."""
        # Implementation
        pass
```

#### 4. Package Configuration

```toml
# pyproject.toml
[project]
name = "streamrip-youtube-music"
version = "1.0.0"
description = "YouTube Music plugin for streamrip"
dependencies = [
    "streamrip>=1.0.0",
    "ytmusicapi>=1.0.0",
]

[project.entry-points."streamrip.plugins"]
youtube_music = "streamrip_youtube_music.plugin:YouTubeMusicPlugin"
```

#### 5. Installation and Usage

```bash
# Install the plugin
pip install streamrip-youtube-music

# Now it's automatically available!
streamrip url "https://music.youtube.com/playlist?list=..."
```

**Streamrip will automatically**:
1. Discover the plugin via entry points
2. Load YouTubeMusicPlugin
3. Register it in the service registry
4. Use it when YouTube Music URLs are encountered

---

## Example: Migration Path

### Phase-by-Phase Code Changes

#### Before: Hardcoded Services

```python
# OLD: streamrip/rip/main.py
class Main:
    def __init__(self, config):
        self.config = config
        # Hardcoded service imports
        from streamrip.client.qobuz import QobuzClient
        from streamrip.client.tidal import TidalClient
        from streamrip.client.deezer import DeezerClient
        from streamrip.client.soundcloud import SoundcloudClient

        # Hardcoded service instantiation
        self.clients = {
            "qobuz": QobuzClient(config.qobuz),
            "tidal": TidalClient(config.tidal),
            "deezer": DeezerClient(config.deezer),
            "soundcloud": SoundcloudClient(config.soundcloud),
        }

    async def add(self, url: str):
        # Hardcoded URL detection
        if "qobuz.com" in url:
            source = "qobuz"
        elif "tidal.com" in url:
            source = "tidal"
        elif "deezer.com" in url:
            source = "deezer"
        elif "soundcloud.com" in url:
            source = "soundcloud"
        else:
            raise ValueError("Unknown service")

        client = self.clients[source]
        # ...
```

#### After Phase 2: Plugin System in Place

```python
# NEW: streamrip/rip/main.py
from streamrip.plugin_system import get_registry, PluginLoader

class Main:
    def __init__(self, config):
        self.config = config
        self.registry = get_registry()

        # Load plugins (discovers all registered services)
        PluginLoader.load_all_plugins()

        # Create clients dynamically
        self.clients = {}
        for service_name in self.registry.list_services():
            service_config = getattr(config, service_name, None)
            if service_config:
                client = self.registry.create_client(service_name, service_config)
                self.clients[service_name] = client

    async def add(self, url: str):
        # Dynamic URL detection via plugins
        source = self.registry.detect_service_from_url(url)

        if not source:
            raise ValueError("Unknown service")

        client = self.clients[source]
        # ...
```

#### After Phase 3: First Service Migrated

```python
# NEW: streamrip/services/soundcloud/__init__.py
"""
SoundCloud service module.

This module is self-contained and includes all SoundCloud-specific code.
"""
from .plugin import SoundcloudPlugin
from .client import SoundcloudClient
from .config import SoundcloudConfig

__all__ = ['SoundcloudPlugin', 'SoundcloudClient', 'SoundcloudConfig']
```

```python
# NEW: streamrip/plugin_system/loader.py (builtin loading)
def load_builtin_plugins():
    """Load built-in plugins."""
    registry = get_registry()

    # Import and register SoundCloud
    from streamrip.services.soundcloud import SoundcloudPlugin
    registry.register(SoundcloudPlugin())

    # Other services still in old location (for now)
    # ... will be migrated in later phases
```

#### After Phase 5: All Services Migrated

```python
# NEW: streamrip/plugin_system/loader.py (all services)
def load_builtin_plugins():
    """Load all built-in service plugins."""
    registry = get_registry()
    services = ['qobuz', 'tidal', 'deezer', 'soundcloud']

    for service in services:
        try:
            module = import_module(f'streamrip.services.{service}.plugin')
            plugin_class = getattr(module, f'{service.capitalize()}Plugin')
            registry.register(plugin_class())
        except ImportError as e:
            logger.warning(f"Failed to load {service}: {e}")

    return len(registry.list_services())
```

### Backward Compatibility Shims

```python
# OLD LOCATION: streamrip/client/soundcloud.py
"""
DEPRECATED: Import from streamrip.services.soundcloud instead.

This module will be removed in v2.0.
"""
import warnings
from streamrip.services.soundcloud.client import SoundcloudClient

warnings.warn(
    "Importing SoundcloudClient from streamrip.client.soundcloud is deprecated. "
    "Use 'from streamrip.services.soundcloud import SoundcloudClient' instead. "
    "This compatibility shim will be removed in v2.0.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ['SoundcloudClient']
```

### Testing Migration

```python
# tests/services/soundcloud/test_migration.py
"""
Tests to ensure migration doesn't break existing functionality.
"""
import pytest


def test_plugin_registered():
    """Test SoundCloud plugin is registered."""
    from streamrip.plugin_system import get_registry

    registry = get_registry()
    assert registry.is_service_available('soundcloud')


def test_url_detection():
    """Test URL detection works via plugin."""
    from streamrip.plugin_system import get_registry

    registry = get_registry()
    service = registry.detect_service_from_url('https://soundcloud.com/artist/track')

    assert service == 'soundcloud'


def test_backward_compatible_import():
    """Test old import path still works (with deprecation warning)."""
    with pytest.warns(DeprecationWarning, match="streamrip.services.soundcloud"):
        from streamrip.client.soundcloud import SoundcloudClient

    # Should still work
    assert SoundcloudClient.source == 'soundcloud'


def test_client_creation_via_plugin():
    """Test client can be created via plugin system."""
    from streamrip.plugin_system import get_registry
    from streamrip.services.soundcloud.config import SoundcloudConfig

    registry = get_registry()
    config = SoundcloudConfig(quality=0)

    client = registry.create_client('soundcloud', config)

    assert client is not None
    assert client.source == 'soundcloud'


def test_existing_functionality_preserved():
    """Test that all existing SoundCloud functionality still works."""
    from streamrip.services.soundcloud import SoundcloudClient, SoundcloudConfig

    config = SoundcloudConfig(quality=0)
    client = SoundcloudClient(config)

    # Test existing methods work
    assert client.source == 'soundcloud'
    assert client.max_quality == 0
    # ... more tests
```

---

## Summary

This refactoring provides:

✅ **Clear organization** - Each service is self-contained
✅ **Plugin system** - Easy to add new services
✅ **Backward compatibility** - Existing code keeps working
✅ **Future flexibility** - Can extract to separate repos later
✅ **Better testing** - Services can be tested in isolation
✅ **External contributions** - Community can add services via plugins

The migration is **gradual and safe**, with each phase independently testable.

---

**Next Steps**: Review this plan and examples, then proceed with Phase 0 when ready.
