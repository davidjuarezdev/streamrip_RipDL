# Qobuz Migration - Quick Reference

**TL;DR**: Complete checklist and before/after guide for migrating Qobuz service

---

## Migration Checklist

### Pre-Migration (15 min)

- [ ] Read `QOBUZ_MIGRATION_GUIDE.md` (overview)
- [ ] Create feature branch: `git checkout -b qobuz-migration`
- [ ] Run existing tests: `pytest tests/client/test_qobuz.py` (if exists)
- [ ] Document baseline coverage: `coverage run -m pytest`

### Phase 1: Directory Setup (10 min)

- [ ] Create `streamrip/services/qobuz/` directory
- [ ] Create all required files (see structure below)
- [ ] Create `tests/services/qobuz/` directory
- [ ] Create test files

**Commands**:
```bash
mkdir -p streamrip/services/qobuz tests/services/qobuz
touch streamrip/services/qobuz/{__init__,plugin,client,spoofer,config,metadata,constants,README}.py
touch tests/services/qobuz/{__init__,conftest,test_plugin,test_client,test_spoofer,test_config,test_integration}.py
```

### Phase 2: Extract Components (2 hours)

- [ ] Extract constants to `constants.py`
- [ ] Extract QobuzConfig to `config.py`
- [ ] Extract QobuzSpoofer to `spoofer.py`
- [ ] Extract QobuzClient to `client.py`
- [ ] Extract metadata parsing to `metadata.py`
- [ ] Create QobuzPlugin in `plugin.py`
- [ ] Set up `__init__.py` exports

### Phase 3: Backward Compatibility (20 min)

- [ ] Update `streamrip/client/qobuz.py` with deprecation warning
- [ ] Update `streamrip/config.py` with import redirect
- [ ] Test old imports still work

### Phase 4: Plugin Integration (30 min)

- [ ] Register in `streamrip/plugin_system/loader.py`
- [ ] Test plugin discovery works
- [ ] Test URL detection through registry

### Phase 5: Testing (1 hour)

- [ ] Write plugin tests (test_plugin.py)
- [ ] Write client tests (test_client.py)
- [ ] Write config tests (test_config.py)
- [ ] Write integration tests (test_integration.py)
- [ ] Run all tests: `pytest tests/services/qobuz/ -v`
- [ ] Check coverage: `pytest --cov=streamrip.services.qobuz`

### Phase 6: Verification (30 min)

- [ ] All new tests pass
- [ ] All existing tests still pass
- [ ] Coverage ≥85%
- [ ] No breaking changes
- [ ] Old imports work (with warnings)
- [ ] Documentation complete

### Phase 7: Commit (10 min)

- [ ] Review all changes
- [ ] Commit with detailed message
- [ ] Push to feature branch

**Total Time**: ~4-5 hours

---

## Before/After Comparison

### Before: Monolithic Structure

```
streamrip/
├── client/
│   └── qobuz.py                    # 456 lines - everything
├── config.py                       # QobuzConfig buried here
└── metadata/
    └── album.py                    # from_qobuz() buried here
```

**Problems**:
- 😞 All Qobuz code in one giant file
- 😞 Hard to find Qobuz-specific code
- 😞 Mixed with other services
- 😞 No clear boundaries

### After: Modular Plugin Structure

```
streamrip/
├── services/
│   └── qobuz/                      # Self-contained module
│       ├── __init__.py             # Public API
│       ├── plugin.py               # Service registration
│       ├── client.py               # QobuzClient
│       ├── spoofer.py              # QobuzSpoofer
│       ├── config.py               # QobuzConfig
│       ├── metadata.py             # Metadata parsing
│       ├── constants.py            # Constants
│       └── README.md               # Documentation
└── plugin_system/
    └── loader.py                   # Registers Qobuz plugin
```

**Benefits**:
- ✅ All Qobuz code in one place
- ✅ Clear module boundaries
- ✅ Easy to find and modify
- ✅ Can be tested independently
- ✅ Plugin-based architecture

---

## Code Changes Summary

### Import Changes

**OLD**:
```python
from streamrip.client.qobuz import QobuzClient
from streamrip.config import QobuzConfig
```

**NEW**:
```python
from streamrip.services.qobuz import QobuzClient, QobuzConfig
```

*(Old imports still work with deprecation warnings)*

### Usage (No Changes)

```python
# User code remains unchanged
config = QobuzConfig(
    email_or_userid="user@example.com",
    password_or_token="password_hash",
    quality=4
)

client = QobuzClient(config)
await client.login()
metadata = await client.get_metadata("album_id", "album")
```

---

## File-by-File Guide

### 1. constants.py

**Purpose**: Centralize all Qobuz constants

**What to extract**:
- `QOBUZ_BASE_URL`
- `QOBUZ_FEATURED_KEYS`
- Quality mapping
- URL patterns

**Lines**: ~30

### 2. config.py

**Purpose**: Qobuz configuration dataclass

**What to extract**:
- `QobuzConfig` from `streamrip/config.py`
- Add validation methods

**Lines**: ~40

### 3. spoofer.py

**Purpose**: App credential extraction

**What to extract**:
- `QobuzSpoofer` class (lines 47-142 from qobuz.py)
- Regex patterns
- Async context manager

**Lines**: ~100

### 4. client.py

**Purpose**: Main Qobuz API client

**What to extract**:
- `QobuzClient` class (lines 144-456 from qobuz.py)
- All methods unchanged
- Update imports

**Lines**: ~320

### 5. metadata.py

**Purpose**: Metadata parsing

**What to extract**:
- `from_qobuz()` from `streamrip/metadata/album.py`
- Track metadata parsing
- Cover art extraction

**Lines**: ~80

### 6. plugin.py

**Purpose**: Service registration

**What to create** (NEW):
- `QobuzPlugin` class
- Implements `ServicePlugin` protocol
- URL detection
- Client factory

**Lines**: ~80

### 7. __init__.py

**Purpose**: Public API

**What to export**:
```python
from .client import QobuzClient
from .config import QobuzConfig
from .plugin import QobuzPlugin
from .spoofer import QobuzSpoofer
from .constants import *

__all__ = [
    "QobuzClient",
    "QobuzConfig",
    "QobuzPlugin",
    "QobuzSpoofer",
]
```

---

## Testing Quick Reference

### Minimal Test Suite

```python
# test_plugin.py - Essential tests
- test_plugin_initialization()
- test_url_compatibility()
- test_create_client()
- test_plugin_registration()

# test_client.py - Essential tests
- test_client_initialization()
- test_login_success()
- test_login_invalid_credentials()
- test_get_metadata()
- test_get_downloadable()

# test_config.py - Essential tests
- test_config_creation()
- test_valid_quality_levels()
- test_has_credentials()

# test_integration.py - Essential tests
- test_plugin_discovery()
- test_url_detection_integration()
- test_client_creation_through_registry()
```

### Running Tests

```bash
# Run all Qobuz tests
pytest tests/services/qobuz/ -v

# Run with coverage
pytest tests/services/qobuz/ --cov=streamrip.services.qobuz

# Run specific test
pytest tests/services/qobuz/test_plugin.py::TestQobuzPlugin::test_url_compatibility -v
```

---

## Common Issues & Solutions

### Issue: Import Error after migration

**Error**: `ImportError: cannot import name 'QobuzClient' from 'streamrip.client.qobuz'`

**Solution**: Make sure backward compatibility shim is in place:
```python
# streamrip/client/qobuz.py
from streamrip.services.qobuz import QobuzClient, QobuzSpoofer
```

### Issue: Tests can't find module

**Error**: `ModuleNotFoundError: No module named 'streamrip.services.qobuz'`

**Solution**:
1. Ensure `__init__.py` exists in `streamrip/services/qobuz/`
2. Reinstall package: `pip install -e .`

### Issue: Plugin not discovered

**Error**: Service 'qobuz' not available in registry

**Solution**: Check `streamrip/plugin_system/loader.py`:
```python
def load_builtin_plugins():
    from streamrip.services.qobuz import QobuzPlugin
    registry.register(QobuzPlugin())
```

### Issue: Circular imports

**Error**: `ImportError: cannot import ... (circular import)`

**Solution**: Use local imports within methods instead of module-level imports

---

## Validation Commands

### Before Starting
```bash
# Ensure clean state
git status

# Run existing tests
pytest

# Check current coverage
coverage run -m pytest
coverage report
```

### After Migration
```bash
# Run new tests
pytest tests/services/qobuz/ -v

# Run all tests (ensure nothing broke)
pytest

# Check coverage
pytest tests/services/qobuz/ --cov=streamrip.services.qobuz --cov-report=term

# Test backward compatibility
python -c "from streamrip.client.qobuz import QobuzClient; print('OK')"

# Test plugin discovery
python -c "
from streamrip.plugin_system import get_registry, PluginLoader
PluginLoader.load_builtin_plugins()
assert get_registry().is_service_available('qobuz')
print('Plugin discovered: OK')
"
```

---

## Success Criteria

✅ **Directory Structure**:
- `streamrip/services/qobuz/` exists with all files
- `tests/services/qobuz/` exists with all test files

✅ **Functionality**:
- All 6+ files created (plugin, client, spoofer, config, metadata, constants)
- QobuzPlugin registered in loader
- All imports work (new and old)

✅ **Tests**:
- All new tests pass
- All existing tests still pass
- Coverage ≥85% for new code

✅ **Integration**:
- Plugin discoverable by registry
- URL detection works
- Client can be created via plugin

✅ **Documentation**:
- README.md in service directory
- Inline documentation complete
- Migration notes added

---

## Timeline

| Task | Estimated Time |
|------|----------------|
| Setup directories | 10 min |
| Extract constants | 15 min |
| Extract config | 20 min |
| Extract spoofer | 30 min |
| Extract client | 45 min |
| Extract metadata | 30 min |
| Create plugin | 45 min |
| Backward compatibility | 20 min |
| Write tests | 60 min |
| Documentation | 30 min |
| Verification | 30 min |
| **Total** | **~5 hours** |

---

## Next Steps After Qobuz

Once Qobuz migration is complete and validated:

1. **Apply pattern to Deezer** (similar complexity)
2. **Apply pattern to SoundCloud** (simpler)
3. **Apply pattern to Tidal** (most complex - OAuth)

Each subsequent service will be faster as you refine the process.

---

## Quick Commands

```bash
# Create branch
git checkout -b qobuz-migration

# Create structure
mkdir -p streamrip/services/qobuz tests/services/qobuz

# Run tests
pytest tests/services/qobuz/ -v --cov

# Commit
git add streamrip/services/qobuz/ tests/services/qobuz/
git commit -m "Migrate Qobuz to plugin architecture"

# Verify
pytest && echo "✓ All tests pass"
```

---

## Resources

- **Full Guide**: See `QOBUZ_MIGRATION_GUIDE.md`
- **Testing Guide**: See `QOBUZ_TESTING_GUIDE.md`
- **General Plan**: See `MONOREPO_REFACTORING_PLAN.md`

---

**Ready to start?** Follow the checklist top to bottom! 🚀
