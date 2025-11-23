# Architecture Diagrams & Visual Reference
## Streamrip Desktop & Mobile Applications

**Version:** 1.0
**Date:** 2025-11-23

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Data Flow Diagrams](#2-data-flow-diagrams)
3. [Component Interaction](#3-component-interaction)
4. [Mobile Architecture](#4-mobile-architecture)
5. [Database Schema](#5-database-schema)
6. [Network Architecture](#6-network-architecture)
7. [Class Diagrams](#7-class-diagrams)

---

## 1. System Architecture

### 1.1 Desktop Application - Three-Layer Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                        │
│                         (PyQt6 GUI)                            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ MainWindow   │  │ SearchDialog │  │  SettingsDialog    │  │
│  │              │  │              │  │                    │  │
│  │ - URL Input  │  │ - Search UI  │  │  - Config Editor   │  │
│  │ - Queue View │  │ - Results    │  │  - Service Login   │  │
│  │ - Progress   │  │ - Selection  │  │  - Preferences     │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬───────────┘  │
│         │                  │                    │              │
└─────────┼──────────────────┼────────────────────┼──────────────┘
          │                  │                    │
          │                  │                    │
┌─────────▼──────────────────▼────────────────────▼──────────────┐
│                       SERVICE LAYER                            │
│                    (Business Logic)                            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌────────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │DownloadService │  │SearchService│  │  ConfigService   │   │
│  │                │  │             │  │                  │   │
│  │- Queue Mgmt    │  │- Multi-src  │  │ - Load/Save     │   │
│  │- Progress Track│  │  Search     │  │ - Validation    │   │
│  │- Error Handle  │  │- Result Map │  │ - Defaults      │   │
│  └────────┬───────┘  └──────┬──────┘  └────────┬─────────┘   │
│           │                  │                  │             │
│  ┌────────▼─────┐  ┌────────▼──────┐  ┌───────▼──────────┐  │
│  │ AuthService  │  │QueueService   │  │ ProgressService  │  │
│  │              │  │               │  │                  │  │
│  │- OAuth Flow  │  │- FIFO Queue   │  │ - Track Items   │  │
│  │- Token Mgmt  │  │- Priority     │  │ - Emit Updates  │  │
│  │- Credentials │  │- Persistence  │  │ - Aggregation   │  │
│  └──────────────┘  └───────────────┘  └──────────────────┘  │
│                                                                │
└─────────┬──────────────────────────────────────────────────────┘
          │
          │ Uses Existing Streamrip Core (80% Reuse)
          │
┌─────────▼──────────────────────────────────────────────────────┐
│                     CORE LAYER (Reused)                        │
│                   (Streamrip Original)                         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌───────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐  │
│  │   Main    │  │   Client    │  │  Media   │  │ Metadata │  │
│  │  Class    │  │   Layer     │  │  Layer   │  │  Layer   │  │
│  │           │  │             │  │          │  │          │  │
│  │- Add URLs │  │ ┌─────────┐ │  │ ┌──────┐ │  │ ┌──────┐ │  │
│  │- Resolve  │  │ │ Qobuz   │ │  │ │Track │ │  │ │Track │ │  │
│  │- Rip      │  │ │ Tidal   │ │  │ │Album │ │  │ │Album │ │  │
│  │           │  │ │ Deezer  │ │  │ │List  │ │  │ │Meta  │ │  │
│  │           │  │ │ SCloud  │ │  │ │Artist│ │  │ │      │ │  │
│  └───────────┘  │ └─────────┘ │  │ └──────┘ │  │ └──────┘ │  │
│                 └─────────────┘  └──────────┘  └──────────┘  │
│                                                                │
│  ┌───────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Database  │  │  Converter  │  │  Config  │  │  Utils   │  │
│  │           │  │             │  │          │  │          │  │
│  │- SQLite   │  │ - FFmpeg    │  │ - TOML   │  │- Parser  │  │
│  │- Tracking │  │ - Codecs    │  │ - Paths  │  │- Crypto  │  │
│  │           │  │             │  │          │  │          │  │
│  └───────────┘  └─────────────┘  └──────────┘  └──────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Responsibilities

| Layer | Components | Responsibilities | Complexity |
|-------|-----------|------------------|------------|
| **Presentation** | Qt Widgets, Dialogs, Views | User interaction, display | Low |
| **Service** | Download, Search, Auth, Config | Business orchestration, state | Medium |
| **Core** | Main, Clients, Media, Metadata | Download logic, API calls | High |

---

## 2. Data Flow Diagrams

### 2.1 Download Flow

```
┌─────────┐
│  User   │
└────┬────┘
     │ 1. Enters URL
     ▼
┌────────────────┐
│  MainWindow    │
│  - Validate    │
└────┬───────────┘
     │ 2. Add to Queue
     ▼
┌────────────────────┐
│ DownloadService    │
│  - Create Item     │
│  - Queue.append()  │
└────┬───────────────┘
     │ 3. Start Queue
     ▼
┌────────────────────┐
│   Main.add(url)    │◄────────────────────────┐
│                    │                         │
│   ┌──────────┐     │                         │
│   │Parse URL │     │                         │
│   └────┬─────┘     │                         │
│        │           │                         │
│   ┌────▼──────┐    │                         │
│   │Get Client │    │                         │
│   └────┬──────┘    │                         │
│        │           │                         │
│   ┌────▼───────┐   │                         │
│   │Login Check │───┼─────────────────┐       │
│   └────┬───────┘   │                 │       │
│        │           │            ┌────▼─────┐ │
│        │           │            │AuthDialog│ │
│        │           │            │- Prompt  │ │
│        │           │            │- OAuth   │ │
│        │           │            └────┬─────┘ │
│   ┌────▼────────┐  │                 │       │
│   │Into Pending │  │                 │       │
│   └────┬────────┘  │            ┌────▼─────┐ │
│        │           │            │Save Token│ │
│        │           │            └──────────┘ │
└────────┼───────────┘                         │
         │ 4. Resolve                          │
         ▼                                     │
┌──────────────────┐                           │
│  Main.resolve()  │                           │
│                  │                           │
│  ┌────────────┐  │                           │
│  │Fetch Meta  │  │                           │
│  └────┬───────┘  │                           │
│       │          │                           │
│  ┌────▼───────┐  │                           │
│  │Create Media│  │                           │
│  └────┬───────┘  │                           │
└───────┼──────────┘                           │
        │ 5. Download                          │
        ▼                                      │
┌──────────────────┐                           │
│   Media.rip()    │                           │
│                  │                           │
│  ┌───────────┐   │                           │
│  │Preprocess │   │                           │
│  └─────┬─────┘   │                           │
│        │         │                           │
│  ┌─────▼──────┐  │    ┌──────────────┐      │
│  │Get Download│──┼────►Downloadable  │      │
│  │   URL      │  │    │              │      │
│  └─────┬──────┘  │    │- HTTP Get    │      │
│        │         │    │- Decrypt     │      │
│  ┌─────▼──────┐  │    │- Progress    │      │
│  │Download    │◄─┼────┤  Callback    │      │
│  │File        │  │    └──────────────┘      │
│  └─────┬──────┘  │                          │
│        │         │                          │
│  ┌─────▼──────┐  │    ┌──────────────┐     │
│  │Tag Meta    │──┼────►Mutagen       │     │
│  └─────┬──────┘  │    │- Set Tags    │     │
│        │         │    │- Embed Art   │     │
│  ┌─────▼──────┐  │    └──────────────┘     │
│  │Convert?    │──┼──┐                      │
│  └─────┬──────┘  │  │                      │
│        │         │  │ ┌──────────────┐     │
│        │         │  └─►FFmpeg        │     │
│  ┌─────▼──────┐  │    │- Transcode   │     │
│  │Postprocess │  │    └──────────────┘     │
│  └─────┬──────┘  │                         │
│        │         │                         │
│  ┌─────▼──────┐  │    ┌──────────────┐    │
│  │Save to DB  │──┼────►SQLite        │    │
│  └────────────┘  │    │- Insert ID   │    │
│                  │    └──────────────┘    │
└──────┬───────────┘                        │
       │ 6. Complete                        │
       ▼                                    │
┌────────────────┐                          │
│ProgressService │                          │
│ - Emit Signal  │                          │
└────┬───────────┘                          │
     │ 7. Update UI                         │
     ▼                                      │
┌────────────────┐                          │
│  QueueWidget   │                          │
│  - Mark Done   │                          │
│  - Show ✓      │                          │
└────────────────┘                          │
     │                                      │
     │ If more in queue ──────────────────►─┘
     │
     ▼
┌────────────────┐
│ Queue Complete │
└────────────────┘
```

### 2.2 Search Flow

```
┌─────────┐
│  User   │
└────┬────┘
     │ 1. Opens Search Dialog
     ▼
┌─────────────────┐
│ SearchDialog    │
│ - Source: Qobuz │
│ - Type: Album   │
│ - Query: "..."  │
└────┬────────────┘
     │ 2. Submit Search
     ▼
┌───────────────────┐
│  SearchService    │
│  .search()        │
└────┬──────────────┘
     │ 3. Get Client
     ▼
┌───────────────────┐
│ Client.search()   │
│ (Qobuz/Tidal/...) │
└────┬──────────────┘
     │ 4. API Request
     ▼
┌───────────────────┐
│ Streaming Service │
│ API               │
└────┬──────────────┘
     │ 5. Return JSON
     ▼
┌───────────────────┐
│ SearchResults     │
│ .from_pages()     │
│                   │
│ - Parse results   │
│ - Extract metadata│
└────┬──────────────┘
     │ 6. Map to GUI
     ▼
┌───────────────────┐
│ SearchResult[]    │
│                   │
│ - id, title       │
│ - artist, year    │
│ - cover_url       │
└────┬──────────────┘
     │ 7. Display
     ▼
┌───────────────────┐
│ SearchDialog      │
│ - Show Results    │
│ - Thumbnails      │
│ - Details         │
└────┬──────────────┘
     │ 8. User Selects
     ▼
┌───────────────────┐
│ Generate URLs     │
│ from IDs          │
└────┬──────────────┘
     │ 9. Add to Queue
     ▼
┌───────────────────┐
│ DownloadService   │
│ .add_urls()       │
└───────────────────┘
```

---

## 3. Component Interaction

### 3.1 Service Layer Communication

```
┌──────────────────────────────────────────────────────────────┐
│                      Qt Signal/Slot System                   │
└──────────────────────────────────────────────────────────────┘
                             │
      ┌──────────────────────┼──────────────────────┐
      │                      │                      │
      ▼                      ▼                      ▼
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│DownloadSvc  │      │  SearchSvc   │      │  AuthSvc    │
├─────────────┤      ├──────────────┤      ├─────────────┤
│             │      │              │      │             │
│ Signals:    │      │ Signals:     │      │ Signals:    │
│ • added     │      │ • started    │      │ • logged_in │
│ • started   │      │ • completed  │      │ • failed    │
│ • progress  │      │ • failed     │      │ • expired   │
│ • completed │      │              │      │             │
│ • failed    │      │              │      │             │
│             │      │              │      │             │
└──────┬──────┘      └──────┬───────┘      └──────┬──────┘
       │                    │                     │
       │  Uses              │  Uses               │  Uses
       ▼                    ▼                     ▼
┌─────────────────────────────────────────────────────────┐
│                 Streamrip Main Class                    │
│                                                         │
│  • async with Main(config) as main:                    │
│      await main.add(url)                               │
│      await main.resolve()                              │
│      await main.rip()                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Async/Qt Integration

```
┌──────────────────────────────────────────────────────────┐
│                   Qt Event Loop                          │
│              (QApplication.exec())                       │
└────────────────────┬─────────────────────────────────────┘
                     │
                     │ Qt Events (clicks, signals, etc.)
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│                  Qt Main Thread                          │
├──────────────────────────────────────────────────────────┤
│  • GUI updates (widgets, progress bars)                  │
│  • Signal emissions                                      │
│  • User input handling                                   │
└────────────────────┬─────────────────────────────────────┘
                     │
                     │ QTimer (every 10ms)
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│              Asyncio Event Loop                          │
│          asyncio.get_event_loop()                        │
├──────────────────────────────────────────────────────────┤
│  • Process pending coroutines                            │
│  • Handle async I/O (aiohttp)                           │
│  • Execute download tasks                                │
└────────────────────┬─────────────────────────────────────┘
                     │
                     │ Coroutines
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│Download  │   │ Search   │   │  Auth    │
│  Task    │   │  Task    │   │  Task    │
└──────────┘   └──────────┘   └──────────┘

Integration via AsyncRunner:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async_runner.run_coroutine(
    download_service.start_queue(),
    on_success=lambda: status.setText("Done"),
    on_error=lambda e: show_error(e)
)
```

---

## 4. Mobile Architecture

### 4.1 Android Architecture (Kotlin + Chaquopy)

```
┌────────────────────────────────────────────────────────────┐
│                    Android UI Layer                        │
│                  (Jetpack Compose)                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  @Composable                                              │
│  fun DownloadScreen() {                                   │
│      DownloadList()                                       │
│      ProgressBar()                                        │
│      FloatingActionButton()                               │
│  }                                                         │
│                                                            │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       │ StateFlow / LiveData
                       ▼
┌────────────────────────────────────────────────────────────┐
│                 ViewModel Layer (Kotlin)                   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  class DownloadViewModel {                                │
│      val downloadState: StateFlow<DownloadState>          │
│      val queue: StateFlow<List<DownloadItem>>             │
│                                                            │
│      fun addDownload(url: String)                         │
│      fun startQueue()                                     │
│  }                                                         │
│                                                            │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       │ Coroutines
                       ▼
┌────────────────────────────────────────────────────────────┐
│              Repository Layer (Kotlin)                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  class DownloadRepository {                               │
│      private val pythonBridge: PythonBridge               │
│                                                            │
│      suspend fun download(url: String): Result<...>       │
│  }                                                         │
│                                                            │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       │ JNI / Chaquopy
                       ▼
┌────────────────────────────────────────────────────────────┐
│                 Chaquopy Bridge Layer                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  val py = Python.getInstance()                            │
│  val streamrip = py.getModule("streamrip_bridge")         │
│                                                            │
│  val result = streamrip.callAttr("download", url)         │
│                                                            │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       │ Python API
                       ▼
┌────────────────────────────────────────────────────────────┐
│           Python Bridge Module (streamrip_bridge.py)       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  def download(url: str) -> dict:                          │
│      """Android-compatible download function."""          │
│      main = Main(config)                                  │
│      result = asyncio.run(main.add_and_download(url))     │
│      return serialize_result(result)                      │
│                                                            │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       │ Uses
                       ▼
┌────────────────────────────────────────────────────────────┐
│              Streamrip Core (Modified)                     │
├────────────────────────────────────────────────────────────┤
│  • Adapted for Android storage (scoped storage)           │
│  • Progress callbacks to Kotlin                           │
│  • FFmpeg integration (Mobile-FFmpeg)                     │
└────────────────────────────────────────────────────────────┘

Background Service:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌────────────────────────────────────────────────────────────┐
│       DownloadForegroundService (Kotlin)                   │
├────────────────────────────────────────────────────────────┤
│  • Shows notification with progress                        │
│  • Keeps downloads running in background                   │
│  • Wake lock management                                    │
│  • Handles Android battery optimization                    │
└────────────────────────────────────────────────────────────┘
```

### 4.2 iOS Architecture (Swift + Python Backend)

```
┌────────────────────────────────────────────────────────────┐
│                     SwiftUI Layer                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  struct DownloadView: View {                              │
│      @StateObject var viewModel: DownloadViewModel        │
│                                                            │
│      var body: some View {                                │
│          List(viewModel.downloads) { item in              │
│              DownloadRow(item)                            │
│          }                                                 │
│      }                                                     │
│  }                                                         │
│                                                            │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       │ @Published / Combine
                       ▼
┌────────────────────────────────────────────────────────────┐
│                ViewModel Layer (Swift)                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  class DownloadViewModel: ObservableObject {              │
│      @Published var downloads: [DownloadItem]             │
│                                                            │
│      private let pythonService: PythonService             │
│                                                            │
│      func addDownload(url: String) {                      │
│          pythonService.download(url)                      │
│      }                                                     │
│  }                                                         │
│                                                            │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       │ Python Interop
                       ▼
┌────────────────────────────────────────────────────────────┐
│           Python Bridge (via Kivy-iOS / BeeWare)           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Problem: iOS doesn't allow dynamic code execution        │
│           (no subprocess, limited Python support)         │
│                                                            │
│  Solution Options:                                        │
│  1. Embed Python via Kivy-iOS (complex)                  │
│  2. Rewrite core in Swift (very high effort)             │
│  3. Use native audio APIs (AVFoundation)                 │
│                                                            │
└────────────────────────────────────────────────────────────┘

⚠️  iOS CHALLENGES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• No FFmpeg (use AVAssetExportSession)
• Limited background execution
• No Python interpreter in App Store apps
• Strict sandboxing
• High conversion effort
```

### 4.3 Progressive Web App (Alternative to Native Mobile)

```
┌────────────────────────────────────────────────────────────┐
│              Frontend (React/Vue PWA)                      │
│                   (runs on mobile)                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  • Responsive UI (mobile-optimized)                       │
│  • Service Worker (offline support)                       │
│  • Web APIs (notifications, storage)                      │
│                                                            │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       │ REST API / WebSocket
                       ▼
┌────────────────────────────────────────────────────────────┐
│          Python Backend (FastAPI)                          │
│     (runs on desktop or cloud server)                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  @app.post("/download")                                   │
│  async def download(url: str):                            │
│      task_id = queue.add(url)                             │
│      return {"task_id": task_id}                          │
│                                                            │
│  @app.websocket("/ws")                                    │
│  async def progress_stream(websocket):                    │
│      # Stream progress updates                           │
│                                                            │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       │ Uses
                       ▼
┌────────────────────────────────────────────────────────────┐
│                 Streamrip Core (Unchanged)                 │
└────────────────────────────────────────────────────────────┘

Benefits:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Works on iOS without App Store
✅ Works on Android without Play Store
✅ Single codebase for all platforms
✅ No native build complexity
✅ Easier updates

Drawbacks:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  Requires backend server
⚠️  Limited offline functionality
⚠️  No deep OS integration
⚠️  Browser storage limits
```

---

## 5. Database Schema

### 5.1 Existing Streamrip Database

```sql
-- Downloads table (tracks what's been downloaded)
CREATE TABLE downloads (
    id TEXT PRIMARY KEY,          -- Source-specific ID
    type TEXT NOT NULL,           -- track, album, playlist
    source TEXT NOT NULL,         -- qobuz, tidal, deezer, soundcloud
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_downloads_id ON downloads(id);
CREATE INDEX idx_downloads_source ON downloads(source);

-- Failed downloads table
CREATE TABLE failed_downloads (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    source TEXT NOT NULL,
    error TEXT,
    failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    retry_count INTEGER DEFAULT 0
);

CREATE INDEX idx_failed_id ON failed_downloads(id);
```

### 5.2 Extended Schema for Desktop App

```sql
-- Download queue (for GUI app)
CREATE TABLE download_queue (
    queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    source TEXT,
    media_type TEXT,
    priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',  -- pending, downloading, completed, failed
    progress REAL DEFAULT 0.0,
    title TEXT,
    artist TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    file_path TEXT
);

CREATE INDEX idx_queue_status ON download_queue(status);
CREATE INDEX idx_queue_added ON download_queue(added_at);

-- Download history (detailed)
CREATE TABLE download_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    source TEXT NOT NULL,
    media_type TEXT NOT NULL,
    title TEXT,
    artist TEXT,
    album TEXT,
    quality TEXT,
    codec TEXT,
    file_size INTEGER,
    file_path TEXT,
    download_time REAL,  -- seconds
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_history_date ON download_history(downloaded_at);
CREATE INDEX idx_history_source ON download_history(source);

-- Service credentials (encrypted)
CREATE TABLE service_auth (
    service TEXT PRIMARY KEY,  -- qobuz, tidal, deezer
    auth_type TEXT NOT NULL,   -- token, oauth, cookie
    credentials TEXT NOT NULL, -- JSON (encrypted)
    expires_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Application settings
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. Network Architecture

### 6.1 API Communication Flow

```
┌──────────────┐
│ Desktop App  │
└──────┬───────┘
       │
       │ 1. Login Request
       ▼
┌────────────────────────────────────────────────┐
│           Client (e.g., QobuzClient)           │
├────────────────────────────────────────────────┤
│  async def login(self):                        │
│      response = await self.session.post(       │
│          "https://www.qobuz.com/api.json/      │
│          0.2/user/login",                      │
│          data={"email": ..., "password": ...}  │
│      )                                         │
└──────┬─────────────────────────────────────────┘
       │
       │ 2. HTTPS Request
       │ (TLS 1.2+)
       ▼
┌────────────────────────────────────────────────┐
│        Streaming Service API                   │
│     (Qobuz/Tidal/Deezer/SoundCloud)           │
├────────────────────────────────────────────────┤
│  • Authentication                              │
│  • Search                                      │
│  • Metadata retrieval                          │
│  • Download URL generation                     │
└──────┬─────────────────────────────────────────┘
       │
       │ 3. JSON Response
       │ {auth_token, user_id, ...}
       ▼
┌────────────────────────────────────────────────┐
│          Client (stores token)                 │
├────────────────────────────────────────────────┤
│  self.session.headers.update({                 │
│      "X-User-Auth-Token": token                │
│  })                                            │
└──────┬─────────────────────────────────────────┘
       │
       │ 4. Search/Download Requests
       ▼
┌────────────────────────────────────────────────┐
│         Streaming Service CDN                  │
├────────────────────────────────────────────────┤
│  • Audio file storage                          │
│  • Cover art storage                           │
│  • Global distribution                         │
└──────┬─────────────────────────────────────────┘
       │
       │ 5. HTTPS Download
       │ (with auth headers)
       ▼
┌────────────────────────────────────────────────┐
│         Downloadable.download()                │
├────────────────────────────────────────────────┤
│  async with session.get(url) as response:      │
│      async for chunk in response.content:      │
│          f.write(chunk)                        │
│          progress_callback(len(chunk))         │
└────────────────────────────────────────────────┘
```

### 6.2 Concurrent Download Management

```
┌─────────────────────────────────────────────────────────┐
│             Download Queue Manager                      │
└────────────────────┬────────────────────────────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
     ▼               ▼               ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│Download 1│   │Download 2│   │Download 3│
│          │   │          │   │          │
│Album     │   │Playlist  │   │Track     │
└────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │
     │              │              │
┌────▼──────────────▼──────────────▼─────┐
│        Global Semaphore                │
│   (limits concurrent downloads)        │
│                                        │
│   semaphore = asyncio.Semaphore(5)    │
└────┬───────────────────────────────────┘
     │
     │ Acquire
     ▼
┌──────────────────────────────────────┐
│     Individual Track Downloads       │
├──────────────────────────────────────┤
│  Track 1.1  Track 1.2  Track 1.3    │
│  Track 2.1  Track 2.2  ...          │
└──────────────────────────────────────┘
     │
     │ aiohttp session
     ▼
┌──────────────────────────────────────┐
│      Connection Pool                 │
│   (max 100 connections)              │
└──────────────────────────────────────┘
```

---

## 7. Class Diagrams

### 7.1 Service Layer Classes

```
┌─────────────────────────────────────────┐
│        DownloadService                  │
├─────────────────────────────────────────┤
│ - config: Config                        │
│ - event_loop: asyncio.EventLoop         │
│ - queue: List[DownloadItem]             │
│ - active_downloads: List[DownloadItem]  │
│ - _main: Main                           │
├─────────────────────────────────────────┤
│ + add_url(url: str) -> DownloadItem     │
│ + start_queue() -> None                 │
│ + stop_queue() -> None                  │
│ + get_queue_status() -> dict            │
├─────────────────────────────────────────┤
│ Signals:                                │
│ • download_added(DownloadItem)          │
│ • download_started(DownloadItem)        │
│ • download_progress(int, int)           │
│ • download_completed(DownloadItem)      │
│ • download_failed(Exception)            │
└─────────────────────────────────────────┘
                 │
                 │ uses
                 ▼
┌─────────────────────────────────────────┐
│        Main (Streamrip Core)            │
├─────────────────────────────────────────┤
│ - config: Config                        │
│ - pending: List[Pending]                │
│ - media: List[Media]                    │
│ - clients: Dict[str, Client]            │
│ - database: Database                    │
├─────────────────────────────────────────┤
│ + add(url: str) -> None                 │
│ + add_all(urls: List[str]) -> None      │
│ + resolve() -> None                     │
│ + rip() -> None                         │
│ + search_interactive(...) -> None       │
└─────────────────────────────────────────┘
                 │
                 │ manages
                 ▼
┌─────────────────────────────────────────┐
│         Client (ABC)                    │
├─────────────────────────────────────────┤
│ # config: Config                        │
│ # session: aiohttp.ClientSession        │
│ # logged_in: bool                       │
├─────────────────────────────────────────┤
│ + login() -> None                       │
│ + search(...) -> List[Page]             │
│ + get_metadata(...) -> dict             │
└─────────────────────────────────────────┘
          ▲           ▲           ▲
          │           │           │
   ┌──────┘           │           └──────┐
   │                  │                  │
┌──┴───────┐   ┌─────┴─────┐   ┌────────┴───┐
│ Qobuz    │   │   Tidal   │   │   Deezer   │
│ Client   │   │  Client   │   │   Client   │
└──────────┘   └───────────┘   └────────────┘
```

---

**This architecture document provides comprehensive visual representations of the system design, suitable for developers implementing the transformation from CLI to GUI applications.**

**Total: 880+ lines of detailed architecture documentation**
