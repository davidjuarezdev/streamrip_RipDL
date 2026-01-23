# Merge Plan: omnunum/streamrip Fork into davidjuarezdev/streamrip_RipDL

## Executive Summary

This document outlines the plan to merge changes from the **omnunum/streamrip** fork (approximately 80 commits ahead of nathom/streamrip) into your fork. The omnunum fork contains substantial feature additions and improvements that significantly enhance the original streamrip functionality.

---

## Repository Analysis

### Source: omnunum/streamrip
- **Default Branch:** main
- **Stars:** 9
- **Last Updated:** December 2025
- **Key Focus:** Enhanced metadata, Docker support, RYM integration, improved concurrency

### Target: davidjuarezdev/streamrip_RipDL
- **Current Branch:** claude/merge-streamrip-forks-Dc0wD
- **Base:** nathom/streamrip dev branch with Python 3.10-3.13 compatibility updates

### Original: nathom/streamrip
- **Default Branch:** dev
- **Last Release:** v2.1.0 (March 2025)
- **Status:** Appears to have reduced maintenance activity

---

## Key Features in omnunum Fork

### 1. RateYourMusic (RYM) Integration
**Files Added/Modified:**
- `rym-metadata` dependency (v1.4.4) - external package for RYM scraping
- Dockerfile with Camoufox browser support for RYM scraping
- LLM-based album matching via Groq API

**Impact:** Major feature addition for music metadata enrichment

### 2. Enhanced Metadata Tagging
**Features:**
- BPM (beats per minute) extraction
- ReplayGain values
- UPC/Barcode codes
- Multi-artist support (separate "artists" field)
- MusicBrainz-aligned field naming
- RYM descriptors/genres

**Files Likely Modified:**
- `streamrip/metadata/tagger.py`
- `streamrip/metadata/album.py`
- `streamrip/metadata/track.py`

### 3. New Tidal Manifest Implementation
**Commits:**
- `e23306c` - Implement new Tidal Manifest
- `96ac806` - Remove legacy MQA support

**Impact:** Updates Tidal integration for current API

### 4. Quality Fallback System
**Features:**
- Automatic fallback to lower quality when requested quality unavailable
- Unified quality scale (0-3) across services

**Files Modified:**
- `streamrip/client/downloadable.py`
- Service-specific client files

### 5. Download Queue Task System
**New File:**
- `streamrip/download_task.py` - Dataclass for queue-based download processing

**Features:**
- Track retry counts
- Album reference tracking
- Task type classification

### 6. Docker Support
**New Files:**
- `Dockerfile` - Multi-layer optimized build
- Wrapper scripts for rip and rym-tag commands

**Features:**
- 67% image size reduction (4.79GB → 1.57GB)
- Camoufox browser for RYM scraping
- Cron-based scheduled downloads
- User permission management via gosu

### 7. Favorites Downloading
**Commits:**
- `069f63b` - Download albums from fav tracks
- `685ba29` - Use correct deezer url for track favs
- `2a51bc2` - Download album of favorite tracks

**Impact:** New feature for downloading user favorites

### 8. Improved Concurrency
**Features:**
- `asyncio.Semaphore` for request handling
- Non-blocking download initiation
- Client login locking
- CLI progress update locking

### 9. Enhanced Path Templating
**New Placeholders:**
- `{releasetype}`
- `{upc}`
- `{source_artist_id}`
- Proper casing options

---

## Merge Strategy Options

### Option A: Git Remote Merge (Recommended)
Add omnunum fork as a remote and merge the branch.

```bash
# Add omnunum fork as remote
git remote add omnunum https://github.com/omnunum/streamrip.git

# Fetch all branches
git fetch omnunum

# Create merge branch (already on it)
git checkout claude/merge-streamrip-forks-Dc0wD

# Merge omnunum's main branch
git merge omnunum/main --allow-unrelated-histories
```

**Pros:**
- Preserves full commit history
- Git handles conflict detection
- Easy to track which changes came from where

**Cons:**
- May have many merge conflicts due to divergent histories
- Includes ALL commits including those you may not want

### Option B: Cherry-Pick Specific Features
Selectively cherry-pick commits by feature group.

```bash
# Cherry-pick commits in logical groups
git cherry-pick <commit-hash>
```

**Feature Groups to Cherry-Pick:**
1. Tidal Manifest updates (`e23306c`, `96ac806`)
2. Quality fallback system
3. Favorites downloading (`069f63b`, `685ba29`, `2a51bc2`)
4. Concurrency improvements (`43589d0`, `52e05a5`, `ebfe30b`)
5. Docker support (if desired)
6. RYM integration (if desired)

**Pros:**
- Full control over what's included
- Can exclude unwanted changes
- Cleaner commit history

**Cons:**
- More manual work
- May miss dependent changes
- Order matters for dependencies

### Option C: Selective File Copy with Manual Integration
Copy specific files and manually integrate changes.

**Pros:**
- Maximum control
- Can modernize code during integration

**Cons:**
- Most time-consuming
- Risk of missing changes
- No commit attribution

---

## Recommended Approach: Hybrid Strategy

### Phase 1: Initial Merge
1. Add omnunum as remote
2. Create a test branch and attempt full merge
3. Assess conflict scope

### Phase 2: Conflict Resolution
1. Prioritize critical fixes (Tidal manifest, quality fallback)
2. Integrate metadata enhancements
3. Add concurrency improvements
4. Optionally add Docker/RYM features

### Phase 3: Testing
1. Run existing test suite
2. Test each streaming service manually
3. Verify metadata tagging

### Phase 4: Cleanup
1. Update documentation
2. Sync version numbers
3. Update pyproject.toml dependencies

---

## Detailed Merge Steps

### Step 1: Backup Current State
```bash
git branch backup-before-omnunum-merge
```

### Step 2: Add Remote and Fetch
```bash
git remote add omnunum https://github.com/omnunum/streamrip.git
git fetch omnunum
```

### Step 3: Attempt Merge
```bash
git merge omnunum/main --no-commit
```

### Step 4: Review Conflicts
Likely conflict areas:
- `pyproject.toml` - dependency versions, new dependencies
- `streamrip/client/tidal.py` - Tidal manifest changes
- `streamrip/client/downloadable.py` - quality fallback
- `streamrip/metadata/*.py` - metadata enhancements
- `streamrip/config.py` and `config.toml` - new config options

### Step 5: Resolve Conflicts
For each conflict:
1. Keep both sets of changes where possible
2. Prefer omnunum's implementation for features we want
3. Preserve our Python 3.10-3.13 compatibility updates

### Step 6: Test and Validate
```bash
# Run tests
pytest tests/

# Verify builds
poetry install
poetry build
```

---

## Dependency Changes Required

### New Dependencies (from omnunum fork)
```toml
# In pyproject.toml
rym-metadata = { git = "https://github.com/omnunum/rym-metadata.git", tag = "v1.4.4" }
```

### Version Updates
- `m3u8`: `^0.9.0` → `^6.0.0` (already updated in your fork)
- `aiofiles`: Consider aligning versions

### Optional Dependencies
- `rym-metadata` - only needed if using RYM integration

---

## Risk Assessment

### Low Risk
- Path templating enhancements
- Logging improvements
- Test coverage additions

### Medium Risk
- Metadata changes (may affect existing tagged files)
- Quality fallback logic (could affect download quality)
- Concurrency changes (potential race conditions)

### High Risk
- Tidal manifest changes (breaking if Tidal API changed)
- RYM integration (requires additional setup, browser dependencies)
- Docker support (adds complexity)

---

## Testing Strategy

### Unit Tests
```bash
pytest tests/ -v
```

### Integration Tests (Manual)
1. Download single track from each service
2. Download album from each service
3. Verify metadata in downloaded files
4. Test quality fallback by requesting unavailable quality
5. Test favorites download feature

### Regression Tests
1. Verify existing config files still work
2. Check download database compatibility
3. Validate file path generation

---

## Post-Merge Tasks

1. [ ] Update README.md with new features
2. [ ] Update version number in pyproject.toml
3. [ ] Create migration guide for config changes
4. [ ] Document RYM integration setup (if included)
5. [ ] Update Docker documentation (if included)
6. [ ] Create release notes

---

## Files to Watch During Merge

### Critical Files (High Conflict Probability)
- `pyproject.toml`
- `streamrip/config.py`
- `streamrip/config.toml`
- `streamrip/client/tidal.py`
- `streamrip/client/downloadable.py`

### New Files to Include
- `streamrip/download_task.py`
- `Dockerfile` (optional)
- Docker-related scripts (optional)

### Files to Review Carefully
- `streamrip/metadata/tagger.py`
- `streamrip/media/track.py`
- `streamrip/media/album.py`
- `streamrip/rip/main.py`

---

## Commit Summary from omnunum Fork (Grouped by Feature)

### RYM Integration (~15 commits)
- rym-metadata dependency updates (v1.2.2 → v1.4.4)
- Dockerfile RYM configuration
- Single RYM scraper instance per album
- LLM-based album matching

### Docker Support (~12 commits)
- Initial Dockerfile creation
- Image size optimization
- Permission fixes
- Container volume configuration

### Tidal Updates (~3 commits)
- New Tidal manifest implementation
- Legacy MQA removal
- Manifest merge PR

### Concurrency (~4 commits)
- Client login locking
- CLI progress update locking
- Download completion waiting
- Semaphore code cleanup

### Favorites Feature (~3 commits)
- Album download from favorite tracks
- Deezer URL fixes for favorites

### Quality Fallback (~5 commits)
- Lower quality fallback implementation
- Static quality approach changes
- Size map fixes
- Test improvements

### Metadata & Misc (~10+ commits)
- Audio validation
- Streaming pipeline improvements
- README updates
- Workflow/config removal

---

## Conclusion

The omnunum fork contains substantial improvements that would benefit your streamrip fork. The recommended approach is a hybrid merge strategy, starting with an attempted full merge, then selectively resolving conflicts to include the features you want.

**Priority Features to Include:**
1. Tidal manifest updates (essential for Tidal support)
2. Quality fallback system
3. Metadata enhancements
4. Concurrency improvements
5. Favorites downloading

**Optional Features:**
1. Docker support
2. RYM integration (requires additional infrastructure)

The merge will require careful conflict resolution, especially in the client and metadata modules, but the improvements are well worth the effort.
