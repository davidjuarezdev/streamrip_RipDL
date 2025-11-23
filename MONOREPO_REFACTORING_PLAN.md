# Modular Monorepo Refactoring - Implementation Plan

**Date:** 2025-11-23
**Approach:** Option 1 - Monorepo with Internal Modularity
**Goal:** Refactor streamrip into a modular architecture with clear service boundaries while maintaining a single repository

---

## Table of Contents

1. [Vision and Goals](#vision-and-goals)
2. [Target Architecture](#target-architecture)
3. [Implementation Phases](#implementation-phases)
4. [Detailed Phase Breakdown](#detailed-phase-breakdown)
5. [Plugin System Design](#plugin-system-design)
6. [Migration Strategy](#migration-strategy)
7. [Testing Strategy](#testing-strategy)
8. [Rollback Plan](#rollback-plan)
9. [Success Criteria](#success-criteria)

---

## Vision and Goals

### Primary Goals

1. **Clear Service Boundaries**: Each music service (Qobuz, Tidal, Deezer, SoundCloud) becomes a self-contained module
2. **Plugin System**: Enable external contributors to add new services without modifying core code
3. **Maintainability**: Easier to understand, test, and modify individual services
4. **Backward Compatibility**: Existing users experience no breaking changes
5. **Future Flexibility**: Make it easy to extract services to separate repos if needed later

### Non-Goals

- ❌ Splitting into multiple repositories (at this stage)
- ❌ Breaking changes to user-facing API
- ❌ Complete rewrite of existing functionality
- ❌ Adding new features (focus is refactoring only)

---

## Target Architecture

### Final Directory Structure

```
streamrip/
├── pyproject.toml
├── README.md
├── streamrip/
│   ├── __init__.py
│   │
│   ├── core/                           # Core abstractions and utilities
│   │   ├── __init__.py
│   │   ├── client.py                   # Abstract Client base class
│   │   ├── downloadable.py             # Abstract Downloadable
│   │   ├── media.py                    # Media/Pending base classes
│   │   ├── metadata.py                 # Metadata base classes
│   │   ├── exceptions.py               # Shared exceptions
│   │   ├── config.py                   # Base config classes
│   │   └── utils/
│   │       ├── ssl_utils.py
│   │       ├── rate_limiting.py
│   │       └── http.py
│   │
│   ├── plugin_system/                  # Plugin discovery and loading
│   │   ├── __init__.py
│   │   ├── registry.py                 # ServiceRegistry class
│   │   ├── interface.py                # ServicePlugin protocol
│   │   └── loader.py                   # Plugin discovery logic
│   │
│   ├── services/                       # Built-in service implementations
│   │   ├── __init__.py
│   │   ├── qobuz/
│   │   │   ├── __init__.py
│   │   │   ├── plugin.py               # QobuzPlugin
│   │   │   ├── client.py               # QobuzClient
│   │   │   ├── downloadable.py         # QobuzDownloadable
│   │   │   ├── metadata.py             # Qobuz metadata parsing
│   │   │   ├── config.py               # QobuzConfig
│   │   │   └── utils.py                # Qobuz-specific utilities
│   │   ├── tidal/
│   │   │   ├── __init__.py
│   │   │   ├── plugin.py
│   │   │   ├── client.py
│   │   │   ├── downloadable.py
│   │   │   ├── metadata.py
│   │   │   ├── config.py
│   │   │   └── oauth.py                # Tidal OAuth handling
│   │   ├── deezer/
│   │   │   ├── __init__.py
│   │   │   ├── plugin.py
│   │   │   ├── client.py
│   │   │   ├── downloadable.py
│   │   │   ├── metadata.py
│   │   │   ├── config.py
│   │   │   └── crypto.py               # Blowfish decryption
│   │   └── soundcloud/
│   │       ├── __init__.py
│   │       ├── plugin.py
│   │       ├── client.py
│   │       ├── downloadable.py
│   │       ├── metadata.py
│   │       └── config.py
│   │
│   ├── rip/                            # Main application logic
│   │   ├── __init__.py
│   │   ├── main.py                     # Main orchestrator (updated)
│   │   └── url_parser.py               # URL parsing (refactored)
│   │
│   ├── metadata/                       # Shared metadata handling
│   │   ├── __init__.py
│   │   ├── tagger.py
│   │   └── covers.py
│   │
│   ├── converter.py                    # Audio conversion
│   ├── config.py                       # Main config (aggregates service configs)
│   └── cli.py                          # CLI interface
│
├── tests/
│   ├── core/                           # Core abstraction tests
│   ├── plugin_system/                  # Plugin system tests
│   ├── services/
│   │   ├── qobuz/
│   │   ├── tidal/
│   │   ├── deezer/
│   │   └── soundcloud/
│   └── integration/                    # End-to-end tests
│
└── docs/
    ├── architecture.md                 # Architecture documentation
    ├── plugin_development.md           # Guide for creating plugins
    └── migration_guide.md              # For contributors
```

### Key Design Principles

1. **Self-Contained Services**: Each service module contains ALL service-specific code
2. **Core Abstraction Layer**: Core defines interfaces but has no service-specific logic
3. **Plugin Registry**: Central registry manages service discovery and instantiation
4. **Backward Compatible**: Existing code continues to work during migration
5. **Gradual Migration**: Services are migrated one at a time

---

## Implementation Phases

| Phase | Duration | Focus | Risk Level |
|-------|----------|-------|------------|
| **Phase 0** | 3 days | Setup and preparation | Low |
| **Phase 1** | 1 week | Create core abstractions | Low |
| **Phase 2** | 1 week | Build plugin system | Medium |
| **Phase 3** | 1 week | Migrate SoundCloud (pilot) | Medium |
| **Phase 4** | 2 weeks | Migrate Deezer, Qobuz, Tidal | Medium |
| **Phase 5** | 1 week | Update main application | High |
| **Phase 6** | 3 days | Testing and documentation | Low |

**Total Timeline:** 6-7 weeks

---

## Detailed Phase Breakdown

### Phase 0: Setup and Preparation (3 days)

**Goal**: Set up development infrastructure and create feature branch

#### Tasks

- [ ] **Create feature branch**
  ```bash
  git checkout -b refactor/modular-monorepo
  ```

- [ ] **Create tracking issue**
  - Document refactoring goals
  - Link to this planning document
  - Set up project board for tracking

- [ ] **Set up testing infrastructure**
  - Ensure pytest is configured
  - Set up coverage reporting
  - Document current test coverage as baseline

- [ ] **Create new directory structure**
  ```bash
  mkdir -p streamrip/core
  mkdir -p streamrip/plugin_system
  mkdir -p streamrip/services/{qobuz,tidal,deezer,soundcloud}
  mkdir -p tests/{core,plugin_system,services/{qobuz,tidal,deezer,soundcloud}}
  ```

- [ ] **Backup current implementation**
  - Tag current state: `git tag pre-refactor-backup`
  - Document rollback procedure

#### Success Criteria

✅ Feature branch created and pushed
✅ Directory structure in place
✅ All existing tests still pass
✅ Baseline metrics documented (test coverage, LOC)

---

### Phase 1: Create Core Abstractions (1 week)

**Goal**: Extract all abstract base classes and shared utilities into `streamrip/core/`

#### Task 1.1: Extract Client Base Class (1 day)

**Current Location**: `streamrip/client/client.py`
**New Location**: `streamrip/core/client.py`

```python
# streamrip/core/client.py
"""
Core client abstraction that all service clients must implement.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional
import aiohttp

class Client(ABC):
    """Abstract base class for music service clients."""

    source: str
    max_quality: int
    session: Optional[aiohttp.ClientSession] = None
    logged_in: bool = False

    @abstractmethod
    async def login(self) -> bool:
        """Authenticate with the music service."""
        pass

    @abstractmethod
    async def get_metadata(self, item_id: str, media_type: str) -> dict[str, Any]:
        """Fetch metadata for an item."""
        pass

    @abstractmethod
    async def search(
        self,
        media_type: str,
        query: str,
        limit: int = 100
    ) -> dict[str, Any]:
        """Search the service."""
        pass

    @abstractmethod
    async def get_downloadable(self, item: Any, quality: int):
        """Get a Downloadable object for a track."""
        pass

    # Shared utility methods (non-abstract)
    @staticmethod
    def get_rate_limiter(calls: int, period: float):
        """Create a rate limiter for API requests."""
        from aiolimiter import AsyncLimiter
        return AsyncLimiter(calls, period)

    @staticmethod
    async def get_session(verify_ssl: bool = True) -> aiohttp.ClientSession:
        """Create an aiohttp session with proper SSL configuration."""
        from ..core.utils.ssl_utils import get_ssl_context
        connector = aiohttp.TCPConnector(
            ssl=get_ssl_context() if verify_ssl else False
        )
        return aiohttp.ClientSession(connector=connector)
```

**Steps**:
1. Create `streamrip/core/client.py`
2. Copy abstract `Client` class from `streamrip/client/client.py`
3. Keep existing `streamrip/client/client.py` as deprecated wrapper that imports from core
4. Update imports in existing services to use `from streamrip.core.client import Client`
5. Run tests to ensure nothing broke

#### Task 1.2: Extract Downloadable Base Class (1 day)

**Current Location**: `streamrip/client/downloadable.py`
**New Location**: `streamrip/core/downloadable.py`

```python
# streamrip/core/downloadable.py
"""
Core downloadable abstraction for streaming and downloading tracks.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional

class Downloadable(ABC):
    """Abstract base class for downloadable items."""

    session: Optional[Any] = None
    url: Optional[str] = None
    _size: Optional[int] = None

    @abstractmethod
    async def _download(
        self,
        path: Path,
        callback: Optional[Callable[[int, int], None]] = None
    ):
        """Service-specific download implementation."""
        pass

    async def download(
        self,
        path: Path,
        callback: Optional[Callable[[int, int], None]] = None
    ):
        """Public download interface."""
        await self._download(path, callback)

    async def size(self) -> int:
        """Get the content length (cached)."""
        if self._size is None:
            self._size = await self._get_size()
        return self._size

    @abstractmethod
    async def _get_size(self) -> int:
        """Service-specific size determination."""
        pass

class BasicDownloadable(Downloadable):
    """Direct HTTP download without decryption."""
    # Implementation...

# Keep other Downloadable subclasses here or move to service-specific modules
```

**Steps**:
1. Create `streamrip/core/downloadable.py`
2. Move abstract `Downloadable` and `BasicDownloadable`
3. Keep service-specific downloadables (Deezer, Tidal, SoundCloud) in current location for now
4. Add backward-compatible imports
5. Test

#### Task 1.3: Extract Media and Pending Base Classes (1 day)

**Current Location**: `streamrip/media/*.py`
**New Location**: `streamrip/core/media.py`

```python
# streamrip/core/media.py
"""
Core media abstraction for tracks, albums, playlists, etc.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional

class PendingBase(ABC):
    """Base class for pending (unresolved) media items."""

    id: str
    source: str
    client: Any  # Will be Client instance

    @abstractmethod
    async def resolve(self) -> "MediaBase":
        """Fetch metadata and convert to Media object."""
        pass

class MediaBase(ABC):
    """Base class for resolved media items."""

    meta: Any  # Metadata object
    source: str

    @abstractmethod
    async def preprocess(self):
        """Pre-download processing."""
        pass

    @abstractmethod
    async def download(self):
        """Download the media."""
        pass

    @abstractmethod
    async def postprocess(self):
        """Post-download processing."""
        pass

    async def rip(self):
        """Complete download flow."""
        await self.preprocess()
        await self.download()
        await self.postprocess()
```

**Steps**:
1. Create `streamrip/core/media.py`
2. Extract abstract base classes
3. Keep concrete implementations in current location
4. Add imports for backward compatibility
5. Test

#### Task 1.4: Extract Shared Utilities (2 days)

**Create `streamrip/core/utils/`**:

```python
# streamrip/core/utils/__init__.py
from .ssl_utils import get_ssl_context
from .rate_limiting import create_rate_limiter
from .http import make_request

# streamrip/core/utils/ssl_utils.py
"""SSL context utilities."""
# Move from streamrip/utils/ssl_utils.py

# streamrip/core/utils/rate_limiting.py
"""Rate limiting utilities."""
from aiolimiter import AsyncLimiter

def create_rate_limiter(calls: int, period: float) -> AsyncLimiter:
    return AsyncLimiter(calls, period)

# streamrip/core/utils/http.py
"""HTTP utilities shared across services."""
import aiohttp
from typing import Any, Optional

async def make_request(
    session: aiohttp.ClientSession,
    url: str,
    method: str = "GET",
    **kwargs
) -> Any:
    """Make HTTP request with error handling."""
    # Shared request logic
```

#### Task 1.5: Extract Exception Hierarchy (1 day)

```python
# streamrip/core/exceptions.py
"""
Core exceptions used across all services.
"""

class StreamripError(Exception):
    """Base exception for all streamrip errors."""
    pass

class AuthenticationError(StreamripError):
    """Authentication failed."""
    pass

class MissingCredentialsError(StreamripError):
    """Required credentials not provided."""
    pass

class NonStreamableError(StreamripError):
    """Content is not streamable/downloadable."""
    pass

class IneligibleError(StreamripError):
    """Account not eligible for this quality/content."""
    pass

class InvalidAppIdError(StreamripError):
    """Invalid application ID (Qobuz-specific but defined in core)."""
    pass

class InvalidAppSecretError(StreamripError):
    """Invalid application secret."""
    pass

class NetworkError(StreamripError):
    """Network-related error."""
    pass

class RateLimitError(StreamripError):
    """Rate limit exceeded."""
    pass
```

#### Phase 1 Success Criteria

✅ `streamrip/core/` contains all abstract base classes
✅ All shared utilities moved to `streamrip/core/utils/`
✅ Exception hierarchy in `streamrip/core/exceptions.py`
✅ Backward-compatible imports maintain existing code
✅ All tests pass
✅ No functionality changes, only code movement

---

### Phase 2: Build Plugin System (1 week)

**Goal**: Create plugin registry and discovery system to manage services

#### Task 2.1: Define Plugin Interface (1 day)

```python
# streamrip/plugin_system/interface.py
"""
Plugin interface that all service plugins must implement.
"""
from typing import Protocol, Type, Optional
from ..core.client import Client

class ServicePlugin(Protocol):
    """
    Protocol defining the interface for service plugins.

    All service plugins (built-in and external) must implement this interface.
    """

    @property
    def name(self) -> str:
        """
        Service identifier (e.g., 'qobuz', 'tidal').
        Must be unique across all plugins.
        """
        ...

    @property
    def display_name(self) -> str:
        """Human-readable service name (e.g., 'Qobuz', 'TIDAL')."""
        ...

    @property
    def client_class(self) -> Type[Client]:
        """Client implementation class."""
        ...

    @property
    def config_class(self) -> Type:
        """Configuration dataclass for this service."""
        ...

    def get_url_patterns(self) -> list[str]:
        """
        List of regex patterns for URL detection.

        Returns:
            List of regex patterns (e.g., [r'qobuz\.com', r'open\.qobuz\.com'])
        """
        ...

    def create_client(self, config: Any) -> Client:
        """
        Factory method to create client instance.

        Args:
            config: Service-specific configuration object

        Returns:
            Initialized client instance
        """
        ...

    def is_url_compatible(self, url: str) -> bool:
        """
        Check if URL belongs to this service.

        Args:
            url: URL to check

        Returns:
            True if URL matches this service's patterns
        """
        ...


class PluginMetadata:
    """Metadata about a plugin."""

    def __init__(
        self,
        name: str,
        display_name: str,
        version: str,
        author: Optional[str] = None,
        description: Optional[str] = None,
        homepage: Optional[str] = None,
    ):
        self.name = name
        self.display_name = display_name
        self.version = version
        self.author = author
        self.description = description
        self.homepage = homepage
```

#### Task 2.2: Create Plugin Registry (2 days)

```python
# streamrip/plugin_system/registry.py
"""
Central registry for managing service plugins.
"""
from typing import Dict, Optional, Type, List
import logging
from .interface import ServicePlugin
from ..core.client import Client

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """
    Central registry for all service plugins.

    Manages plugin registration, discovery, and retrieval.
    """

    def __init__(self):
        self._plugins: Dict[str, ServicePlugin] = {}
        self._url_pattern_cache: Optional[List[tuple[str, str]]] = None

    def register(self, plugin: ServicePlugin) -> None:
        """
        Register a service plugin.

        Args:
            plugin: Plugin instance to register

        Raises:
            ValueError: If plugin with same name already registered
        """
        if plugin.name in self._plugins:
            logger.warning(
                f"Plugin '{plugin.name}' already registered. "
                f"Replacing with new instance."
            )

        self._plugins[plugin.name] = plugin
        self._url_pattern_cache = None  # Invalidate cache

        logger.info(
            f"Registered service plugin: {plugin.display_name} "
            f"({plugin.name})"
        )

    def unregister(self, name: str) -> None:
        """Unregister a plugin by name."""
        if name in self._plugins:
            del self._plugins[name]
            self._url_pattern_cache = None
            logger.info(f"Unregistered plugin: {name}")

    def get_plugin(self, name: str) -> Optional[ServicePlugin]:
        """Get plugin by service name."""
        return self._plugins.get(name)

    def get_all_plugins(self) -> Dict[str, ServicePlugin]:
        """Get all registered plugins."""
        return self._plugins.copy()

    def detect_service_from_url(self, url: str) -> Optional[str]:
        """
        Detect which service a URL belongs to.

        Args:
            url: URL to analyze

        Returns:
            Service name if detected, None otherwise
        """
        for name, plugin in self._plugins.items():
            if plugin.is_url_compatible(url):
                return name
        return None

    def create_client(self, service_name: str, config: Any) -> Optional[Client]:
        """
        Create client instance for a service.

        Args:
            service_name: Name of service
            config: Service configuration

        Returns:
            Client instance or None if service not found
        """
        plugin = self.get_plugin(service_name)
        if plugin is None:
            logger.error(f"No plugin found for service: {service_name}")
            return None

        try:
            return plugin.create_client(config)
        except Exception as e:
            logger.error(
                f"Failed to create client for {service_name}: {e}",
                exc_info=True
            )
            return None

    def list_services(self) -> List[str]:
        """Get list of all registered service names."""
        return list(self._plugins.keys())

    def is_service_available(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._plugins


# Global registry instance
_global_registry = ServiceRegistry()


def get_registry() -> ServiceRegistry:
    """Get the global service registry."""
    return _global_registry
```

#### Task 2.3: Create Plugin Loader (2 days)

```python
# streamrip/plugin_system/loader.py
"""
Plugin discovery and loading functionality.
"""
from importlib import import_module
from importlib.metadata import entry_points
import logging
from typing import List
from .registry import get_registry
from .interface import ServicePlugin

logger = logging.getLogger(__name__)


class PluginLoader:
    """Handles discovery and loading of service plugins."""

    @staticmethod
    def load_builtin_plugins() -> int:
        """
        Load built-in service plugins.

        Returns:
            Number of plugins loaded
        """
        builtin_services = ['qobuz', 'tidal', 'deezer', 'soundcloud']
        registry = get_registry()
        loaded = 0

        for service_name in builtin_services:
            try:
                # Import service plugin module
                module = import_module(f'streamrip.services.{service_name}.plugin')

                # Get plugin instance
                plugin = getattr(module, f'{service_name.capitalize()}Plugin')()

                # Register
                registry.register(plugin)
                loaded += 1

            except ImportError as e:
                logger.warning(
                    f"Failed to load built-in plugin '{service_name}': {e}"
                )
            except AttributeError as e:
                logger.error(
                    f"Plugin '{service_name}' missing expected class: {e}"
                )

        return loaded

    @staticmethod
    def load_external_plugins() -> int:
        """
        Load external plugins via entry points.

        External plugins should define entry point in their setup.py:

        ```python
        entry_points={
            'streamrip.plugins': [
                'myservice = myservice_plugin:MyServicePlugin',
            ],
        }
        ```

        Returns:
            Number of external plugins loaded
        """
        registry = get_registry()
        loaded = 0

        try:
            # Discover plugins via entry points
            eps = entry_points(group='streamrip.plugins')

            for ep in eps:
                try:
                    # Load plugin class
                    plugin_class = ep.load()

                    # Instantiate
                    plugin = plugin_class()

                    # Register
                    registry.register(plugin)
                    loaded += 1

                    logger.info(f"Loaded external plugin: {ep.name}")

                except Exception as e:
                    logger.error(
                        f"Failed to load external plugin '{ep.name}': {e}",
                        exc_info=True
                    )

        except Exception as e:
            logger.warning(f"Error discovering external plugins: {e}")

        return loaded

    @staticmethod
    def load_all_plugins() -> tuple[int, int]:
        """
        Load all plugins (built-in and external).

        Returns:
            Tuple of (builtin_count, external_count)
        """
        builtin = PluginLoader.load_builtin_plugins()
        external = PluginLoader.load_external_plugins()

        logger.info(
            f"Loaded {builtin} built-in plugins and "
            f"{external} external plugins"
        )

        return (builtin, external)


# streamrip/plugin_system/__init__.py
"""
Plugin system for managing music service implementations.
"""
from .registry import ServiceRegistry, get_registry
from .interface import ServicePlugin, PluginMetadata
from .loader import PluginLoader

__all__ = [
    'ServiceRegistry',
    'get_registry',
    'ServicePlugin',
    'PluginMetadata',
    'PluginLoader',
]
```

#### Phase 2 Success Criteria

✅ Plugin system fully implemented
✅ `ServiceRegistry` can register and retrieve plugins
✅ `PluginLoader` can discover built-in plugins
✅ Entry point mechanism defined for external plugins
✅ Clear `ServicePlugin` protocol documented
✅ Unit tests for plugin system (90%+ coverage)

---

### Phase 3: Migrate SoundCloud (Pilot) (1 week)

**Goal**: Migrate SoundCloud service as proof-of-concept for the new structure

**Why SoundCloud First?**
- Simplest service (no complex auth like OAuth)
- Fewest dependencies
- Good test case for plugin system

#### Task 3.1: Create Service Structure (1 day)

```bash
streamrip/services/soundcloud/
├── __init__.py
├── plugin.py          # SoundcloudPlugin implementation
├── client.py          # SoundcloudClient (moved from streamrip/client/)
├── downloadable.py    # SoundcloudDownloadable
├── metadata.py        # Metadata parsing
├── config.py          # SoundcloudConfig
└── README.md          # Service-specific documentation
```

#### Task 3.2: Implement SoundCloud Plugin (2 days)

```python
# streamrip/services/soundcloud/plugin.py
"""
SoundCloud service plugin implementation.
"""
import re
from typing import Type
from streamrip.plugin_system import ServicePlugin, PluginMetadata
from streamrip.core.client import Client
from .client import SoundcloudClient
from .config import SoundcloudConfig


class SoundcloudPlugin:
    """Plugin for SoundCloud music service."""

    def __init__(self):
        self.metadata = PluginMetadata(
            name="soundcloud",
            display_name="SoundCloud",
            version="1.0.0",
            author="streamrip contributors",
            description="SoundCloud streaming service support",
            homepage="https://soundcloud.com",
        )

    @property
    def name(self) -> str:
        return "soundcloud"

    @property
    def display_name(self) -> str:
        return "SoundCloud"

    @property
    def client_class(self) -> Type[Client]:
        return SoundcloudClient

    @property
    def config_class(self) -> Type:
        return SoundcloudConfig

    def get_url_patterns(self) -> list[str]:
        return [
            r'soundcloud\.com',
            r'on\.soundcloud\.com',
            r'api\.soundcloud\.com',
        ]

    def is_url_compatible(self, url: str) -> bool:
        """Check if URL belongs to SoundCloud."""
        for pattern in self.get_url_patterns():
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def create_client(self, config: SoundcloudConfig) -> Client:
        """Create SoundCloud client instance."""
        return SoundcloudClient(config)
```

#### Task 3.3: Refactor SoundCloud Client (2 days)

**Move and refactor** `streamrip/client/soundcloud.py` → `streamrip/services/soundcloud/client.py`

```python
# streamrip/services/soundcloud/client.py
"""
SoundCloud client implementation.
"""
from streamrip.core.client import Client
from streamrip.core.exceptions import AuthenticationError, NetworkError
from .config import SoundcloudConfig
from .downloadable import SoundcloudDownloadable
# ... rest of implementation

class SoundcloudClient(Client):
    """Client for SoundCloud API."""

    source = "soundcloud"
    max_quality = 0

    def __init__(self, config: SoundcloudConfig):
        self.config = config
        # ... initialization

    # All existing methods...
```

#### Task 3.4: Move Service-Specific Code (1 day)

- Move `SoundcloudDownloadable` to `services/soundcloud/downloadable.py`
- Move metadata parsing to `services/soundcloud/metadata.py`
- Move `SoundcloudConfig` to `services/soundcloud/config.py`
- Create backward-compatible imports in old locations

#### Task 3.5: Write Tests (1 day)

```python
# tests/services/soundcloud/test_plugin.py
"""Tests for SoundCloud plugin."""

def test_soundcloud_plugin_registration():
    """Test plugin can be registered."""
    from streamrip.services.soundcloud.plugin import SoundcloudPlugin
    from streamrip.plugin_system import get_registry

    plugin = SoundcloudPlugin()
    registry = get_registry()
    registry.register(plugin)

    assert registry.is_service_available('soundcloud')
    retrieved = registry.get_plugin('soundcloud')
    assert retrieved.name == 'soundcloud'

def test_soundcloud_url_detection():
    """Test URL pattern matching."""
    from streamrip.services.soundcloud.plugin import SoundcloudPlugin

    plugin = SoundcloudPlugin()

    assert plugin.is_url_compatible('https://soundcloud.com/artist/track')
    assert plugin.is_url_compatible('https://on.soundcloud.com/xyz')
    assert not plugin.is_url_compatible('https://qobuz.com/album')

def test_soundcloud_client_creation():
    """Test client factory method."""
    from streamrip.services.soundcloud.plugin import SoundcloudPlugin
    from streamrip.services.soundcloud.config import SoundcloudConfig

    plugin = SoundcloudPlugin()
    config = SoundcloudConfig(quality=0)

    client = plugin.create_client(config)
    assert client.source == 'soundcloud'
```

#### Phase 3 Success Criteria

✅ SoundCloud fully migrated to `services/soundcloud/`
✅ Plugin registered and discoverable
✅ All SoundCloud tests pass
✅ URL detection works via plugin
✅ Client can be created via plugin factory
✅ No breaking changes to existing functionality

---

### Phase 4: Migrate Remaining Services (2 weeks)

**Goal**: Migrate Deezer, Qobuz, and Tidal using the pattern established with SoundCloud

#### Week 1: Deezer and Qobuz

**Deezer** (3 days):
- Similar to SoundCloud but with Blowfish decryption
- Move `DeezerClient`, `DeezerDownloadable`, crypto utilities
- Create `DeezerPlugin`
- Test

**Qobuz** (4 days):
- More complex: app ID spoofer, secrets management
- Move `QobuzClient`, `QobuzSpoofer`, utilities
- Create `QobuzPlugin`
- Ensure booklet download still works
- Test

#### Week 2: Tidal

**Tidal** (5 days):
- Most complex: OAuth 2.0, token refresh, MQA decryption
- Move `TidalClient`, OAuth handling, MQA decryption
- Create `TidalPlugin`
- Test token refresh mechanism
- Test video downloads
- Integration tests

#### Migration Checklist Per Service

For each service, complete:

- [ ] Create `services/<service>/` directory structure
- [ ] Implement `<Service>Plugin` class
- [ ] Move `<Service>Client` from `client/` to `services/<service>/client.py`
- [ ] Move `<Service>Downloadable` to `services/<service>/downloadable.py`
- [ ] Move metadata parsing to `services/<service>/metadata.py`
- [ ] Move config to `services/<service>/config.py`
- [ ] Move service-specific utilities
- [ ] Add backward-compatible imports in old locations
- [ ] Update internal imports to use new locations
- [ ] Write plugin registration tests
- [ ] Write URL detection tests
- [ ] Write client creation tests
- [ ] Run all existing service tests
- [ ] Update documentation

#### Phase 4 Success Criteria

✅ All four services migrated to `services/` directory
✅ All services registered as plugins
✅ All existing tests pass
✅ Code coverage maintained or improved
✅ No regression in functionality

---

### Phase 5: Update Main Application (1 week)

**Goal**: Update main orchestrator to use plugin system instead of hardcoded services

#### Task 5.1: Refactor Main Class (3 days)

```python
# streamrip/rip/main.py
"""
Main application orchestrator using plugin system.
"""
from typing import Dict, Optional
import logging
from streamrip.plugin_system import get_registry, PluginLoader
from streamrip.core.client import Client
from streamrip.config import Config

logger = logging.getLogger(__name__)


class Main:
    """Main application class."""

    def __init__(self, config: Config):
        self.config = config
        self.registry = get_registry()
        self.clients: Dict[str, Client] = {}

        # Load all plugins
        self._load_plugins()

        # Initialize clients for configured services
        self._initialize_clients()

    def _load_plugins(self):
        """Load all available plugins."""
        builtin, external = PluginLoader.load_all_plugins()
        logger.info(
            f"Loaded {builtin} built-in and {external} external service plugins"
        )

    def _initialize_clients(self):
        """Initialize clients for all configured services."""
        for service_name in self.registry.list_services():
            # Check if service is configured
            if not hasattr(self.config, service_name):
                logger.debug(f"No configuration for service: {service_name}")
                continue

            service_config = getattr(self.config, service_name)

            # Create client via plugin
            client = self.registry.create_client(service_name, service_config)

            if client:
                self.clients[service_name] = client
                logger.debug(f"Initialized client for: {service_name}")

    async def get_logged_in_client(self, source: str) -> Optional[Client]:
        """
        Get authenticated client for a service.

        Args:
            source: Service name (e.g., 'qobuz')

        Returns:
            Authenticated client or None
        """
        if source not in self.clients:
            logger.error(f"Service '{source}' not available or configured")
            return None

        client = self.clients[source]

        if not client.logged_in:
            success = await client.login()
            if not success:
                logger.error(f"Failed to authenticate with {source}")
                return None

        return client

    async def add(self, url: str):
        """
        Add item from URL.

        Args:
            url: URL to download from
        """
        # Detect service from URL
        service_name = self.registry.detect_service_from_url(url)

        if not service_name:
            raise ValueError(f"Could not detect service from URL: {url}")

        if service_name not in self.clients:
            raise ValueError(
                f"Service '{service_name}' is not installed or configured. "
                f"Available services: {', '.join(self.clients.keys())}"
            )

        logger.info(f"Detected service: {service_name}")

        # Get authenticated client
        client = await self.get_logged_in_client(service_name)

        if not client:
            raise RuntimeError(f"Failed to authenticate with {service_name}")

        # Rest of add logic...
        # (parse URL, create Pending object, etc.)
```

#### Task 5.2: Update URL Parsing (2 days)

Refactor `streamrip/rip/parse_url.py` to use plugin URL patterns instead of hardcoded regex.

```python
# streamrip/rip/url_parser.py (renamed from parse_url.py)
"""
URL parsing using plugin system.
"""
from typing import Optional, Tuple
from streamrip.plugin_system import get_registry


class URLParser:
    """Parse URLs and detect service."""

    def __init__(self):
        self.registry = get_registry()

    def parse(self, url: str) -> Optional[Tuple[str, dict]]:
        """
        Parse URL and extract service name and parameters.

        Args:
            url: URL to parse

        Returns:
            Tuple of (service_name, params) or None if no match
        """
        # Detect service
        service_name = self.registry.detect_service_from_url(url)

        if not service_name:
            return None

        # Get plugin for detailed parsing
        plugin = self.registry.get_plugin(service_name)

        # Extract parameters (media type, ID, etc.)
        # This could be delegated to plugin if needed
        params = self._extract_params(url, plugin)

        return (service_name, params)

    def _extract_params(self, url: str, plugin) -> dict:
        """Extract URL parameters."""
        # Implementation...
        pass
```

#### Task 5.3: Update Configuration (1 day)

Ensure `Config` class can handle dynamic service configs.

```python
# streamrip/config.py
"""
Main configuration that aggregates service configs.
"""
from dataclasses import dataclass
from typing import Optional
from streamrip.services.qobuz.config import QobuzConfig
from streamrip.services.tidal.config import TidalConfig
from streamrip.services.deezer.config import DeezerConfig
from streamrip.services.soundcloud.config import SoundcloudConfig


@dataclass
class Config:
    """Main application configuration."""

    # Service configs
    qobuz: Optional[QobuzConfig] = None
    tidal: Optional[TidalConfig] = None
    deezer: Optional[DeezerConfig] = None
    soundcloud: Optional[SoundcloudConfig] = None

    # Other settings...
    downloads_folder: str = "downloads"
    # ...
```

#### Phase 5 Success Criteria

✅ Main application uses plugin system
✅ Services discovered dynamically
✅ URL parsing uses plugin patterns
✅ Graceful handling of missing services
✅ All integration tests pass
✅ CLI still works as before

---

### Phase 6: Testing and Documentation (3 days)

**Goal**: Comprehensive testing and documentation of new architecture

#### Task 6.1: Integration Testing (1 day)

```python
# tests/integration/test_plugin_system.py
"""Integration tests for plugin system."""

def test_end_to_end_download():
    """Test complete download flow with plugin system."""
    # Test with each service
    # Verify plugin discovery, client creation, download

def test_missing_service_handling():
    """Test graceful handling when service not installed."""
    # Attempt to use unregistered service
    # Verify helpful error message

def test_external_plugin_loading():
    """Test loading external plugins."""
    # Mock external plugin
    # Verify it's discovered and registered
```

#### Task 6.2: Documentation (2 days)

Create comprehensive documentation:

**1. Architecture Documentation** (`docs/architecture.md`):
- Overview of modular design
- Plugin system explanation
- Directory structure guide
- Dependency diagram

**2. Plugin Development Guide** (`docs/plugin_development.md`):
- How to create custom service plugin
- Plugin interface requirements
- Example plugin implementation
- Testing guidelines
- Publishing to PyPI (for external plugins)

**3. Migration Guide** (`docs/migration_guide.md`):
- Guide for contributors updating code
- Import path changes
- Deprecation timeline
- Breaking changes (if any)

**4. Update README**:
- Mention plugin system
- Link to plugin development guide
- List available services

#### Task 6.3: Code Coverage and Quality (1 day)

- Ensure test coverage ≥ 85% for new code
- Run linting and type checking
- Fix any issues
- Update CI/CD configuration if needed

#### Phase 6 Success Criteria

✅ Test coverage ≥ 85%
✅ All integration tests pass
✅ Documentation complete and reviewed
✅ No linting or type errors
✅ CI/CD pipeline green

---

## Testing Strategy

### Unit Tests

**Core Module Tests** (`tests/core/`):
- Test abstract base classes
- Test utility functions
- Test exception hierarchy

**Plugin System Tests** (`tests/plugin_system/`):
- Test plugin registration
- Test plugin discovery
- Test service detection from URLs
- Test client factory

**Service Tests** (`tests/services/<service>/`):
- Test each service's plugin implementation
- Test client functionality
- Test downloadable implementations
- Test metadata parsing

### Integration Tests

**End-to-End Tests** (`tests/integration/`):
- Test complete download flow
- Test service switching
- Test error handling
- Test configuration loading

### Coverage Goals

- Core modules: 95%+
- Plugin system: 90%+
- Services: 80%+ (existing coverage)
- Overall: 85%+

---

## Migration Strategy

### Backward Compatibility

**During Migration**:
1. Keep old imports working via compatibility layer
2. Add deprecation warnings to old imports
3. Document new import paths

**Example**:
```python
# streamrip/client/client.py (old location)
import warnings
from streamrip.core.client import Client

warnings.warn(
    "Importing from streamrip.client.client is deprecated. "
    "Use streamrip.core.client instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ['Client']
```

**After Migration** (in future major version):
- Remove old import paths
- Update all internal code to use new paths
- Announce breaking changes

### Deprecation Timeline

- **v1.0**: New structure introduced, old imports deprecated
- **v1.1-v1.9**: Deprecation warnings in place
- **v2.0**: Remove deprecated imports (breaking change)

---

## Rollback Plan

### If Issues Arise

**Immediate Rollback**:
```bash
git revert <commit-range>
git push -f origin refactor/modular-monorepo
```

**Selective Rollback**:
- Identify problematic phase
- Revert commits from that phase only
- Keep earlier phases if stable

### Risk Mitigation

1. **Feature Branch**: All work on separate branch
2. **Incremental Merges**: Merge phases individually to main
3. **Testing Gates**: Don't proceed to next phase until tests pass
4. **Backup Tag**: Tag before each major change
5. **Canary Testing**: Test with subset of users before full release

---

## Success Criteria

### Technical Metrics

✅ All existing tests pass
✅ Test coverage ≥ 85%
✅ No performance regression (±5% tolerance)
✅ All services work as before
✅ Plugin system operational
✅ Documentation complete

### User Experience

✅ No breaking changes for end users
✅ CLI works identically
✅ Configuration format unchanged (or migrated automatically)
✅ Download quality and metadata unchanged

### Developer Experience

✅ Clearer code organization
✅ Easier to add new services
✅ Better separation of concerns
✅ Comprehensive documentation for contributors

### Maintenance

✅ Reduced coupling between services
✅ Easier to test services in isolation
✅ Clear plugin interface for external contributors
✅ Foundation for potential future extraction to separate repos

---

## Timeline Summary

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1 | Phase 0-1 | Core abstractions extracted |
| 2 | Phase 2 | Plugin system functional |
| 3 | Phase 3 | SoundCloud migrated (pilot) |
| 4 | Phase 4 (part 1) | Deezer, Qobuz migrated |
| 5 | Phase 4 (part 2) | Tidal migrated |
| 6 | Phase 5 | Main app updated |
| 7 | Phase 6 | Testing and docs complete |

**Total: 6-7 weeks**

---

## Next Steps

1. **Review this plan** with team/stakeholders
2. **Get approval** to proceed
3. **Create GitHub issue** linking to this document
4. **Set up project board** for tracking
5. **Begin Phase 0** - Setup and preparation

---

## Questions for Consideration

Before starting, please confirm:

1. **Timeline**: Is 6-7 weeks acceptable for this refactoring?
2. **Resources**: How many developers will work on this?
3. **Priority**: Can this be worked on full-time or alongside other tasks?
4. **Testing**: Do we have good test coverage currently? (If not, we should add tests first)
5. **External Plugins**: Do we want to support external plugins in v1.0 or delay to v2.0?
6. **Breaking Changes**: Are we comfortable with deprecation warnings, or must we maintain perfect backward compatibility?

---

**Document Version**: 1.0
**Status**: Awaiting Approval
**Author**: Claude (AI Assistant)
**Date**: 2025-11-23
