# Monorepo Refactoring - Quick Start Guide

**TL;DR**: Refactor streamrip into a modular monorepo with plugin system. 6-7 weeks. Keep all services in one repo but cleanly separated.

---

## 📚 Documentation Overview

| Document | Purpose | Read This If... |
|----------|---------|-----------------|
| **MUSIC_SERVICE_REPOSITORY_SPLIT_RECOMMENDATIONS.md** | Strategic analysis | You want to understand WHY we're doing this |
| **MONOREPO_REFACTORING_PLAN.md** | Implementation plan | You want to know HOW we'll do it |
| **REFACTORING_EXAMPLES.md** | Code examples | You want to SEE what it looks like |
| **QUICK_START_GUIDE.md** (this doc) | Quick reference | You want to get started NOW |

---

## 🎯 What We're Doing

**Current State**:
- All services (Qobuz, Tidal, Deezer, SoundCloud) mixed together
- Hard to add new services
- Tight coupling between components

**Target State**:
- Each service in its own module (`streamrip/services/<service>/`)
- Plugin system for service discovery
- Clear separation between core and services
- Easy to add new services (even external ones)

---

## 🏗️ Architecture at a Glance

```
streamrip/
├── core/                    # Abstract base classes
│   ├── client.py
│   ├── downloadable.py
│   └── media.py
│
├── plugin_system/           # Service discovery
│   ├── registry.py
│   └── loader.py
│
└── services/                # Self-contained services
    ├── qobuz/
    │   ├── plugin.py        # Service registration
    │   ├── client.py        # Service implementation
    │   └── config.py        # Service config
    ├── tidal/
    ├── deezer/
    └── soundcloud/
```

**Key Concept**: Each service is 100% self-contained in its own directory.

---

## 📅 Timeline

| Week | Milestone |
|------|-----------|
| 1 | Core abstractions extracted |
| 2 | Plugin system working |
| 3 | SoundCloud migrated (pilot) |
| 4-5 | Other services migrated |
| 6 | Main app updated |
| 7 | Testing and docs |

**Total: 6-7 weeks**

---

## 🚀 Getting Started

### Step 1: Review Documents (1 hour)

1. Read **MUSIC_SERVICE_REPOSITORY_SPLIT_RECOMMENDATIONS.md** - Understand the strategy
2. Skim **MONOREPO_REFACTORING_PLAN.md** - Get familiar with phases
3. Look at **REFACTORING_EXAMPLES.md** - See concrete code

### Step 2: Create Feature Branch

```bash
git checkout -b refactor/modular-monorepo
```

### Step 3: Run Current Tests

```bash
# Establish baseline
pytest
coverage run -m pytest
coverage report
```

Document current test coverage - this is your baseline.

### Step 4: Start Phase 1

Follow **Phase 1** in `MONOREPO_REFACTORING_PLAN.md`:

1. Create `streamrip/core/` directory
2. Extract `Client` base class
3. Extract `Downloadable` base class
4. Extract shared utilities
5. Run tests (should all pass!)

---

## 🔑 Key Principles

### 1. Self-Contained Services

Each service directory should contain EVERYTHING for that service:

```
services/qobuz/
├── plugin.py          # Service registration
├── client.py          # QobuzClient
├── downloadable.py    # QobuzDownloadable
├── metadata.py        # Qobuz metadata parsing
├── config.py          # QobuzConfig
└── utils.py           # Qobuz-specific utilities
```

❌ **Don't**: Scatter Qobuz code across multiple top-level directories
✅ **Do**: Keep all Qobuz code in `services/qobuz/`

### 2. Plugin Protocol

Every service implements the same interface:

```python
class ServicePlugin:
    @property
    def name(self) -> str: ...              # "qobuz"

    @property
    def client_class(self) -> Type[Client]: # QobuzClient

    def is_url_compatible(self, url: str) -> bool: ...
    def create_client(self, config) -> Client: ...
```

### 3. Backward Compatibility

Keep old imports working during migration:

```python
# OLD: streamrip/client/qobuz.py
from streamrip.services.qobuz import QobuzClient  # ✅ Redirect

warnings.warn("Use streamrip.services.qobuz instead", DeprecationWarning)
```

### 4. Gradual Migration

Migrate one service at a time:
1. SoundCloud (simplest) ✅ Proof of concept
2. Deezer ✅ Validate pattern
3. Qobuz ✅ Test with complex service
4. Tidal ✅ Most complex

### 5. Test Every Phase

After each phase:
- ✅ All existing tests pass
- ✅ Code coverage maintained
- ✅ No functionality changes

---

## 🧪 Testing Strategy

### Unit Tests

```python
# Test plugin registration
def test_qobuz_plugin_registration():
    from streamrip.services.qobuz import QobuzPlugin
    plugin = QobuzPlugin()
    registry.register(plugin)
    assert registry.is_service_available('qobuz')

# Test URL detection
def test_qobuz_url_detection():
    plugin = QobuzPlugin()
    assert plugin.is_url_compatible('https://open.qobuz.com/album/123')
```

### Integration Tests

```python
# Test end-to-end flow
async def test_download_via_plugin_system():
    app = Main(config)
    await app.add('https://open.qobuz.com/album/123')
    await app.rip()
    # Verify file downloaded correctly
```

---

## 📋 Checklist: Before You Start

- [ ] Read all documentation
- [ ] Understand the plugin pattern
- [ ] Have baseline test coverage numbers
- [ ] Created feature branch
- [ ] Set up project tracking (GitHub Issues/Project Board)

---

## 📋 Checklist: Per Service Migration

For each service you migrate:

- [ ] Create `services/<service>/` directory
- [ ] Implement `<Service>Plugin` class
- [ ] Move client code to `services/<service>/client.py`
- [ ] Move downloadable to `services/<service>/downloadable.py`
- [ ] Move metadata parsing to `services/<service>/metadata.py`
- [ ] Move config to `services/<service>/config.py`
- [ ] Add backward-compatible imports in old locations
- [ ] Write plugin tests
- [ ] Run all existing tests
- [ ] Update documentation

---

## 🎓 Example: Migrating a Service

### Before

```
streamrip/client/qobuz.py          # 800 lines - everything mixed
```

### After

```
streamrip/services/qobuz/
├── plugin.py         # 50 lines  - registration
├── client.py         # 400 lines - client logic
├── downloadable.py   # 100 lines - download handling
├── metadata.py       # 150 lines - parsing
├── config.py         # 30 lines  - config
└── utils.py          # 70 lines  - spoofer, etc.
```

### Plugin Implementation

```python
# streamrip/services/qobuz/plugin.py
from streamrip.plugin_system import ServicePlugin
from .client import QobuzClient
from .config import QobuzConfig

class QobuzPlugin:
    name = "qobuz"
    display_name = "Qobuz"
    client_class = QobuzClient
    config_class = QobuzConfig

    def get_url_patterns(self):
        return [r'qobuz\.com', r'open\.qobuz\.com']

    def is_url_compatible(self, url):
        # Check if URL matches patterns
        ...

    def create_client(self, config):
        return QobuzClient(config)
```

---

## 🚨 Common Pitfalls to Avoid

### ❌ Don't: Mix service code with core

```python
# BAD: streamrip/core/client.py
class Client:
    def qobuz_specific_method(self):  # ❌ Service-specific in core
        pass
```

### ✅ Do: Keep core abstract

```python
# GOOD: streamrip/core/client.py
class Client(ABC):
    @abstractmethod
    async def get_metadata(self, item_id, media_type):
        pass
```

### ❌ Don't: Break existing functionality

```python
# BAD: Removing old import path immediately
# streamrip/client/qobuz.py - DELETED ❌
```

### ✅ Do: Maintain backward compatibility

```python
# GOOD: streamrip/client/qobuz.py
from streamrip.services.qobuz import QobuzClient
warnings.warn("Deprecated", DeprecationWarning)
```

### ❌ Don't: Skip testing

```python
# BAD: Move code, assume it works
```

### ✅ Do: Test after every change

```bash
# GOOD: Test continuously
pytest tests/services/qobuz/
pytest  # Run all tests
```

---

## 🆘 Troubleshooting

### "Import Error" after moving code

**Problem**: Moved code but forgot to update imports

**Solution**:
```bash
# Find all imports of the moved module
grep -r "from streamrip.client.qobuz" .

# Update to new path
# from streamrip.client.qobuz import QobuzClient
# → from streamrip.services.qobuz import QobuzClient
```

### Tests failing after migration

**Problem**: Service-specific tests can't find module

**Solution**:
```python
# Update test imports
# OLD: from streamrip.client.qobuz import QobuzClient
# NEW: from streamrip.services.qobuz import QobuzClient
```

### Plugin not discovered

**Problem**: Plugin not registered in loader

**Solution**:
```python
# streamrip/plugin_system/loader.py
def load_builtin_plugins():
    from streamrip.services.qobuz import QobuzPlugin
    registry.register(QobuzPlugin())  # ← Make sure this exists
```

---

## 📊 Success Metrics

Track these metrics throughout refactoring:

| Metric | Target |
|--------|--------|
| Test Coverage | ≥85% (maintain or improve) |
| Tests Passing | 100% |
| Services Migrated | 4/4 (Qobuz, Tidal, Deezer, SoundCloud) |
| Plugin Tests | 90%+ coverage |
| Documentation | Complete for all services |
| Backward Compatibility | 100% during v1.x |

---

## 🎯 Definition of Done

The refactoring is complete when:

✅ All 4 services migrated to `services/` directory
✅ Plugin system operational
✅ All existing tests pass
✅ Test coverage ≥85%
✅ Documentation complete
✅ Backward-compatible imports in place
✅ No breaking changes for users
✅ Integration tests pass
✅ Ready to merge to main

---

## 📖 Key Concepts

### Plugin System

**Registry**: Central service that tracks all plugins
**Plugin**: Provides metadata and factory for a service
**Loader**: Discovers and registers plugins

### Service Lifecycle

1. **Discovery**: PluginLoader finds service plugin
2. **Registration**: Plugin added to registry
3. **URL Detection**: User provides URL → registry detects service
4. **Client Creation**: Plugin creates configured client
5. **Authentication**: Client logs in to service
6. **Download**: Client fetches and downloads content

### Code Organization

```
core/           → What ALL services share (interfaces)
plugin_system/  → HOW services are discovered (infrastructure)
services/       → WHAT each service does (implementations)
```

---

## 🔗 External Resources

- **Python Entry Points**: https://packaging.python.org/en/latest/specifications/entry-points/
- **ABC (Abstract Base Classes)**: https://docs.python.org/3/library/abc.html
- **Protocol (Structural Subtyping)**: https://peps.python.org/pep-0544/

---

## ✅ Quick Decision Tree

**Should I proceed with this refactoring?**

```
Do you need to add new services frequently?
├─ Yes → ✅ Proceed (plugin system helps)
└─ No
   └─ Is the codebase hard to navigate?
      ├─ Yes → ✅ Proceed (organization helps)
      └─ No
         └─ Do you want to support external plugins?
            ├─ Yes → ✅ Proceed
            └─ No → ⚠️  Consider if worth the effort
```

**How long will this take?**
- 1 developer full-time: 6-7 weeks
- 2 developers: 4-5 weeks
- Part-time: 3-4 months

**What's the risk?**
- 🟢 Low: We're not changing functionality, just organizing code
- 🟡 Medium: Need to be careful with imports
- 🔴 High risk areas: Main orchestrator changes (Phase 5)

---

## 🚦 Phase 0 Checklist (Start Here!)

Ready to begin? Complete these tasks:

- [ ] Read this quick start guide
- [ ] Review detailed plan (`MONOREPO_REFACTORING_PLAN.md`)
- [ ] Look at code examples (`REFACTORING_EXAMPLES.md`)
- [ ] Run current tests and document coverage
- [ ] Create feature branch: `refactor/modular-monorepo`
- [ ] Create directories:
  ```bash
  mkdir -p streamrip/core
  mkdir -p streamrip/plugin_system
  mkdir -p streamrip/services/{qobuz,tidal,deezer,soundcloud}
  ```
- [ ] Tag current state: `git tag pre-refactor-backup`
- [ ] Set up project board for tracking
- [ ] Get team buy-in and approval

**Once complete, proceed to Phase 1!**

---

## 💡 Pro Tips

1. **Commit frequently** - Each small change should be a commit
2. **Test continuously** - Don't wait until the end
3. **One service at a time** - Don't try to migrate all at once
4. **Keep notes** - Document gotchas as you find them
5. **Pair program** - Especially for complex services like Tidal
6. **Use Git branches** - One branch per phase if needed

---

**Questions?** Refer to the detailed documentation or ask for clarification.

**Ready?** Start with Phase 0, then move to Phase 1!

Good luck! 🚀
