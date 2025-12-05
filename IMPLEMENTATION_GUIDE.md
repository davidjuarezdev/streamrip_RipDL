# StreamRip Feature Implementation Guide

**Document Version:** 1.0
**Date:** 2025-11-23
**Status:** Technical Specification
**Companion to:** FEATURE_RECOMMENDATIONS.md

This document provides detailed implementation guidance, technical architecture, database schemas, and production-ready specifications for the features outlined in FEATURE_RECOMMENDATIONS.md.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Database Schema Extensions](#database-schema-extensions)
4. [API Specifications](#api-specifications)
5. [Configuration Schema](#configuration-schema)
6. [Implementation Priority & Dependencies](#implementation-priority--dependencies)
7. [Performance Considerations](#performance-considerations)
8. [Security Considerations](#security-considerations)
9. [Testing Strategy](#testing-strategy)
10. [Migration & Backward Compatibility](#migration--backward-compatibility)
11. [Production-Ready Code Examples](#production-ready-code-examples)

---

## Executive Summary

### Feature Count by Category

| Category | Feature Count | Priority Distribution |
|----------|---------------|----------------------|
| Download Management | 12 | Tier 1: 3, Tier 2: 5, Tier 3: 4 |
| Library Management | 15 | Tier 1: 4, Tier 2: 6, Tier 3: 5 |
| Search & Discovery | 8 | Tier 1: 2, Tier 2: 4, Tier 3: 2 |
| Quality Assurance | 10 | Tier 1: 3, Tier 2: 5, Tier 3: 2 |
| Statistics & Analytics | 12 | Tier 1: 2, Tier 2: 4, Tier 3: 6 |
| Audio Processing | 8 | Tier 2: 3, Tier 3: 5 |
| Interfaces & UX | 6 | Tier 2: 2, Tier 3: 4 |
| Automation | 9 | Tier 1: 1, Tier 2: 5, Tier 3: 3 |
| Security & Privacy | 5 | Tier 2: 2, Tier 3: 3 |
| Integration | 8 | Tier 2: 3, Tier 3: 5 |
| Developer Tools | 7 | Tier 3: 4, Tier 4: 3 |
| **Total** | **100+** | **Tier 1: 15, Tier 2: 39, Tier 3: 43, Tier 4: 10** |

### Estimated Development Effort

- **Tier 1 Features:** ~6-9 months (2-3 developers)
- **Tier 2 Features:** ~12-18 months (3-4 developers)
- **Tier 3 Features:** ~18-24 months (4-5 developers)
- **Tier 4 Features:** ~12-18 months (2-3 developers, research-heavy)

---

## Architecture Overview

### Current Architecture

```
streamrip/
├── rip/              # CLI interface
│   ├── cli.py       # Click commands
│   ├── main.py      # Main orchestration
│   └── parse_url.py # URL parsing
├── client/          # Source clients
│   ├── qobuz.py
│   ├── tidal.py
│   ├── deezer.py
│   └── soundcloud.py
├── media/           # Media handlers
│   ├── track.py
│   ├── album.py
│   └── playlist.py
├── metadata/        # Metadata handling
├── config.py        # Configuration
└── db.py            # Database
```

### Proposed Enhanced Architecture

```
streamrip/
├── api/                    # NEW: REST/GraphQL APIs
│   ├── rest/
│   │   ├── routes/
│   │   ├── middleware/
│   │   └── server.py
│   ├── graphql/
│   │   ├── schema.py
│   │   ├── resolvers.py
│   │   └── server.py
│   └── websocket/
│       └── progress.py
├── automation/             # NEW: Rules & scheduling
│   ├── rules_engine.py
│   ├── scheduler.py
│   ├── workflows.py
│   └── watch_lists.py
├── analytics/              # NEW: Statistics & insights
│   ├── stats.py
│   ├── insights.py
│   ├── reports.py
│   └── visualizations.py
├── audio/                  # NEW: Audio processing
│   ├── analysis.py
│   ├── replaygain.py
│   ├── spectral.py
│   └── repair.py
├── library/                # NEW: Library management
│   ├── scanner.py
│   ├── deduplicator.py
│   ├── organizer.py
│   └── importer.py
├── quality/                # NEW: Quality assurance
│   ├── validator.py
│   ├── checker.py
│   └── verifier.py
├── sync/                   # NEW: Cloud sync
│   ├── providers/
│   ├── sync_engine.py
│   └── conflict_resolver.py
├── plugins/                # NEW: Plugin system
│   ├── manager.py
│   ├── loader.py
│   └── base.py
├── web/                    # NEW: Web UI
│   ├── frontend/
│   ├── backend/
│   └── templates/
├── hooks/                  # NEW: Event system
│   ├── events.py
│   └── handlers.py
├── queue/                  # ENHANCED: Queue management
│   ├── manager.py
│   ├── priority.py
│   └── optimizer.py
├── db/                     # ENHANCED: Multiple DBs
│   ├── downloads.py
│   ├── analytics.py
│   ├── library.py
│   ├── queue.py
│   └── migrations/
├── rip/                    # EXISTING: CLI (enhanced)
├── client/                 # EXISTING: Source clients
├── media/                  # EXISTING: Media handlers
├── metadata/               # EXISTING: Metadata
└── config.py               # ENHANCED: Config
```

---

## Database Schema Extensions

### Current Schema

```sql
-- downloads table
CREATE TABLE downloads (
    id TEXT UNIQUE NOT NULL
);

-- failed_downloads table
CREATE TABLE failed_downloads (
    source TEXT NOT NULL,
    media_type TEXT NOT NULL,
    id TEXT UNIQUE NOT NULL
);
```

### Enhanced Schema

#### 1. Downloads Table (Enhanced)

```sql
CREATE TABLE downloads (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    media_type TEXT NOT NULL,  -- track, album, playlist, artist, label
    title TEXT,
    artist TEXT,
    album TEXT,
    quality INTEGER,  -- 0-4
    bit_depth INTEGER,
    sampling_rate INTEGER,
    codec TEXT,  -- FLAC, MP3, AAC, etc.
    file_size INTEGER,  -- bytes
    file_path TEXT,
    download_timestamp INTEGER,  -- Unix timestamp
    download_duration INTEGER,  -- seconds
    success BOOLEAN DEFAULT TRUE,
    retry_count INTEGER DEFAULT 0,

    -- NEW: Metadata
    genre TEXT,
    year INTEGER,
    label TEXT,
    isrc TEXT,

    -- NEW: Analytics
    checksum TEXT,  -- MD5/SHA256
    version INTEGER DEFAULT 1,  -- For tracking re-downloads

    UNIQUE(id)
);

CREATE INDEX idx_downloads_timestamp ON downloads(download_timestamp);
CREATE INDEX idx_downloads_source ON downloads(source);
CREATE INDEX idx_downloads_artist ON downloads(artist);
CREATE INDEX idx_downloads_genre ON downloads(genre);
CREATE INDEX idx_downloads_quality ON downloads(quality);
```

#### 2. Download Queue Table

```sql
CREATE TABLE download_queue (
    queue_id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    source TEXT NOT NULL,
    media_type TEXT NOT NULL,
    item_id TEXT,

    -- Priority & scheduling
    priority INTEGER DEFAULT 5,  -- 1-10, higher = more priority
    scheduled_time INTEGER,  -- Unix timestamp, NULL = immediate
    depends_on TEXT,  -- queue_id of prerequisite

    -- Status
    status TEXT DEFAULT 'pending',  -- pending, downloading, completed, failed, cancelled
    progress REAL DEFAULT 0.0,  -- 0.0 - 1.0

    -- Configuration overrides
    quality_override INTEGER,
    codec_override TEXT,
    folder_override TEXT,

    -- Timestamps
    created_at INTEGER NOT NULL,
    started_at INTEGER,
    completed_at INTEGER,

    -- Error handling
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_error TEXT,

    FOREIGN KEY (depends_on) REFERENCES download_queue(queue_id)
);

CREATE INDEX idx_queue_status ON download_queue(status);
CREATE INDEX idx_queue_priority ON download_queue(priority DESC);
CREATE INDEX idx_queue_scheduled ON download_queue(scheduled_time);
```

#### 3. Library Catalog Table

```sql
CREATE TABLE library_catalog (
    catalog_id TEXT PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,

    -- Basic metadata
    title TEXT NOT NULL,
    artist TEXT,
    album TEXT,
    album_artist TEXT,
    track_number INTEGER,
    disc_number INTEGER,

    -- Audio properties
    duration REAL,  -- seconds
    bit_depth INTEGER,
    sampling_rate INTEGER,
    bitrate INTEGER,
    codec TEXT,
    file_size INTEGER,

    -- Additional metadata
    genre TEXT,
    year INTEGER,
    label TEXT,
    isrc TEXT,
    composer TEXT,

    -- Quality indicators
    has_artwork BOOLEAN DEFAULT FALSE,
    artwork_resolution TEXT,
    is_lossless BOOLEAN,
    dynamic_range REAL,  -- DR meter value
    quality_score INTEGER,  -- 0-100

    -- Flags
    is_transcoded BOOLEAN DEFAULT FALSE,
    is_upsampled BOOLEAN DEFAULT FALSE,
    has_issues BOOLEAN DEFAULT FALSE,
    issue_description TEXT,

    -- Timestamps
    added_at INTEGER NOT NULL,
    last_scanned INTEGER,
    last_modified INTEGER,

    -- Checksums
    file_md5 TEXT,
    audio_fingerprint TEXT,  -- Chromaprint/AcoustID

    -- Source tracking
    download_id TEXT,
    source TEXT,

    FOREIGN KEY (download_id) REFERENCES downloads(id)
);

CREATE INDEX idx_catalog_artist ON library_catalog(artist);
CREATE INDEX idx_catalog_album ON library_catalog(album);
CREATE INDEX idx_catalog_genre ON library_catalog(genre);
CREATE INDEX idx_catalog_fingerprint ON library_catalog(audio_fingerprint);
CREATE UNIQUE INDEX idx_catalog_path ON library_catalog(file_path);
```

#### 4. Statistics Table

```sql
CREATE TABLE download_stats (
    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,  -- YYYY-MM-DD

    -- Counts
    total_downloads INTEGER DEFAULT 0,
    successful_downloads INTEGER DEFAULT 0,
    failed_downloads INTEGER DEFAULT 0,

    -- By source
    qobuz_count INTEGER DEFAULT 0,
    tidal_count INTEGER DEFAULT 0,
    deezer_count INTEGER DEFAULT 0,
    soundcloud_count INTEGER DEFAULT 0,

    -- By quality
    quality_0_count INTEGER DEFAULT 0,
    quality_1_count INTEGER DEFAULT 0,
    quality_2_count INTEGER DEFAULT 0,
    quality_3_count INTEGER DEFAULT 0,
    quality_4_count INTEGER DEFAULT 0,

    -- Data transfer
    total_bytes INTEGER DEFAULT 0,
    total_duration REAL DEFAULT 0,  -- seconds

    UNIQUE(date)
);

CREATE INDEX idx_stats_date ON download_stats(date);
```

#### 5. Watch Lists Table

```sql
CREATE TABLE watch_lists (
    watch_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- artist, label, playlist
    source TEXT NOT NULL,
    item_id TEXT NOT NULL,
    name TEXT NOT NULL,

    -- Settings
    auto_download BOOLEAN DEFAULT FALSE,
    quality_preference INTEGER,
    notification_enabled BOOLEAN DEFAULT TRUE,

    -- Tracking
    last_checked INTEGER,
    last_found_item_id TEXT,
    last_download_timestamp INTEGER,

    -- Stats
    total_items_found INTEGER DEFAULT 0,
    total_items_downloaded INTEGER DEFAULT 0,

    created_at INTEGER NOT NULL,

    UNIQUE(source, type, item_id)
);

CREATE INDEX idx_watch_type ON watch_lists(type);
CREATE INDEX idx_watch_source ON watch_lists(source);
```

#### 6. Automation Rules Table

```sql
CREATE TABLE automation_rules (
    rule_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    enabled BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 5,  -- Execution order

    -- Match conditions (JSON)
    match_conditions TEXT NOT NULL,  -- JSON: {genre: "Jazz", quality: ">=3"}

    -- Actions (JSON)
    actions TEXT NOT NULL,  -- JSON: {quality: 4, source: "qobuz"}

    -- Statistics
    times_triggered INTEGER DEFAULT 0,
    last_triggered INTEGER,

    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX idx_rules_enabled ON automation_rules(enabled);
CREATE INDEX idx_rules_priority ON automation_rules(priority DESC);
```

#### 7. Duplicates Table

```sql
CREATE TABLE duplicates (
    duplicate_id TEXT PRIMARY KEY,
    group_hash TEXT NOT NULL,  -- Hash of normalized artist+title

    -- File references
    file_paths TEXT NOT NULL,  -- JSON array of file paths
    catalog_ids TEXT NOT NULL,  -- JSON array of catalog_ids

    -- Duplicate info
    duplicate_count INTEGER NOT NULL,
    best_quality_index INTEGER,  -- Index of highest quality version

    -- Similarity
    similarity_score REAL,  -- 0.0 - 1.0
    match_method TEXT,  -- metadata, fingerprint, both

    -- Status
    resolved BOOLEAN DEFAULT FALSE,
    resolution_action TEXT,  -- kept_all, kept_best, manual

    detected_at INTEGER NOT NULL,
    resolved_at INTEGER
);

CREATE INDEX idx_duplicates_hash ON duplicates(group_hash);
CREATE INDEX idx_duplicates_resolved ON duplicates(resolved);
```

#### 8. Sessions Table (for resume/pause)

```sql
CREATE TABLE download_sessions (
    session_id TEXT PRIMARY KEY,
    session_name TEXT,

    -- State
    status TEXT DEFAULT 'active',  -- active, paused, completed, failed

    -- Progress tracking
    total_items INTEGER NOT NULL,
    completed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,

    -- Resume data (JSON)
    resume_data TEXT,  -- JSON: partial downloads, byte offsets, etc.

    -- Timestamps
    created_at INTEGER NOT NULL,
    started_at INTEGER,
    paused_at INTEGER,
    resumed_at INTEGER,
    completed_at INTEGER
);

CREATE INDEX idx_sessions_status ON download_sessions(status);
```

---

## API Specifications

### REST API Endpoints

#### Base URL: `/api/v1`

#### Authentication
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user",
  "password": "pass"
}

Response:
{
  "token": "jwt-token-here",
  "expires_in": 3600
}
```

#### Downloads

```http
# Queue a download
POST /api/v1/download
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://qobuz.com/album/...",
  "quality": 3,
  "priority": 5,
  "scheduled_time": null,
  "codec": "FLAC"
}

Response:
{
  "queue_id": "uuid",
  "status": "pending",
  "estimated_size": "450 MB",
  "estimated_duration": 225
}

# Get download status
GET /api/v1/download/{queue_id}

Response:
{
  "queue_id": "uuid",
  "status": "downloading",
  "progress": 0.45,
  "current_item": "Track 5 of 12",
  "bytes_downloaded": 210000000,
  "bytes_total": 470000000,
  "speed": "5.2 MB/s",
  "eta": 120
}

# List downloads
GET /api/v1/downloads?status=active&limit=50&offset=0

Response:
{
  "items": [...],
  "total": 150,
  "page": 1,
  "pages": 3
}

# Cancel download
DELETE /api/v1/download/{queue_id}

Response:
{
  "success": true,
  "message": "Download cancelled"
}

# Pause/Resume
POST /api/v1/download/{queue_id}/pause
POST /api/v1/download/{queue_id}/resume
```

#### Library

```http
# Get library stats
GET /api/v1/library/stats

Response:
{
  "total_tracks": 1247,
  "total_albums": 152,
  "total_artists": 87,
  "total_size": 48234567890,
  "total_duration": 4023456,
  "by_source": {
    "qobuz": 834,
    "tidal": 312,
    "deezer": 101
  },
  "by_quality": {
    "0": 45,
    "1": 123,
    "2": 456,
    "3": 521,
    "4": 102
  }
}

# Search library
GET /api/v1/library/search?q=miles+davis&type=album

Response:
{
  "results": [
    {
      "catalog_id": "uuid",
      "title": "Kind of Blue",
      "artist": "Miles Davis",
      "album": "Kind of Blue",
      "year": 1959,
      "quality": "24-bit/96kHz",
      "file_path": "/path/to/file.flac",
      "artwork_url": "/api/v1/artwork/uuid"
    }
  ],
  "count": 1
}

# Scan library
POST /api/v1/library/scan
Content-Type: application/json

{
  "path": "/path/to/music",
  "recursive": true,
  "update_existing": false
}

Response:
{
  "scan_id": "uuid",
  "status": "scanning",
  "files_found": 0
}
```

#### Search (Streaming Services)

```http
# Search across sources
GET /api/v1/search?q=radiohead&sources=qobuz,tidal&type=album

Response:
{
  "results": {
    "qobuz": [
      {
        "id": "album-id",
        "title": "OK Computer",
        "artist": "Radiohead",
        "year": 1997,
        "quality_available": [2, 3, 4],
        "label": "Parlophone"
      }
    ],
    "tidal": [...]
  },
  "total": 24
}
```

#### Statistics

```http
# Get download statistics
GET /api/v1/stats/downloads?period=30d

Response:
{
  "period": "30d",
  "total_downloads": 234,
  "total_size": 10234567890,
  "average_quality": 3.2,
  "most_downloaded_artist": "Miles Davis",
  "downloads_by_day": [
    {"date": "2024-01-01", "count": 8},
    {"date": "2024-01-02", "count": 12}
  ],
  "downloads_by_source": {
    "qobuz": 156,
    "tidal": 67,
    "deezer": 11
  }
}

# Get insights
GET /api/v1/stats/insights

Response:
{
  "insights": [
    {
      "type": "preference",
      "message": "You prefer 1970s music (32% of library)"
    },
    {
      "type": "quality",
      "message": "78% of your library is lossless"
    },
    {
      "type": "prediction",
      "message": "Predicted storage in 1 year: 850GB"
    }
  ]
}
```

#### Health Check

```http
GET /api/v1/health

Response:
{
  "status": "healthy",
  "version": "2.1.0",
  "uptime": 123456,
  "checks": {
    "database": "ok",
    "storage": "ok",
    "qobuz": "authenticated",
    "tidal": "token_expires_soon",
    "deezer": "authenticated",
    "soundcloud": "ok"
  },
  "warnings": [
    "Tidal token expires in 2 days"
  ]
}
```

### WebSocket API

```javascript
// Connection
const ws = new WebSocket('ws://localhost:8080/ws/progress?token=jwt-token');

// Subscribe to download progress
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'download',
  queue_id: 'uuid'
}));

// Receive updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  /*
  {
    type: 'progress',
    queue_id: 'uuid',
    progress: 0.67,
    current_item: 'Track 8 of 12',
    speed: '5.2 MB/s',
    eta: 45
  }
  */
};

// Subscribe to global stats
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'stats'
}));
```

### GraphQL Schema

```graphql
type Query {
  # Library queries
  library(filter: LibraryFilter, sort: SortOptions, limit: Int, offset: Int): LibraryResult!
  track(id: ID!): Track
  album(id: ID!): Album
  artist(name: String!): Artist

  # Download queries
  downloads(status: DownloadStatus, limit: Int): [Download!]!
  download(queueId: ID!): Download
  queue: [QueueItem!]!

  # Search queries
  search(query: String!, sources: [Source!], type: MediaType!): SearchResults!

  # Stats queries
  stats(period: TimePeriod): Statistics!
  insights: [Insight!]!

  # Config queries
  config: Config!
  sources: [SourceConfig!]!
}

type Mutation {
  # Download mutations
  queueDownload(input: DownloadInput!): QueueItem!
  cancelDownload(queueId: ID!): Boolean!
  pauseDownload(queueId: ID!): Boolean!
  resumeDownload(queueId: ID!): Boolean!
  retryDownload(queueId: ID!): Boolean!

  # Library mutations
  scanLibrary(path: String!, recursive: Boolean): ScanJob!
  updateMetadata(catalogId: ID!, metadata: MetadataInput!): Track!
  deleteFromLibrary(catalogId: ID!): Boolean!

  # Config mutations
  updateConfig(input: ConfigInput!): Config!
  updateSourceConfig(source: Source!, input: SourceConfigInput!): SourceConfig!
}

type Subscription {
  # Real-time updates
  downloadProgress(queueId: ID!): DownloadProgress!
  queueUpdates: QueueUpdate!
  statsUpdates: StatsUpdate!
}

type Download {
  queueId: ID!
  url: String!
  source: Source!
  mediaType: MediaType!
  status: DownloadStatus!
  progress: Float!
  currentItem: String
  bytesDownloaded: Int!
  bytesTotal: Int
  speed: String
  eta: Int
  error: String
  createdAt: DateTime!
  startedAt: DateTime
  completedAt: DateTime
}

type Track {
  catalogId: ID!
  title: String!
  artist: String!
  album: String
  albumArtist: String
  trackNumber: Int
  discNumber: Int
  duration: Float!
  quality: Quality!
  codec: String!
  fileSize: Int!
  filePath: String!
  genre: String
  year: Int
  label: String
  hasArtwork: Boolean!
  artworkUrl: String
  isLossless: Boolean!
  dynamicRange: Float
  qualityScore: Int
  addedAt: DateTime!
}

type Statistics {
  totalTracks: Int!
  totalAlbums: Int!
  totalArtists: Int!
  totalSize: Int!
  totalDuration: Int!
  bySource: SourceStats!
  byQuality: QualityStats!
  byGenre: [GenreCount!]!
  timeline: [TimelinePoint!]!
}

enum DownloadStatus {
  PENDING
  DOWNLOADING
  COMPLETED
  FAILED
  CANCELLED
  PAUSED
}

enum Source {
  QOBUZ
  TIDAL
  DEEZER
  SOUNDCLOUD
}

enum MediaType {
  TRACK
  ALBUM
  PLAYLIST
  ARTIST
  LABEL
}

input DownloadInput {
  url: String!
  quality: Int
  priority: Int
  scheduledTime: DateTime
  codec: String
}

input LibraryFilter {
  artist: String
  album: String
  genre: String
  yearRange: YearRangeInput
  quality: QualityFilter
  isLossless: Boolean
}
```

---

## Configuration Schema

### Enhanced config.toml Structure

```toml
[downloads]
folder = "~/StreamripDownloads"
source_subdirectories = false
disc_subdirectories = true
concurrency = true
max_connections = 6
requests_per_minute = 60
verify_ssl = true

# NEW: Resume/retry settings
enable_resume = true
resume_chunk_size = 1048576  # 1MB chunks
max_retries = 3
retry_delay_base = 2
retry_on_errors = ["timeout", "connection", "503", "429"]
skip_on_errors = ["404", "403"]

# NEW: Bandwidth management
bandwidth_limit = 0  # 0 = unlimited, in MB/s
bandwidth_schedule = []  # e.g., [{time_range = "08:00-18:00", limit = 1}]

# NEW: Session management
enable_sessions = true
auto_resume_on_start = true

[queue]
# NEW: Queue management
enabled = true
default_priority = 5
optimize_order = true
optimization_strategy = "source-batching"  # size-first, quality-first, source-batching
max_queue_size = 1000

[database]
downloads_enabled = true
downloads_path = "~/.streamrip/downloads.db"
failed_downloads_enabled = true
failed_downloads_path = "~/.streamrip/failed_downloads.db"

# NEW: Additional databases
library_catalog_enabled = true
library_catalog_path = "~/.streamrip/library.db"
analytics_enabled = true
analytics_path = "~/.streamrip/analytics.db"
queue_path = "~/.streamrip/queue.db"

[library]
# NEW: Library management
auto_scan = false
scan_on_download = true
watch_folders = []
enable_duplicate_detection = true
duplicate_threshold = 0.85

[statistics]
# NEW: Statistics tracking
enabled = true
track_download_stats = true
track_listening_stats = false  # Requires scrobbling setup
retention_days = 365  # 0 = forever

[automation]
# NEW: Automation engine
enabled = false
rules_path = "~/.streamrip/rules.toml"

[[automation.rules]]
name = "High-Res Classical"
enabled = true
priority = 10
match = {genre = "Classical"}
action = {min_quality = 4, source = "qobuz"}

[watch_lists]
# NEW: Artist/label monitoring
enabled = false
check_interval = "daily"  # hourly, daily, weekly
auto_download = false
notification_enabled = true

[playlist]
# NEW: Playlist syncing
auto_sync = false
sync_interval = "weekly"
watched_playlists = []

[audio_processing]
# NEW: Audio processing
auto_replaygain = false
replaygain_mode = "album"
target_loudness = -14
auto_analyze = false  # BPM, key, etc.

[quality_assurance]
# NEW: Quality checks
verify_downloads = true
check_integrity = true
detect_transcodes = false
detect_upsampling = false
flag_suspicious = true

[api]
# NEW: API server
enabled = false
host = "127.0.0.1"
port = 8080
enable_websocket = true
enable_graphql = false
auth_required = true
cors_enabled = false
cors_origins = ["http://localhost:3000"]

[webui]
# NEW: Web interface
enabled = false
port = 8081
theme = "dark"
open_browser_on_start = true

[sync]
# NEW: Cloud sync
enabled = false
provider = "s3"  # s3, dropbox, google-drive, nextcloud
sync_database = true
sync_config = true
sync_metadata_only = false

[security]
# NEW: Security settings
encrypt_library = false
encryption_method = "aes-256"
vpn_required = false
anonymous_mode = false

[plugins]
# NEW: Plugin system
enabled = false
auto_update = true
plugin_directories = ["~/.streamrip/plugins"]

[hooks]
# NEW: Event hooks
enabled = false
before_download = ""
after_download = ""
on_failure = ""
on_complete = ""

[notifications]
# NEW: Notifications
enabled = false
email_enabled = false
email_smtp_host = ""
email_smtp_port = 587
email_from = ""
email_to = ""
desktop_enabled = true
webhook_url = ""

[cli]
text_output = true
progress_bars = true
max_search_results = 100
# NEW
interactive_mode = false
color_output = true
confirm_deletes = true

[misc]
version = "2.0.6"
check_for_updates = true
# NEW
telemetry_enabled = false  # Anonymous usage stats
debug_mode = false
log_level = "INFO"
log_file = "~/.streamrip/streamrip.log"
```

---

## Implementation Priority & Dependencies

### Dependency Graph

```
Level 1 (Foundation - No Dependencies):
├── Database Schema Extensions
├── Enhanced Configuration System
├── Logging & Error Handling Improvements
└── Basic Statistics Collection

Level 2 (Core Features - Depends on Level 1):
├── Resume/Pause System → Database, Config
├── Smart Retry System → Database, Config
├── Queue Management → Database, Config
├── Download Statistics → Database
├── File Verification → None
└── Health Monitoring → Database, Config

Level 3 (Enhanced Features - Depends on Level 1-2):
├── Library Catalog → Database, Queue
├── Duplicate Detection → Library Catalog
├── Watch Lists → Queue, Database
├── Automation Rules → Queue, Config
├── Playlist Syncing → Queue
└── Advanced Search → Library Catalog

Level 4 (Advanced Features - Depends on Level 1-3):
├── Web UI → API, Library, Statistics
├── REST API → Queue, Library, Statistics
├── Audio Analysis → Library Catalog
├── Quality Analysis → Library Catalog
├── ReplayGain → Audio Analysis
└── Analytics Dashboard → Statistics

Level 5 (Integration - Depends on Level 1-4):
├── Plugin System → API, Hooks
├── Cloud Sync → Library, Database
├── Backup System → Library
├── GraphQL API → REST API, Library
└── ML Recommendations → Analytics, Library

Level 6 (Advanced Intelligence - Depends on All):
├── AI Organization → ML, Library
├── Community Features → API, Analytics
├── Voice Control → API
└── Distributed Downloads → Sync, Queue
```

### Implementation Sequence (Tier 1 Focus)

**Sprint 1-2: Foundation (Weeks 1-4)**
- Database schema migrations
- Enhanced configuration system
- Improved error handling
- Basic logging framework

**Sprint 3-4: Resume/Pause (Weeks 5-8)**
- Session management
- Checkpoint system
- Resume logic
- CLI commands

**Sprint 5-6: Smart Retry (Weeks 9-12)**
- Retry configuration
- Exponential backoff
- Error classification
- Retry statistics

**Sprint 7-8: Queue System (Weeks 13-16)**
- Queue database
- Priority management
- Queue optimization
- CLI commands

**Sprint 9-10: Statistics (Weeks 17-20)**
- Statistics collection
- Database queries
- CLI statistics commands
- Export functionality

**Sprint 11-12: Verification (Weeks 21-24)**
- File integrity checks
- FFmpeg integration
- Verification reports
- Auto-fix system

---

## Performance Considerations

### Database Performance

**Indexes Required:**
```sql
-- High-traffic queries
CREATE INDEX idx_downloads_composite ON downloads(source, download_timestamp);
CREATE INDEX idx_queue_status_priority ON download_queue(status, priority DESC);
CREATE INDEX idx_catalog_artist_album ON library_catalog(artist, album);

-- Analytics queries
CREATE INDEX idx_downloads_stats ON downloads(download_timestamp, source, quality);
CREATE INDEX idx_catalog_quality ON library_catalog(bit_depth, sampling_rate);
```

**Query Optimization:**
- Use prepared statements for all database queries
- Implement connection pooling (SQLite with WAL mode)
- Batch inserts for statistics (insert every N downloads, not per download)
- Use transactions for multi-step operations
- Consider read replicas for analytics queries

**Database Sharding:**
- Separate databases: downloads, library, analytics, queue
- Reduces lock contention
- Allows independent scaling
- Enables selective backups

### API Performance

**Caching Strategy:**
```python
# Redis cache for hot data
cache_config = {
    'library_stats': 60,  # 1 minute TTL
    'download_status': 5,  # 5 seconds TTL
    'search_results': 300,  # 5 minutes TTL
    'health_check': 30,  # 30 seconds TTL
}
```

**Rate Limiting:**
```python
# Per-endpoint rate limits
rate_limits = {
    '/api/v1/download': '100/hour',  # Queue downloads
    '/api/v1/search': '60/minute',  # Search queries
    '/api/v1/library': '300/minute',  # Library access
}
```

**Pagination:**
- Default page size: 50 items
- Maximum page size: 200 items
- Use cursor-based pagination for large datasets

### Async Processing

**Task Queue (using Celery or similar):**
```python
# Background tasks
@celery.task
async def scan_library(path):
    """Async library scanning"""
    pass

@celery.task
async def analyze_audio(file_path):
    """Async audio analysis"""
    pass

@celery.task
async def generate_spectrograms(file_path):
    """Async spectrogram generation"""
    pass
```

### Memory Management

**Streaming Downloads:**
```python
# Stream files to disk, don't load in memory
async def download_file(url, path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            with open(path, 'wb') as f:
                async for chunk in resp.content.iter_chunked(1024 * 1024):  # 1MB chunks
                    f.write(chunk)
```

**Memory Limits:**
- Library scan: Process files in batches of 100
- Duplicate detection: Compare in chunks
- Statistics: Aggregate incrementally

---

## Security Considerations

### Authentication & Authorization

**JWT Token Structure:**
```json
{
  "user_id": "uuid",
  "username": "user",
  "permissions": ["download", "library:read", "library:write", "admin"],
  "exp": 1234567890,
  "iat": 1234567890
}
```

**Password Hashing:**
```python
from passlib.hash import bcrypt

# Store hashed passwords
hashed = bcrypt.hash(password)

# Verify
bcrypt.verify(password, hashed)
```

### API Security

**Request Validation:**
```python
from pydantic import BaseModel, validator

class DownloadRequest(BaseModel):
    url: str
    quality: int = 3

    @validator('url')
    def validate_url(cls, v):
        # Validate URL format
        # Whitelist domains (qobuz, tidal, deezer, soundcloud)
        return v

    @validator('quality')
    def validate_quality(cls, v):
        if v not in range(5):
            raise ValueError('Quality must be 0-4')
        return v
```

**SQL Injection Prevention:**
```python
# Always use parameterized queries
cursor.execute("SELECT * FROM downloads WHERE id = ?", (track_id,))

# NEVER use f-strings with user input
# BAD: cursor.execute(f"SELECT * FROM downloads WHERE id = '{track_id}'")
```

**Path Traversal Prevention:**
```python
from pathlib import Path

def safe_path_join(base, user_input):
    base_path = Path(base).resolve()
    target_path = (base_path / user_input).resolve()

    # Ensure target is within base
    if not str(target_path).startswith(str(base_path)):
        raise SecurityError("Path traversal attempt detected")

    return target_path
```

### Encryption

**Library Encryption:**
```python
from cryptography.fernet import Fernet

def encrypt_file(file_path, key):
    f = Fernet(key)
    with open(file_path, 'rb') as file:
        file_data = file.read()
    encrypted = f.encrypt(file_data)
    with open(file_path + '.enc', 'wb') as file:
        file.write(encrypted)
```

**Credential Storage:**
```python
import keyring

# Store sensitive credentials in system keyring
keyring.set_password("streamrip", "qobuz_password", password)

# Retrieve
password = keyring.get_password("streamrip", "qobuz_password")
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_retry_system.py
import pytest
from streamrip.download import RetryManager

@pytest.mark.asyncio
async def test_exponential_backoff():
    manager = RetryManager(max_retries=3, base_delay=1)

    delays = []
    for i in range(3):
        delay = manager.get_retry_delay(i)
        delays.append(delay)

    assert delays == [1, 2, 4]

@pytest.mark.asyncio
async def test_retry_on_timeout():
    manager = RetryManager(retry_on=["timeout"])

    assert manager.should_retry("timeout") == True
    assert manager.should_retry("404") == False

# tests/test_queue.py
@pytest.mark.asyncio
async def test_queue_priority():
    queue = DownloadQueue()

    await queue.add("url1", priority=5)
    await queue.add("url2", priority=10)
    await queue.add("url3", priority=1)

    next_item = await queue.get_next()
    assert next_item.priority == 10  # Highest priority
```

### Integration Tests

```python
# tests/integration/test_download_flow.py
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_download_flow():
    """Test complete download flow from queue to completion"""
    async with Main(test_config) as main:
        # Queue download
        queue_id = await main.queue_download("https://test.url")

        # Check queue
        status = await main.get_queue_status(queue_id)
        assert status['status'] == 'pending'

        # Process queue
        await main.process_queue()

        # Verify completion
        status = await main.get_queue_status(queue_id)
        assert status['status'] == 'completed'

        # Check database
        assert main.database.downloaded("test-id")

        # Check file exists
        assert os.path.exists("/path/to/downloaded/file.flac")
```

### Load Testing

```python
# tests/load/test_api_performance.py
import locust

class StreamripUser(locust.HttpUser):
    wait_time = locust.between(1, 3)

    @locust.task(3)
    def search(self):
        self.client.get("/api/v1/search?q=test&sources=qobuz")

    @locust.task(2)
    def get_stats(self):
        self.client.get("/api/v1/stats/downloads?period=30d")

    @locust.task(1)
    def queue_download(self):
        self.client.post("/api/v1/download", json={
            "url": "https://test.url",
            "quality": 3
        })

# Run: locust -f test_api_performance.py --users 100 --spawn-rate 10
```

### Test Coverage Goals

- Unit tests: >80% coverage
- Integration tests: Critical paths covered
- E2E tests: Main user workflows
- Performance tests: API endpoints < 100ms p95
- Load tests: Support 1000 concurrent users

---

## Migration & Backward Compatibility

### Database Migration Strategy

```python
# streamrip/db/migrations/001_add_enhanced_downloads.py
from typing import Tuple

def upgrade(conn) -> None:
    """Upgrade to version 001"""
    # Add new columns to downloads table
    conn.execute("""
        ALTER TABLE downloads ADD COLUMN source TEXT;
    """)
    conn.execute("""
        ALTER TABLE downloads ADD COLUMN media_type TEXT;
    """)
    # ... etc

    # Create new tables
    conn.execute("""
        CREATE TABLE download_queue (
            -- schema here
        );
    """)

    # Set version
    conn.execute("PRAGMA user_version = 1")

def downgrade(conn) -> None:
    """Downgrade from version 001"""
    # Reverse changes
    pass

def get_version() -> Tuple[int, str]:
    return (1, "Add enhanced downloads tracking")
```

**Migration Runner:**
```python
# streamrip/db/migrate.py
class DatabaseMigrator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    def get_current_version(self) -> int:
        cursor = self.conn.execute("PRAGMA user_version")
        return cursor.fetchone()[0]

    def migrate(self, target_version: int = None):
        current = self.get_current_version()
        migrations = self.get_migrations()

        if target_version is None:
            target_version = max(migrations.keys())

        for version in range(current + 1, target_version + 1):
            logger.info(f"Applying migration {version}")
            migration = migrations[version]
            migration.upgrade(self.conn)
            self.conn.commit()
```

### Config File Migration

```python
def migrate_config(old_config: dict, old_version: str, new_version: str) -> dict:
    """Migrate config from old version to new version"""
    new_config = copy.deepcopy(old_config)

    # Add new sections with defaults
    if 'queue' not in new_config:
        new_config['queue'] = {
            'enabled': True,
            'default_priority': 5,
            'optimize_order': True
        }

    if 'library' not in new_config:
        new_config['library'] = {
            'auto_scan': False,
            'scan_on_download': True,
            'watch_folders': []
        }

    # Migrate renamed fields
    if 'max_connections' in new_config['downloads']:
        new_config['downloads']['max_concurrent_downloads'] = \
            new_config['downloads'].pop('max_connections')

    # Update version
    new_config['misc']['version'] = new_version

    return new_config
```

### API Versioning

```python
# Support multiple API versions
@app.route('/api/v1/download', methods=['POST'])
def download_v1():
    # Version 1 implementation
    pass

@app.route('/api/v2/download', methods=['POST'])
def download_v2():
    # Version 2 with breaking changes
    pass

# Deprecation warnings
@app.route('/api/v1/stats', methods=['GET'])
@deprecated(version='v1', sunset_date='2025-12-31', new_endpoint='/api/v2/statistics')
def stats_v1():
    pass
```

---

## Production-Ready Code Examples

### 1. Resume/Pause Implementation

```python
# streamrip/session/session_manager.py
import asyncio
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict
import aiofiles

@dataclass
class SessionState:
    session_id: str
    status: str  # active, paused, completed
    current_item_index: int
    total_items: int
    partial_downloads: Dict[str, int]  # {track_id: bytes_downloaded}
    queue_state: list

class SessionManager:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.state_file = Path(config.app_dir) / "session_state.json"

    async def create_session(self, session_name: Optional[str] = None) -> str:
        """Create a new download session"""
        import uuid
        session_id = str(uuid.uuid4())

        await self.db.sessions.add({
            'session_id': session_id,
            'session_name': session_name,
            'status': 'active',
            'total_items': 0,
            'completed_items': 0,
            'created_at': int(time.time())
        })

        return session_id

    async def save_state(self, session: SessionState):
        """Save session state for resume"""
        async with aiofiles.open(self.state_file, 'w') as f:
            await f.write(json.dumps(asdict(session), indent=2))

        # Also save to database
        await self.db.sessions.update(
            session.session_id,
            resume_data=json.dumps(asdict(session))
        )

    async def load_state(self, session_id: str) -> Optional[SessionState]:
        """Load session state for resume"""
        session_data = await self.db.sessions.get(session_id)
        if not session_data or not session_data['resume_data']:
            return None

        data = json.loads(session_data['resume_data'])
        return SessionState(**data)

    async def pause_session(self, session_id: str):
        """Pause active session"""
        await self.db.sessions.update(
            session_id,
            status='paused',
            paused_at=int(time.time())
        )
        logger.info(f"Session {session_id} paused")

    async def resume_session(self, session_id: str) -> SessionState:
        """Resume paused session"""
        state = await self.load_state(session_id)
        if not state:
            raise ValueError(f"No saved state for session {session_id}")

        await self.db.sessions.update(
            session_id,
            status='active',
            resumed_at=int(time.time())
        )

        logger.info(f"Session {session_id} resumed from item {state.current_item_index}")
        return state


# streamrip/download/resumable.py
class ResumableDownload:
    """Handle resumable downloads with partial file support"""

    def __init__(self, url: str, output_path: str, session: aiohttp.ClientSession):
        self.url = url
        self.output_path = output_path
        self.partial_path = output_path + '.partial'
        self.session = session
        self.bytes_downloaded = 0

    async def download(self, resume_from: int = 0):
        """Download file with resume support"""
        headers = {}

        # Check if partial file exists
        if resume_from > 0 and Path(self.partial_path).exists():
            headers['Range'] = f'bytes={resume_from}-'
            self.bytes_downloaded = resume_from
            mode = 'ab'  # Append mode
            logger.info(f"Resuming download from byte {resume_from}")
        else:
            mode = 'wb'
            logger.info(f"Starting new download")

        try:
            async with self.session.get(self.url, headers=headers) as resp:
                # Check if server supports resume
                if resume_from > 0 and resp.status != 206:
                    logger.warning("Server doesn't support resume, starting over")
                    mode = 'wb'
                    self.bytes_downloaded = 0

                total_size = int(resp.headers.get('content-length', 0))

                async with aiofiles.open(self.partial_path, mode) as f:
                    async for chunk in resp.content.iter_chunked(1024 * 1024):  # 1MB chunks
                        await f.write(chunk)
                        self.bytes_downloaded += len(chunk)

                        # Yield progress
                        yield {
                            'bytes_downloaded': self.bytes_downloaded,
                            'total_bytes': total_size,
                            'progress': self.bytes_downloaded / total_size if total_size else 0
                        }

            # Download complete, rename to final filename
            Path(self.partial_path).rename(self.output_path)
            logger.info(f"Download complete: {self.output_path}")

        except asyncio.CancelledError:
            logger.info(f"Download cancelled at {self.bytes_downloaded} bytes")
            raise
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise
```

### 2. Queue Management System

```python
# streamrip/queue/manager.py
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
import heapq

class QueueStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

@dataclass
class QueueItem:
    queue_id: str
    url: str
    source: str
    media_type: str
    priority: int = 5  # 1-10, higher = more important
    scheduled_time: Optional[int] = None
    status: QueueStatus = QueueStatus.PENDING
    progress: float = 0.0
    quality_override: Optional[int] = None
    depends_on: Optional[str] = None

    def __lt__(self, other):
        # For heapq (min-heap), negate priority for max-heap behavior
        return -self.priority < -other.priority

class QueueManager:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.active_downloads: Dict[str, asyncio.Task] = {}
        self.max_concurrent = config.session.downloads.max_connections

        # Priority queue
        self._queue: List[QueueItem] = []
        self._lock = asyncio.Lock()

    async def add(self, url: str, **kwargs) -> str:
        """Add item to queue"""
        import uuid
        queue_id = str(uuid.uuid4())

        item = QueueItem(
            queue_id=queue_id,
            url=url,
            source=kwargs.get('source'),
            media_type=kwargs.get('media_type'),
            priority=kwargs.get('priority', 5),
            scheduled_time=kwargs.get('scheduled_time'),
            quality_override=kwargs.get('quality'),
            depends_on=kwargs.get('depends_on')
        )

        # Save to database
        await self.db.queue.add({
            'queue_id': queue_id,
            'url': url,
            'source': item.source,
            'media_type': item.media_type,
            'priority': item.priority,
            'scheduled_time': item.scheduled_time,
            'status': QueueStatus.PENDING.value,
            'quality_override': item.quality_override,
            'depends_on': item.depends_on,
            'created_at': int(time.time())
        })

        # Add to in-memory queue
        async with self._lock:
            heapq.heappush(self._queue, item)

        logger.info(f"Added {url} to queue with priority {item.priority}")
        return queue_id

    async def get_next(self) -> Optional[QueueItem]:
        """Get next item from queue respecting priorities and dependencies"""
        async with self._lock:
            while self._queue:
                item = heapq.heappop(self._queue)

                # Check if scheduled time has passed
                if item.scheduled_time:
                    if int(time.time()) < item.scheduled_time:
                        # Put back and skip
                        heapq.heappush(self._queue, item)
                        continue

                # Check dependencies
                if item.depends_on:
                    dep_status = await self.get_status(item.depends_on)
                    if dep_status != QueueStatus.COMPLETED:
                        # Dependency not ready, put back
                        heapq.heappush(self._queue, item)
                        continue

                return item

            return None

    async def process_queue(self):
        """Process queue with concurrency control"""
        while True:
            # Check if we can start more downloads
            if len(self.active_downloads) >= self.max_concurrent:
                await asyncio.sleep(1)
                continue

            # Get next item
            item = await self.get_next()
            if not item:
                # Queue empty, wait for new items
                await asyncio.sleep(5)
                continue

            # Start download
            task = asyncio.create_task(self._download_item(item))
            self.active_downloads[item.queue_id] = task

            # Cleanup completed tasks
            self._cleanup_completed()

    async def _download_item(self, item: QueueItem):
        """Download a single item"""
        try:
            await self.update_status(item.queue_id, QueueStatus.DOWNLOADING)

            # Actual download logic
            async with Main(self.config) as main:
                await main.add(item.url)
                await main.resolve()
                await main.rip()

            await self.update_status(item.queue_id, QueueStatus.COMPLETED)
            logger.info(f"Completed: {item.queue_id}")

        except Exception as e:
            logger.error(f"Failed: {item.queue_id} - {e}")
            await self.update_status(item.queue_id, QueueStatus.FAILED)

        finally:
            # Remove from active
            self.active_downloads.pop(item.queue_id, None)

    def _cleanup_completed(self):
        """Remove completed tasks from active downloads"""
        completed = [
            qid for qid, task in self.active_downloads.items()
            if task.done()
        ]
        for qid in completed:
            self.active_downloads.pop(qid)

    async def update_status(self, queue_id: str, status: QueueStatus, **kwargs):
        """Update item status"""
        update_data = {'status': status.value}

        if status == QueueStatus.DOWNLOADING:
            update_data['started_at'] = int(time.time())
        elif status in (QueueStatus.COMPLETED, QueueStatus.FAILED):
            update_data['completed_at'] = int(time.time())

        update_data.update(kwargs)

        await self.db.queue.update(queue_id, **update_data)

    async def cancel(self, queue_id: str):
        """Cancel queued or active download"""
        # Cancel active task if running
        if queue_id in self.active_downloads:
            self.active_downloads[queue_id].cancel()

        await self.update_status(queue_id, QueueStatus.CANCELLED)
        logger.info(f"Cancelled: {queue_id}")
```

### 3. Statistics Collection

```python
# streamrip/analytics/collector.py
from datetime import datetime, timedelta
from typing import Dict, List

class StatsCollector:
    def __init__(self, db: Database):
        self.db = db

    async def record_download(self, download_data: dict):
        """Record download for statistics"""
        date = datetime.now().strftime('%Y-%m-%d')

        # Update daily stats
        await self._increment_daily_stat(date, 'total_downloads')

        if download_data.get('success'):
            await self._increment_daily_stat(date, 'successful_downloads')
        else:
            await self._increment_daily_stat(date, 'failed_downloads')

        # Update source-specific counts
        source = download_data['source']
        await self._increment_daily_stat(date, f'{source}_count')

        # Update quality counts
        quality = download_data['quality']
        await self._increment_daily_stat(date, f'quality_{quality}_count')

        # Update data transfer
        file_size = download_data.get('file_size', 0)
        await self._add_to_daily_stat(date, 'total_bytes', file_size)

        duration = download_data.get('download_duration', 0)
        await self._add_to_daily_stat(date, 'total_duration', duration)

    async def _increment_daily_stat(self, date: str, field: str):
        """Increment a daily statistic"""
        # Use SQL ON CONFLICT to upsert
        await self.db.execute(f"""
            INSERT INTO download_stats (date, {field})
            VALUES (?, 1)
            ON CONFLICT(date) DO UPDATE SET
                {field} = {field} + 1
        """, (date,))

    async def _add_to_daily_stat(self, date: str, field: str, value: float):
        """Add value to a daily statistic"""
        await self.db.execute(f"""
            INSERT INTO download_stats (date, {field})
            VALUES (?, ?)
            ON CONFLICT(date) DO UPDATE SET
                {field} = {field} + ?
        """, (date, value, value))

    async def get_stats(self, period: int = 30) -> Dict:
        """Get statistics for the last N days"""
        start_date = (datetime.now() - timedelta(days=period)).strftime('%Y-%m-%d')

        # Get daily stats
        daily_stats = await self.db.query("""
            SELECT * FROM download_stats
            WHERE date >= ?
            ORDER BY date
        """, (start_date,))

        # Get library stats
        library_stats = await self.db.query("""
            SELECT
                COUNT(*) as total_tracks,
                COUNT(DISTINCT artist) as total_artists,
                COUNT(DISTINCT album) as total_albums,
                SUM(file_size) as total_size,
                SUM(duration) as total_duration,
                AVG(quality) as avg_quality
            FROM library_catalog
        """)

        # Aggregate by source
        by_source = await self.db.query("""
            SELECT source, COUNT(*) as count
            FROM downloads
            WHERE download_timestamp >= ?
            GROUP BY source
        """, (int(time.time()) - period * 86400,))

        # Most downloaded artist
        top_artist = await self.db.query("""
            SELECT artist, COUNT(*) as count
            FROM downloads
            WHERE download_timestamp >= ?
            GROUP BY artist
            ORDER BY count DESC
            LIMIT 1
        """, (int(time.time()) - period * 86400,))

        return {
            'period': f'{period}d',
            'daily_stats': daily_stats,
            'library': library_stats[0] if library_stats else {},
            'by_source': {row['source']: row['count'] for row in by_source},
            'top_artist': top_artist[0]['artist'] if top_artist else None
        }

    async def get_insights(self) -> List[Dict]:
        """Generate insights from statistics"""
        insights = []

        # Library composition
        genre_dist = await self.db.query("""
            SELECT genre, COUNT(*) * 100.0 / (SELECT COUNT(*) FROM library_catalog) as percentage
            FROM library_catalog
            WHERE genre IS NOT NULL
            GROUP BY genre
            ORDER BY percentage DESC
            LIMIT 3
        """)

        for row in genre_dist:
            insights.append({
                'type': 'composition',
                'message': f"{row['genre']} makes up {row['percentage']:.1f}% of your library"
            })

        # Quality preference
        lossless_pct = await self.db.query_scalar("""
            SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM library_catalog)
            FROM library_catalog
            WHERE is_lossless = 1
        """)

        insights.append({
            'type': 'quality',
            'message': f"{lossless_pct:.0f}% of your library is lossless"
        })

        # Download patterns
        most_active_day = await self.db.query("""
            SELECT strftime('%w', datetime(download_timestamp, 'unixepoch')) as day,
                   COUNT(*) as count
            FROM downloads
            GROUP BY day
            ORDER BY count DESC
            LIMIT 1
        """)

        if most_active_day:
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            day_name = days[int(most_active_day[0]['day'])]
            insights.append({
                'type': 'pattern',
                'message': f"You download most on {day_name}s"
            })

        # Storage prediction
        recent_growth = await self.db.query_scalar("""
            SELECT SUM(file_size) as bytes
            FROM downloads
            WHERE download_timestamp >= ?
        """, (int(time.time()) - 30 * 86400,))

        if recent_growth:
            yearly_growth = recent_growth * 12  # 30 days * 12 months
            insights.append({
                'type': 'prediction',
                'message': f"Predicted storage in 1 year: {yearly_growth / 1e9:.0f} GB"
            })

        return insights
```

---

## Conclusion

This implementation guide provides:

1. **Detailed Architecture** - Clear structure for new components
2. **Database Schemas** - Production-ready table definitions with indexes
3. **API Specifications** - Complete REST and GraphQL endpoints
4. **Configuration** - Enhanced config structure
5. **Dependencies** - Clear implementation order
6. **Performance** - Optimization strategies
7. **Security** - Best practices and examples
8. **Testing** - Comprehensive testing approach
9. **Migration** - Backward compatibility strategy
10. **Code Examples** - Production-ready implementations

### Next Steps

1. Review and validate architecture decisions
2. Set up development environment
3. Implement Tier 1 features following the sprint plan
4. Establish CI/CD pipeline
5. Set up monitoring and logging infrastructure
6. Create developer documentation
7. Build community around contributions

### Success Metrics

- Code coverage >80%
- API response time <100ms (p95)
- Database queries <50ms (p95)
- Support 1000+ concurrent downloads
- Zero data loss on crashes (resume capability)
- <1% download failure rate

This guide, combined with FEATURE_RECOMMENDATIONS.md, provides a complete roadmap for transforming streamrip into a world-class music library management platform.
