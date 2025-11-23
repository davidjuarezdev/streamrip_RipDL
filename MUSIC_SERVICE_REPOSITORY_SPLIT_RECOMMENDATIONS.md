# Music Service Repository Split - Architectural Recommendations

**Date:** 2025-11-23
**Author:** Claude (AI Assistant)
**Purpose:** Evaluate and recommend strategies for splitting music service implementations into separate repositories

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Architecture Analysis](#current-architecture-analysis)
3. [Proposed Architecture Options](#proposed-architecture-options)
4. [Detailed Analysis](#detailed-analysis)
5. [Implementation Strategy](#implementation-strategy)
6. [Migration Path](#migration-path)
7. [Final Recommendations](#final-recommendations)

---

## Executive Summary

### Current State
Streamrip currently uses a **monolithic plugin architecture** where all music services (Qobuz, Tidal, Deezer, SoundCloud) are implemented as separate client classes within a single repository. Each service inherits from a common `Client` base class and implements service-specific authentication, metadata fetching, and download logic.

### Proposed Change
Split each music service into its own repository while extracting shared functionality into a core library, creating a **distributed plugin ecosystem**.

### Key Recommendation
**I recommend a HYBRID approach**: Keep the core services (Qobuz, Tidal, Deezer, SoundCloud) in the main repository for now, but architect the system to support external service plugins. This provides the benefits of modularity without the operational overhead of managing multiple repositories.

**However**, if you have specific reasons to pursue separate repositories (organizational structure, licensing, team distribution, etc.), I provide a comprehensive migration strategy below.

---

## Current Architecture Analysis

### Service Structure

```
streamrip/
├── client/
│   ├── client.py           # Abstract Client base class
│   ├── qobuz.py            # QobuzClient implementation
│   ├── tidal.py            # TidalClient implementation
│   ├── deezer.py           # DeezerClient implementation
│   ├── soundcloud.py       # SoundcloudClient implementation
│   └── downloadable.py     # Download handling abstractions
├── metadata/
│   ├── album.py            # AlbumMetadata with from_qobuz(), from_tidal(), etc.
│   ├── track.py            # TrackMetadata parsing per service
│   └── covers.py           # Cover art extraction per service
├── media/
│   ├── track.py            # Track media object
│   ├── album.py            # Album media object
│   └── pending.py          # Pending* classes for lazy metadata loading
├── rip/
│   ├── main.py             # Main orchestrator with clients dict
│   └── parse_url.py        # URL parsing for all services
└── config.py               # Service-specific config dataclasses
```

### Key Shared Dependencies

1. **Abstract Base Classes**: `Client`, `Downloadable`, `Media`, `Pending`
2. **HTTP Session Management**: `aiohttp` session with SSL config
3. **Metadata System**: Common metadata structures and tagging
4. **Configuration System**: Unified config with service sections
5. **URL Parsing**: Service detection and URL validation
6. **Error Handling**: Shared exception hierarchy
7. **Utilities**: Rate limiting, conversion, file handling, logging

### Service Coupling Points

| Component | Coupling Level | Description |
|-----------|----------------|-------------|
| **Client Interface** | High | All services must implement abstract methods |
| **Metadata Parsers** | High | Centralized parsing in `metadata/` with service-specific branches |
| **Config System** | Medium | Each service has config dataclass in main `config.py` |
| **URL Routing** | Medium | `Main.add()` routes URLs to appropriate client |
| **Downloadable** | Medium | Each service may have custom `Downloadable` subclass |
| **Quality Mapping** | Low | Service-specific quality levels are independent |

---

## Proposed Architecture Options

### Option 1: Monorepo with Internal Modularity (RECOMMENDED)

**Structure:**
```
streamrip/                          # Main repository
├── streamrip-core/                 # Core library (could be separate package)
│   ├── client.py                   # Abstract Client
│   ├── downloadable.py             # Abstract Downloadable
│   ├── media.py                    # Media/Pending base classes
│   └── metadata.py                 # Metadata base classes
├── streamrip-services/             # Services as internal modules
│   ├── qobuz/                      # Self-contained Qobuz module
│   │   ├── client.py
│   │   ├── metadata.py
│   │   ├── downloadable.py
│   │   └── config.py
│   ├── tidal/
│   ├── deezer/
│   └── soundcloud/
└── streamrip/                      # Main application
    ├── rip/main.py                 # Service registry and orchestration
    └── config.py                   # Aggregates service configs
```

**Key Features:**
- Services are self-contained modules within main repo
- Clear boundaries between services and core
- Easy to develop and test together
- Simple dependency management (single requirements.txt)
- Can later extract individual services if needed

---

### Option 2: Multi-Repository Plugin System

**Structure:**
```
streamrip-core/                     # Core library repository
├── pyproject.toml
└── streamrip_core/
    ├── client.py                   # Abstract Client
    ├── downloadable.py
    ├── media.py
    ├── metadata.py
    └── plugin_registry.py          # Plugin discovery and loading

streamrip-qobuz/                    # Qobuz service repository
├── pyproject.toml
├── streamrip_qobuz/
│   ├── client.py
│   ├── metadata.py
│   └── downloadable.py
└── setup.py                        # Entry points for plugin discovery

streamrip-tidal/                    # Tidal service repository
streamrip-deezer/                   # Deezer service repository
streamrip-soundcloud/               # SoundCloud service repository

streamrip/                          # Main application repository
├── pyproject.toml
└── streamrip/
    ├── rip/main.py
    └── config.py
```

**Key Features:**
- Complete separation of services
- Each service is independently versioned
- Plugin discovery via Python entry points
- Requires plugin registry and loader system
- More complex dependency management

---

### Option 3: Monorepo with Multiple Packages

**Structure:**
```
streamrip-monorepo/
├── packages/
│   ├── core/                       # streamrip-core package
│   ├── qobuz/                      # streamrip-qobuz package
│   ├── tidal/                      # streamrip-tidal package
│   ├── deezer/                     # streamrip-deezer package
│   └── soundcloud/                 # streamrip-soundcloud package
├── pyproject.toml                  # Workspace configuration (Poetry/PDM)
└── README.md
```

**Key Features:**
- Single repository with multiple packages
- Each package can be published independently to PyPI
- Shared tooling and CI/CD
- Easier cross-package changes
- Workspace support in modern Python tools (Poetry, PDM)

---

## Detailed Analysis

### Pros and Cons of Repository Splitting

#### ✅ PROS: Separate Repositories

1. **Independent Development Cycles**
   - Services can be released independently
   - Qobuz updates don't require Tidal testing
   - Different maintainers for different services

2. **Smaller Codebases**
   - Easier for contributors to understand
   - Faster clone/checkout times
   - Reduced cognitive load

3. **Clear Ownership**
   - Teams can own specific service repos
   - Easier to manage permissions
   - Service-specific issue tracking

4. **Licensing Flexibility**
   - Different licenses per service if needed
   - Easier to handle service-specific legal requirements

5. **Reduced Blast Radius**
   - Breaking changes in one service don't affect others
   - Security issues are isolated

6. **Specialized CI/CD**
   - Service-specific test suites
   - Different deployment strategies
   - Optimized builds per service

#### ❌ CONS: Separate Repositories

1. **Increased Coordination Overhead**
   - Changes to core interfaces require updates across multiple repos
   - Version compatibility management becomes complex
   - Need semantic versioning strategy for core library

2. **Complex Dependency Management**
   - Each service depends on `streamrip-core` version
   - Breaking changes in core affect all services
   - Requires careful API versioning and deprecation cycles

3. **Harder to Make Cross-Service Changes**
   - Refactoring shared code requires multiple PRs
   - Testing cross-repo changes is complex
   - Atomic commits across repos are impossible

4. **Duplicated Tooling**
   - Each repo needs own CI/CD configuration
   - Repeated setup for linting, testing, formatting
   - More maintenance burden

5. **Discovery and Installation Complexity**
   - Users must install multiple packages
   - Need plugin discovery mechanism
   - Harder to ensure all services work together

6. **Documentation Fragmentation**
   - Docs spread across multiple repos
   - Harder to maintain consistency
   - Users must navigate multiple sources

7. **Testing Complexity**
   - Integration tests across services harder
   - Need to test against multiple core versions
   - Mock dependencies increase

8. **Release Coordination**
   - Need release strategy for core + services
   - Compatibility matrix becomes complex
   - Users may end up with incompatible versions

---

## Implementation Strategy

### If Pursuing Multi-Repository Approach

#### Phase 1: Extract Core Library (Weeks 1-2)

**Goal**: Create `streamrip-core` package with all shared abstractions

1. **Create Core Package Structure**
   ```
   streamrip-core/
   ├── pyproject.toml
   ├── README.md
   ├── src/streamrip_core/
   │   ├── __init__.py
   │   ├── client.py              # Abstract Client
   │   ├── downloadable.py        # Abstract Downloadable
   │   ├── media.py               # Media/Pending base classes
   │   ├── metadata.py            # Metadata base classes
   │   ├── exceptions.py          # Shared exceptions
   │   ├── utils/
   │   │   ├── ssl_utils.py
   │   │   ├── rate_limiting.py
   │   │   └── aiohttp_utils.py
   │   └── plugin_system/
   │       ├── registry.py        # Plugin registration
   │       └── loader.py          # Plugin discovery
   └── tests/
   ```

2. **Define Plugin Interface**
   ```python
   # streamrip_core/plugin_system/interface.py
   from typing import Protocol

   class ServicePlugin(Protocol):
       """Interface that all service plugins must implement."""

       @property
       def name(self) -> str:
           """Service name (e.g., 'qobuz', 'tidal')."""
           ...

       @property
       def client_class(self) -> type[Client]:
           """Client implementation for this service."""
           ...

       @property
       def config_class(self) -> type:
           """Configuration dataclass for this service."""
           ...

       def get_url_patterns(self) -> list[str]:
           """Regex patterns for URL detection."""
           ...
   ```

3. **Create Plugin Registry**
   ```python
   # streamrip_core/plugin_system/registry.py
   from importlib.metadata import entry_points

   class PluginRegistry:
       def __init__(self):
           self.plugins = {}

       def discover(self):
           """Discover plugins via entry points."""
           eps = entry_points(group='streamrip.services')
           for ep in eps:
               plugin = ep.load()
               self.plugins[plugin.name] = plugin

       def get_client(self, service_name: str) -> Client:
           """Get client instance for service."""
           plugin = self.plugins[service_name]
           return plugin.client_class()
   ```

4. **Version and Publish Core**
   - Semantic versioning: Start with `0.1.0` (pre-stable)
   - Publish to PyPI: `streamrip-core`
   - Document API stability guarantees

#### Phase 2: Extract First Service (Weeks 3-4)

**Goal**: Prove the plugin system with one service (suggest SoundCloud as it's simplest)

1. **Create Service Repository**
   ```
   streamrip-soundcloud/
   ├── pyproject.toml
   ├── README.md
   ├── src/streamrip_soundcloud/
   │   ├── __init__.py
   │   ├── client.py              # SoundcloudClient
   │   ├── downloadable.py        # SoundcloudDownloadable
   │   ├── metadata.py            # Metadata parsing
   │   └── config.py              # SoundcloudConfig
   ├── tests/
   └── docs/
   ```

2. **Configure Entry Point**
   ```toml
   # pyproject.toml
   [project.entry-points."streamrip.services"]
   soundcloud = "streamrip_soundcloud:SoundCloudPlugin"
   ```

3. **Implement Plugin**
   ```python
   # streamrip_soundcloud/__init__.py
   from streamrip_core.plugin_system import ServicePlugin
   from .client import SoundcloudClient
   from .config import SoundcloudConfig

   class SoundCloudPlugin:
       name = "soundcloud"
       client_class = SoundcloudClient
       config_class = SoundcloudConfig

       def get_url_patterns(self):
           return [r'soundcloud\.com']
   ```

4. **Test Plugin Discovery**
   - Install both `streamrip-core` and `streamrip-soundcloud`
   - Verify plugin auto-discovery works
   - Test client instantiation and basic functionality

#### Phase 3: Migrate Remaining Services (Weeks 5-8)

**Goal**: Extract Qobuz, Tidal, Deezer one at a time

1. **Priority Order**:
   - SoundCloud (simplest, already done)
   - Deezer (medium complexity)
   - Qobuz (complex authentication)
   - Tidal (most complex with OAuth)

2. **For Each Service**:
   - Create repo from template
   - Copy service code
   - Update imports to use `streamrip_core`
   - Implement plugin interface
   - Write service-specific tests
   - Document installation and usage
   - Publish to PyPI

#### Phase 4: Update Main Application (Week 9)

**Goal**: Convert main app to use plugin system

1. **Update Dependencies**
   ```toml
   # pyproject.toml
   [project]
   dependencies = [
       "streamrip-core>=0.1.0,<1.0.0",
   ]

   [project.optional-dependencies]
   all-services = [
       "streamrip-qobuz>=0.1.0",
       "streamrip-tidal>=0.1.0",
       "streamrip-deezer>=0.1.0",
       "streamrip-soundcloud>=0.1.0",
   ]
   qobuz = ["streamrip-qobuz>=0.1.0"]
   tidal = ["streamrip-tidal>=0.1.0"]
   # etc.
   ```

2. **Update Main Orchestrator**
   ```python
   # streamrip/rip/main.py
   from streamrip_core.plugin_system import PluginRegistry

   class Main:
       def __init__(self, config):
           self.registry = PluginRegistry()
           self.registry.discover()  # Auto-discover installed services

           # Create clients from plugins
           self.clients = {}
           for service_name, plugin in self.registry.plugins.items():
               if hasattr(config, service_name):
                   service_config = getattr(config, service_name)
                   self.clients[service_name] = plugin.client_class(service_config)
   ```

3. **Graceful Degradation**
   - Handle missing services gracefully
   - Show helpful error if user tries to use uninstalled service
   - Suggest installation command

#### Phase 5: Documentation and Migration Guide (Week 10)

1. **User Migration Guide**
   - How to install services
   - Breaking changes from monolithic version
   - Troubleshooting common issues

2. **Developer Documentation**
   - How to create custom service plugins
   - Core API documentation
   - Contributing guidelines per repo

3. **Architecture Documentation**
   - Plugin system design
   - Version compatibility matrix
   - Release process

---

## Migration Path

### For Users

**Before (Monolithic)**:
```bash
pip install streamrip
streamrip url "https://open.qobuz.com/album/..."
```

**After (Plugin System)**:

**Option A**: Install all services (same as before)
```bash
pip install streamrip[all-services]
streamrip url "https://open.qobuz.com/album/..."
```

**Option B**: Install specific services only
```bash
pip install streamrip streamrip-qobuz streamrip-tidal
streamrip url "https://open.qobuz.com/album/..."  # Works
streamrip url "https://deezer.com/album/..."      # Error: Service not installed
```

### For Contributors

**Before**: Single PR in one repository

**After**:
1. Core changes: PR to `streamrip-core`
2. Wait for core release
3. Update service repos to use new core version
4. Service changes: PR to specific service repo

---

## Challenges and Mitigation

### Challenge 1: Breaking Changes in Core

**Problem**: Core API changes break all services

**Mitigation**:
- Semantic versioning with strict API contracts
- Deprecation warnings before removing features
- Keep core API minimal and stable
- Version core aggressively (keep old versions supported)
- Automated compatibility testing across service versions

### Challenge 2: Testing Integration

**Problem**: Hard to test services work together

**Mitigation**:
- Integration test suite in main repo
- Nightly builds testing latest versions of all services
- Matrix testing: core version × service versions
- Docker compose for local integration testing

### Challenge 3: Discovery and Installation

**Problem**: Users don't know which packages to install

**Mitigation**:
- Clear documentation on installation options
- `streamrip[all-services]` convenience extra
- First-run detection with helpful error messages
- Consider creating meta-package that installs all

### Challenge 4: Version Compatibility Matrix

**Problem**: Tracking which versions work together

**Mitigation**:
- Document compatibility in main README
- Automated compatibility testing
- Pin core version requirements in services
- Release notes showing tested combinations

### Challenge 5: Duplicated CI/CD

**Problem**: Each repo needs own GitHub Actions, etc.

**Mitigation**:
- Create reusable workflow templates
- Shared GitHub Actions in separate repo
- Template repository for new services
- Consider monorepo if this becomes painful

---

## Final Recommendations

### Recommendation 1: START WITH MONOREPO REFACTORING ⭐ (RECOMMENDED)

**What to Do**:
1. Refactor current monorepo into clean, self-contained service modules
2. Create clear boundaries between services and core
3. Implement plugin registry within monorepo
4. Allow external plugins to be loaded (for community contributions)

**Benefits**:
- Get modularity benefits without multi-repo complexity
- Can extract services later if truly needed
- Easier to maintain and develop
- Simpler for users

**When to Extract**:
- When services have truly independent development teams
- When licensing requirements differ per service
- When release cycles need to be completely independent
- When repository size becomes unmanageable (not the case now)

**Implementation**:
```
streamrip/
├── streamrip/
│   ├── core/              # Core abstractions (could become package)
│   │   ├── client.py
│   │   ├── downloadable.py
│   │   └── plugin_registry.py
│   ├── services/          # Built-in services
│   │   ├── qobuz/
│   │   ├── tidal/
│   │   ├── deezer/
│   │   └── soundcloud/
│   └── rip/               # Main application
└── tests/
```

### Recommendation 2: IF YOU MUST SPLIT, USE OPTION 3 (Monorepo with Multiple Packages)

**What to Do**:
1. Keep single repository
2. Structure as multiple packages under `packages/`
3. Use Poetry or PDM workspace features
4. Publish packages independently to PyPI

**Benefits**:
- Get independent versioning and publishing
- Keep atomic commits across packages
- Shared CI/CD and tooling
- Easier refactoring across boundaries

**Tools**:
- Poetry: Supports workspace dependencies
- PDM: Modern Python dependency management with workspace support
- Nx: Advanced monorepo tooling (if needed later)

### Recommendation 3: ONLY USE MULTI-REPO IF...

**Conditions**:
- You have dedicated teams per service
- Services have completely different stakeholders
- Legal/licensing requirements mandate separation
- You're comfortable with significant coordination overhead

**If pursuing this**, follow the Phase 1-5 implementation strategy above.

---

## Summary Decision Matrix

| Approach | Complexity | Flexibility | Maintenance | User Experience | Recommendation |
|----------|-----------|-------------|-------------|-----------------|----------------|
| **Monorepo with Modules** | Low | Medium | Low | Excellent | ⭐⭐⭐⭐⭐ BEST |
| **Monorepo with Packages** | Medium | High | Medium | Good | ⭐⭐⭐⭐ Good if need independence |
| **Multi-Repository** | High | Highest | High | Complex | ⭐⭐ Only if required |

---

## Next Steps

### If Proceeding with Monorepo Refactoring (Recommended):

1. **Week 1**: Create `streamrip/core/` module with abstractions
2. **Week 2**: Refactor one service (SoundCloud) to use clean module structure
3. **Week 3**: Apply pattern to remaining services
4. **Week 4**: Implement plugin registry for external plugins
5. **Week 5**: Document architecture and contribution guidelines

### If Proceeding with Repository Split:

1. **Month 1**: Follow Phase 1-2 (Core + one service)
2. **Month 2**: Validate approach, gather feedback, adjust
3. **Month 3**: Migrate remaining services (Phase 3)
4. **Month 4**: Update main app and document (Phases 4-5)

---

## Conclusion

While splitting services into separate repositories is technically feasible and has benefits for large-scale projects with distributed teams, **I strongly recommend starting with a modular monorepo architecture**. This provides:

- ✅ Clear service boundaries
- ✅ Ability to extract later if needed
- ✅ Much lower complexity and maintenance burden
- ✅ Better developer experience
- ✅ Simpler user experience
- ✅ Easier testing and integration

The current codebase (~10K LOC) is not large enough to warrant the overhead of multiple repositories. Save multi-repo for when you have clear organizational reasons beyond code organization.

---

## Questions to Consider

Before deciding, answer these:

1. **Do you have multiple teams?** If no → monorepo
2. **Do services need independent release cycles?** If no → monorepo
3. **Are there licensing differences?** If no → monorepo
4. **Is the codebase unmanageably large?** If no → monorepo
5. **Do you want community plugins?** If yes → plugin system (works in monorepo)

If you answered "no" to most of these, **stick with a well-structured monorepo**.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-23
**Feedback**: Please provide feedback on this analysis before proceeding with any major architectural changes.
