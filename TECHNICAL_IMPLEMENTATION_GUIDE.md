# Technical Implementation Guide
## Streamrip Desktop Application Development

**Version:** 1.0
**Date:** 2025-11-23
**Target Platform:** Desktop (Windows, macOS, Linux)
**Framework:** PyQt6/PySide6
**Language:** Python 3.10+

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Code Migration Strategy](#2-code-migration-strategy)
3. [Desktop Application Structure](#3-desktop-application-structure)
4. [Implementation Details](#4-implementation-details)
5. [Service Layer Design](#5-service-layer-design)
6. [GUI Components](#6-gui-components)
7. [Async Integration with Qt](#7-async-integration-with-qt)
8. [Configuration Management](#8-configuration-management)
9. [Download Queue Management](#9-download-queue-management)
10. [OAuth Implementation](#10-oauth-implementation)
11. [Progress Tracking](#11-progress-tracking)
12. [FFmpeg Integration](#12-ffmpeg-integration)
13. [Database Integration](#13-database-integration)
14. [Error Handling](#14-error-handling)
15. [Packaging & Distribution](#15-packaging--distribution)

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                      │
│                        (PyQt6 GUI)                          │
├─────────────────────────────────────────────────────────────┤
│  MainWindow  │  SettingsDialog  │  SearchDialog  │  Queue   │
└────────┬────────────────┬──────────────┬──────────────┬─────┘
         │                │              │              │
┌────────▼────────────────▼──────────────▼──────────────▼─────┐
│                      Service Layer                          │
│                    (New Abstraction)                        │
├─────────────────────────────────────────────────────────────┤
│  DownloadService  │  SearchService  │  ConfigService  │     │
│  AuthService      │  QueueService   │  ProgressService│     │
└────────┬────────────────┬──────────────┬──────────────┬─────┘
         │                │              │              │
┌────────▼────────────────▼──────────────▼──────────────▼─────┐
│                  Core Streamrip (80% Reused)                │
├─────────────────────────────────────────────────────────────┤
│  Main Class  │  Client Layer  │  Media Layer  │  Metadata  │
│  Database    │  Converter     │  Config       │  Utils     │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Component Interaction Flow

```
User Action (Click Download Button)
    ↓
MainWindow.on_download_clicked()
    ↓
DownloadService.add_url(url)
    ↓
Main.add(url) [Existing Streamrip Code]
    ↓
ParseURL → Pending → Media
    ↓
DownloadService.start_download()
    ↓
Media.rip() [Existing Streamrip Code]
    ↓
Progress Updates → ProgressService
    ↓
GUI Updates (Progress Bar, Status)
```

---

## 2. Code Migration Strategy

### 2.1 What to Reuse (80% of codebase)

**✅ Fully Reusable Components:**

| Component | Location | Reuse Level | Modifications |
|-----------|----------|-------------|---------------|
| `Main` class | `streamrip/rip/main.py` | 95% | Minor callback additions |
| Client layer | `streamrip/client/*.py` | 100% | None |
| Media layer | `streamrip/media/*.py` | 98% | Add progress callbacks |
| Metadata layer | `streamrip/metadata/*.py` | 100% | None |
| Database | `streamrip/db.py` | 100% | None |
| Config | `streamrip/config.py` | 90% | GUI settings wrapper |
| Converter | `streamrip/converter.py` | 100% | None |
| Utils | `streamrip/utils/*.py` | 100% | None |

**❌ Replace Completely:**

| Component | Location | Replace With |
|-----------|----------|--------------|
| CLI commands | `streamrip/rip/cli.py` | PyQt6 GUI |
| Progress bars | `streamrip/progress.py` | Qt progress widgets |
| Terminal menus | `simple-term-menu` | Qt dialogs/lists |
| Console output | `rich` console | Qt message boxes |
| Prompter | `streamrip/rip/prompter.py` | Qt input dialogs |

### 2.2 Migration Phases

**Phase 1: Core Extraction (Week 1-2)**
- Create service layer abstraction
- Add callback support to Main class
- Test existing functionality still works

**Phase 2: Basic GUI (Week 3-6)**
- Main window skeleton
- URL input and download button
- Basic progress display
- Settings dialog

**Phase 3: Advanced Features (Week 7-12)**
- Search interface
- Download queue management
- OAuth integration
- Advanced settings

**Phase 4: Polish (Week 13-16)**
- Error handling
- Logging viewer
- Keyboard shortcuts
- Dark mode support

---

## 3. Desktop Application Structure

### 3.1 Project Directory Layout

```
streamrip-desktop/
├── src/
│   ├── main.py                 # Application entry point
│   ├── ui/                     # PyQt6 UI components
│   │   ├── __init__.py
│   │   ├── main_window.py      # Main application window
│   │   ├── settings_dialog.py  # Settings dialog
│   │   ├── search_dialog.py    # Search interface
│   │   ├── queue_widget.py     # Download queue
│   │   ├── login_dialog.py     # OAuth/login dialogs
│   │   ├── about_dialog.py     # About dialog
│   │   └── widgets/            # Custom widgets
│   │       ├── download_item.py
│   │       ├── progress_widget.py
│   │       └── status_bar.py
│   │
│   ├── services/               # Service layer (new)
│   │   ├── __init__.py
│   │   ├── download_service.py # Download orchestration
│   │   ├── search_service.py   # Search functionality
│   │   ├── auth_service.py     # Authentication
│   │   ├── config_service.py   # Configuration
│   │   ├── queue_service.py    # Queue management
│   │   └── progress_service.py # Progress tracking
│   │
│   ├── models/                 # Qt models (new)
│   │   ├── __init__.py
│   │   ├── download_model.py   # Download queue model
│   │   ├── search_model.py     # Search results model
│   │   └── history_model.py    # Download history
│   │
│   ├── utils/                  # GUI utilities (new)
│   │   ├── __init__.py
│   │   ├── async_helper.py     # Async/Qt integration
│   │   ├── style.py            # Styling helpers
│   │   └── validators.py       # Input validators
│   │
│   ├── resources/              # Qt resources
│   │   ├── icons/
│   │   ├── styles/
│   │   │   ├── light.qss
│   │   │   └── dark.qss
│   │   └── resources.qrc
│   │
│   └── streamrip/              # Original streamrip (submodule or copy)
│       ├── client/
│       ├── media/
│       ├── metadata/
│       ├── config.py
│       ├── db.py
│       └── ...
│
├── tests/                      # Unit tests
│   ├── test_services/
│   ├── test_ui/
│   └── fixtures/
│
├── assets/                     # Application assets
│   ├── app_icon.icns          # macOS
│   ├── app_icon.ico           # Windows
│   ├── app_icon.png           # Linux
│   └── screenshots/
│
├── packaging/                  # Packaging configs
│   ├── windows/
│   │   ├── installer.nsi      # NSIS script
│   │   └── streamrip.spec     # PyInstaller spec
│   ├── macos/
│   │   ├── Info.plist
│   │   └── entitlements.plist
│   └── linux/
│       ├── streamrip.desktop
│       └── AppImage.yml
│
├── requirements.txt
├── setup.py
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## 4. Implementation Details

### 4.1 Application Entry Point

**`src/main.py`**

```python
#!/usr/bin/env python3
"""
Streamrip Desktop - Main Entry Point
"""
import sys
import logging
import asyncio
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from ui.main_window import MainWindow
from utils.async_helper import AsyncioEventLoopPolicy
from streamrip.config import Config, DEFAULT_CONFIG_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / '.config' / 'streamrip' / 'desktop.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('streamrip-desktop')


class StreamripApplication(QApplication):
    """Main application class with async event loop integration."""

    def __init__(self, argv):
        super().__init__(argv)

        # Set application metadata
        self.setApplicationName("Streamrip Desktop")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("Streamrip")
        self.setOrganizationDomain("github.com/nathom/streamrip")

        # Set application icon
        icon_path = Path(__file__).parent / 'resources' / 'icons' / 'app_icon.png'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Enable high DPI support
        self.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        self.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

        # Set up asyncio event loop integration
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)

        # Timer to process asyncio events
        self.async_timer = QTimer()
        self.async_timer.timeout.connect(self._process_async_events)
        self.async_timer.start(10)  # Process every 10ms

        # Load configuration
        self.config = self._load_config()

        # Create main window
        self.main_window = MainWindow(self.config, self.event_loop)

    def _load_config(self) -> Config:
        """Load or create streamrip configuration."""
        try:
            config = Config(DEFAULT_CONFIG_PATH)
            logger.info(f"Loaded config from {DEFAULT_CONFIG_PATH}")
            return config
        except FileNotFoundError:
            logger.info("Creating default configuration")
            Config.create_default(DEFAULT_CONFIG_PATH)
            return Config(DEFAULT_CONFIG_PATH)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Create temporary config
            return Config()

    def _process_async_events(self):
        """Process asyncio events in the Qt event loop."""
        try:
            self.event_loop.stop()
            self.event_loop.run_forever()
        except Exception as e:
            logger.error(f"Error processing async events: {e}")

    def exec(self):
        """Override exec to show main window."""
        self.main_window.show()
        return super().exec()

    def cleanup(self):
        """Cleanup resources before exit."""
        logger.info("Cleaning up application resources...")
        self.async_timer.stop()

        # Close event loop
        pending = asyncio.all_tasks(self.event_loop)
        for task in pending:
            task.cancel()

        self.event_loop.close()


def main():
    """Main entry point."""
    logger.info("Starting Streamrip Desktop...")

    # Create application
    app = StreamripApplication(sys.argv)

    # Run application
    try:
        exit_code = app.exec()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        exit_code = 0
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        exit_code = 1
    finally:
        app.cleanup()

    logger.info(f"Application exited with code {exit_code}")
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
```

### 4.2 Async/Qt Integration Helper

**`src/utils/async_helper.py`**

```python
"""
Helper utilities for integrating asyncio with PyQt6.
"""
import asyncio
import functools
from typing import Callable, Any, Coroutine
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool


class AsyncTask(QObject):
    """Wrapper for running async tasks with Qt signals."""

    # Signals
    finished = pyqtSignal(object)  # Result
    error = pyqtSignal(Exception)  # Error
    progress = pyqtSignal(int, int)  # Current, Total

    def __init__(self, coro: Coroutine, parent=None):
        super().__init__(parent)
        self.coro = coro
        self.task = None

    async def run(self):
        """Execute the coroutine."""
        try:
            result = await self.coro
            self.finished.emit(result)
            return result
        except Exception as e:
            self.error.emit(e)
            raise

    def cancel(self):
        """Cancel the task."""
        if self.task and not self.task.done():
            self.task.cancel()


class AsyncRunner(QObject):
    """Helper class to run async functions from Qt slots."""

    def __init__(self, event_loop: asyncio.AbstractEventLoop, parent=None):
        super().__init__(parent)
        self.event_loop = event_loop

    def run_coroutine(self, coro: Coroutine,
                     on_success: Callable = None,
                     on_error: Callable = None) -> AsyncTask:
        """
        Run a coroutine and connect callbacks.

        Args:
            coro: The coroutine to run
            on_success: Callback when coroutine completes successfully
            on_error: Callback when coroutine raises an exception

        Returns:
            AsyncTask object that can be used to track/cancel the task
        """
        task_wrapper = AsyncTask(coro)

        if on_success:
            task_wrapper.finished.connect(on_success)
        if on_error:
            task_wrapper.error.connect(on_error)

        # Schedule in event loop
        task_wrapper.task = asyncio.ensure_future(
            task_wrapper.run(),
            loop=self.event_loop
        )

        return task_wrapper

    def run_in_executor(self, func: Callable, *args, **kwargs) -> asyncio.Future:
        """Run a blocking function in an executor."""
        partial = functools.partial(func, *args, **kwargs)
        return self.event_loop.run_in_executor(None, partial)


def async_slot(func):
    """
    Decorator to make async functions work as Qt slots.

    Usage:
        @async_slot
        async def on_button_clicked(self):
            result = await some_async_function()
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Get event loop from parent or create new one
        loop = getattr(self, 'event_loop', asyncio.get_event_loop())
        coro = func(self, *args, **kwargs)

        # Schedule coroutine
        return asyncio.ensure_future(coro, loop=loop)

    return wrapper
```

---

## 5. Service Layer Design

### 5.1 Download Service

**`src/services/download_service.py`**

```python
"""
Download service - orchestrates downloads using streamrip core.
"""
import asyncio
import logging
from typing import Optional, List, Callable
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal

from streamrip.rip.main import Main
from streamrip.config import Config
from streamrip.exceptions import NonStreamableError, AuthenticationError


logger = logging.getLogger(__name__)


class DownloadStatus(Enum):
    """Download status enumeration."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadItem:
    """Represents a single download item."""

    def __init__(self, url: str, quality: int = None):
        self.url = url
        self.quality = quality
        self.status = DownloadStatus.PENDING
        self.progress = 0.0
        self.total_size = 0
        self.downloaded_size = 0
        self.error: Optional[Exception] = None
        self.title: Optional[str] = None
        self.artist: Optional[str] = None
        self.type: Optional[str] = None  # track, album, playlist

    def __repr__(self):
        return f"<DownloadItem {self.url} [{self.status.value}]>"


class DownloadService(QObject):
    """
    Service for managing downloads.

    Signals:
        download_added: Emitted when a download is added to queue
        download_started: Emitted when a download starts
        download_progress: Emitted on download progress (item, current, total)
        download_completed: Emitted when a download completes
        download_failed: Emitted when a download fails
    """

    # Signals
    download_added = pyqtSignal(DownloadItem)
    download_started = pyqtSignal(DownloadItem)
    download_progress = pyqtSignal(DownloadItem, int, int)
    download_completed = pyqtSignal(DownloadItem)
    download_failed = pyqtSignal(DownloadItem, Exception)
    queue_completed = pyqtSignal()

    def __init__(self, config: Config, event_loop: asyncio.AbstractEventLoop):
        super().__init__()
        self.config = config
        self.event_loop = event_loop
        self.queue: List[DownloadItem] = []
        self.active_downloads: List[DownloadItem] = []
        self.max_concurrent = config.session.downloads.concurrency
        self._main: Optional[Main] = None
        self._is_running = False

    async def initialize(self):
        """Initialize the download service."""
        self._main = Main(self.config)
        logger.info("Download service initialized")

    async def cleanup(self):
        """Cleanup resources."""
        if self._main:
            await self._main.__aexit__(None, None, None)
        logger.info("Download service cleaned up")

    def add_url(self, url: str, quality: Optional[int] = None) -> DownloadItem:
        """
        Add a URL to the download queue.

        Args:
            url: The URL to download
            quality: Optional quality override (0-4)

        Returns:
            DownloadItem object
        """
        item = DownloadItem(url, quality)
        self.queue.append(item)
        self.download_added.emit(item)
        logger.info(f"Added to queue: {url}")
        return item

    def add_urls(self, urls: List[str]) -> List[DownloadItem]:
        """Add multiple URLs to queue."""
        items = []
        for url in urls:
            item = self.add_url(url)
            items.append(item)
        return items

    async def start_queue(self):
        """Start processing the download queue."""
        if self._is_running:
            logger.warning("Download queue already running")
            return

        self._is_running = True
        logger.info(f"Starting download queue ({len(self.queue)} items)")

        try:
            while self.queue and self._is_running:
                # Process up to max_concurrent downloads
                while (len(self.active_downloads) < self.max_concurrent and
                       self.queue and self._is_running):
                    item = self.queue.pop(0)
                    asyncio.create_task(self._download_item(item))

                # Wait a bit before checking again
                await asyncio.sleep(0.5)

            # Wait for all active downloads to complete
            while self.active_downloads:
                await asyncio.sleep(0.5)

            self.queue_completed.emit()
            logger.info("Download queue completed")

        except Exception as e:
            logger.error(f"Error in download queue: {e}")
        finally:
            self._is_running = False

    async def _download_item(self, item: DownloadItem):
        """Download a single item."""
        self.active_downloads.append(item)
        item.status = DownloadStatus.DOWNLOADING
        self.download_started.emit(item)

        try:
            # Add to streamrip Main
            await self._main.add(item.url)

            # Resolve metadata
            await self._main.resolve()

            # Get media info for display
            if self._main.media:
                media = self._main.media[-1]
                item.title = getattr(media.meta, 'title', 'Unknown')
                item.artist = getattr(media.meta, 'artist', 'Unknown')
                item.type = media.__class__.__name__.lower()

            # Start download with progress callback
            await self._download_with_progress(item)

            # Mark as completed
            item.status = DownloadStatus.COMPLETED
            item.progress = 100.0
            self.download_completed.emit(item)
            logger.info(f"Completed: {item.url}")

        except AuthenticationError as e:
            item.status = DownloadStatus.FAILED
            item.error = e
            self.download_failed.emit(item, e)
            logger.error(f"Authentication failed for {item.url}: {e}")

        except NonStreamableError as e:
            item.status = DownloadStatus.FAILED
            item.error = e
            self.download_failed.emit(item, e)
            logger.error(f"Non-streamable content {item.url}: {e}")

        except Exception as e:
            item.status = DownloadStatus.FAILED
            item.error = e
            self.download_failed.emit(item, e)
            logger.exception(f"Download failed for {item.url}: {e}")

        finally:
            self.active_downloads.remove(item)
            # Clear main's media list for next download
            self._main.media.clear()

    async def _download_with_progress(self, item: DownloadItem):
        """
        Download media with progress tracking.

        This is a modified version of Main.rip() with progress callbacks.
        """
        if not self._main.media:
            return

        media = self._main.media[-1]

        # Monkey-patch progress callback into track downloads
        original_download = media.rip

        async def download_with_callback():
            # Set up progress tracking
            # This would require modifying streamrip's download methods
            # to accept progress callbacks
            result = await original_download()
            return result

        await download_with_callback()

    def stop_queue(self):
        """Stop processing the download queue."""
        self._is_running = False
        logger.info("Download queue stopped")

    def clear_queue(self):
        """Clear the download queue."""
        self.queue.clear()
        logger.info("Download queue cleared")

    def remove_item(self, item: DownloadItem):
        """Remove an item from the queue."""
        if item in self.queue:
            self.queue.remove(item)
            logger.info(f"Removed from queue: {item.url}")

    def get_queue_status(self) -> dict:
        """Get current queue status."""
        return {
            'total': len(self.queue) + len(self.active_downloads),
            'active': len(self.active_downloads),
            'queued': len(self.queue),
            'is_running': self._is_running
        }
```

### 5.2 Search Service

**`src/services/search_service.py`**

```python
"""
Search service - handles search across streaming platforms.
"""
import asyncio
import logging
from typing import List, Optional
from dataclasses import dataclass

from PyQt6.QtCore import QObject, pyqtSignal

from streamrip.rip.main import Main
from streamrip.config import Config
from streamrip.metadata import SearchResults


logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Simplified search result for GUI."""
    id: str
    source: str
    media_type: str
    title: str
    artist: str
    year: Optional[int]
    cover_url: Optional[str]
    extra_info: str  # Additional info (album count, track count, etc.)

    def __str__(self):
        return f"{self.title} - {self.artist} ({self.year or 'N/A'})"


class SearchService(QObject):
    """
    Service for searching across streaming platforms.

    Signals:
        search_started: Emitted when search begins
        search_completed: Emitted when search completes
        search_failed: Emitted when search fails
    """

    # Signals
    search_started = pyqtSignal(str, str, str)  # source, media_type, query
    search_completed = pyqtSignal(list)  # List[SearchResult]
    search_failed = pyqtSignal(Exception)

    def __init__(self, config: Config, event_loop: asyncio.AbstractEventLoop):
        super().__init__()
        self.config = config
        self.event_loop = event_loop
        self._main: Optional[Main] = None
        self._last_results: List[SearchResult] = []

    async def initialize(self):
        """Initialize the search service."""
        self._main = Main(self.config)
        logger.info("Search service initialized")

    async def cleanup(self):
        """Cleanup resources."""
        if self._main:
            await self._main.__aexit__(None, None, None)
        logger.info("Search service cleaned up")

    async def search(self, source: str, media_type: str, query: str,
                    limit: int = 50) -> List[SearchResult]:
        """
        Search for content.

        Args:
            source: Platform to search (qobuz, tidal, deezer, soundcloud)
            media_type: Type to search for (track, album, playlist, artist)
            query: Search query
            limit: Maximum results to return

        Returns:
            List of SearchResult objects
        """
        self.search_started.emit(source, media_type, query)
        logger.info(f"Searching {source} for {media_type}: {query}")

        try:
            # Get logged in client
            client = await self._main.get_logged_in_client(source)

            # Perform search
            pages = await client.search(media_type, query, limit=limit)

            if not pages:
                logger.info(f"No results found for '{query}'")
                self.search_completed.emit([])
                return []

            # Convert to SearchResults
            search_results = SearchResults.from_pages(source, media_type, pages)

            # Convert to GUI-friendly format
            gui_results = []
            for result in search_results.results:
                gui_result = self._convert_result(result, source, media_type)
                gui_results.append(gui_result)

            self._last_results = gui_results
            self.search_completed.emit(gui_results)
            logger.info(f"Found {len(gui_results)} results")

            return gui_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            self.search_failed.emit(e)
            raise

    def _convert_result(self, result, source: str, media_type: str) -> SearchResult:
        """Convert streamrip search result to GUI format."""
        return SearchResult(
            id=result.id,
            source=source,
            media_type=media_type,
            title=getattr(result, 'title', 'Unknown'),
            artist=getattr(result, 'artist', 'Unknown'),
            year=getattr(result, 'year', None),
            cover_url=getattr(result, 'cover_url', None),
            extra_info=self._get_extra_info(result, media_type)
        )

    def _get_extra_info(self, result, media_type: str) -> str:
        """Extract extra information based on media type."""
        if media_type == 'album':
            track_count = getattr(result, 'track_count', 0)
            return f"{track_count} tracks"
        elif media_type == 'playlist':
            track_count = getattr(result, 'track_count', 0)
            return f"{track_count} tracks"
        elif media_type == 'artist':
            album_count = getattr(result, 'album_count', 0)
            return f"{album_count} albums"
        elif media_type == 'track':
            duration = getattr(result, 'duration', 0)
            return f"{duration // 60}:{duration % 60:02d}"
        return ""

    def get_last_results(self) -> List[SearchResult]:
        """Get the last search results."""
        return self._last_results
```

---

## 6. GUI Components

### 6.1 Main Window

**`src/ui/main_window.py`**

```python
"""
Main application window.
"""
import logging
from typing import Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QTabWidget,
    QMenuBar, QMenu, QToolBar, QStatusBar,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from streamrip.config import Config
from services.download_service import DownloadService, DownloadStatus
from services.search_service import SearchService
from services.auth_service import AuthService
from utils.async_helper import AsyncRunner
from ui.queue_widget import QueueWidget
from ui.search_dialog import SearchDialog
from ui.settings_dialog import SettingsDialog
from ui.login_dialog import LoginDialog
from ui.about_dialog import AboutDialog


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, config: Config, event_loop):
        super().__init__()
        self.config = config
        self.event_loop = event_loop

        # Services
        self.download_service = DownloadService(config, event_loop)
        self.search_service = SearchService(config, event_loop)
        self.auth_service = AuthService(config, event_loop)
        self.async_runner = AsyncRunner(event_loop)

        # Initialize UI
        self._init_ui()
        self._connect_signals()

        # Initialize services
        self.async_runner.run_coroutine(
            self._initialize_services(),
            on_success=self._on_services_ready,
            on_error=self._on_services_error
        )

    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Streamrip Desktop")
        self.setMinimumSize(900, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Add URL input section
        layout.addLayout(self._create_url_input())

        # Add tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Queue tab
        self.queue_widget = QueueWidget(self.download_service)
        self.tabs.addTab(self.queue_widget, "Download Queue")

        # Create menu bar
        self._create_menu_bar()

        # Create toolbar
        self._create_toolbar()

        # Create status bar
        self._create_status_bar()

        # Apply theme
        self._apply_theme()

    def _create_url_input(self) -> QHBoxLayout:
        """Create URL input section."""
        layout = QHBoxLayout()

        # Label
        label = QLabel("URL:")
        layout.addWidget(label)

        # URL input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "Enter URL (album, track, playlist, artist)..."
        )
        self.url_input.returnPressed.connect(self._on_download_clicked)
        layout.addWidget(self.url_input, stretch=1)

        # Download button
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self._on_download_clicked)
        self.download_btn.setDefault(True)
        layout.addWidget(self.download_btn)

        # Search button
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self._on_search_clicked)
        layout.addWidget(self.search_btn)

        return layout

    def _create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        download_action = QAction("&Download URL...", self)
        download_action.setShortcut(QKeySequence.StandardKey.New)
        download_action.triggered.connect(self._on_download_clicked)
        file_menu.addAction(download_action)

        search_action = QAction("&Search...", self)
        search_action.setShortcut(QKeySequence("Ctrl+F"))
        search_action.triggered.connect(self._on_search_clicked)
        file_menu.addAction(search_action)

        file_menu.addSeparator()

        settings_action = QAction("Se&ttings...", self)
        settings_action.setShortcut(QKeySequence.StandardKey.Preferences)
        settings_action.triggered.connect(self._on_settings_clicked)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        clear_queue_action = QAction("&Clear Queue", self)
        clear_queue_action.triggered.connect(self._on_clear_queue)
        edit_menu.addAction(clear_queue_action)

        # Downloads menu
        downloads_menu = menubar.addMenu("&Downloads")

        start_queue_action = QAction("&Start Queue", self)
        start_queue_action.setShortcut(QKeySequence("Ctrl+R"))
        start_queue_action.triggered.connect(self._on_start_queue)
        downloads_menu.addAction(start_queue_action)

        stop_queue_action = QAction("S&top Queue", self)
        stop_queue_action.setShortcut(QKeySequence("Ctrl+T"))
        stop_queue_action.triggered.connect(self._on_stop_queue)
        downloads_menu.addAction(stop_queue_action)

        downloads_menu.addSeparator()

        open_folder_action = QAction("&Open Download Folder", self)
        open_folder_action.triggered.connect(self._on_open_download_folder)
        downloads_menu.addAction(open_folder_action)

        # Account menu
        account_menu = menubar.addMenu("&Account")

        login_qobuz_action = QAction("Login to &Qobuz...", self)
        login_qobuz_action.triggered.connect(lambda: self._on_login('qobuz'))
        account_menu.addAction(login_qobuz_action)

        login_tidal_action = QAction("Login to &Tidal...", self)
        login_tidal_action.triggered.connect(lambda: self._on_login('tidal'))
        account_menu.addAction(login_tidal_action)

        login_deezer_action = QAction("Login to &Deezer...", self)
        login_deezer_action.triggered.connect(lambda: self._on_login('deezer'))
        account_menu.addAction(login_deezer_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About Streamrip Desktop", self)
        about_action.triggered.connect(self._on_about_clicked)
        help_menu.addAction(about_action)

        docs_action = QAction("&Documentation", self)
        docs_action.triggered.connect(self._on_docs_clicked)
        help_menu.addAction(docs_action)

    def _create_toolbar(self):
        """Create toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Add actions to toolbar
        download_action = QAction("Download", self)
        download_action.triggered.connect(self._on_download_clicked)
        toolbar.addAction(download_action)

        search_action = QAction("Search", self)
        search_action.triggered.connect(self._on_search_clicked)
        toolbar.addAction(search_action)

        toolbar.addSeparator()

        start_action = QAction("Start", self)
        start_action.triggered.connect(self._on_start_queue)
        toolbar.addAction(start_action)

        stop_action = QAction("Stop", self)
        stop_action.triggered.connect(self._on_stop_queue)
        toolbar.addAction(stop_action)

    def _create_status_bar(self):
        """Create status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _apply_theme(self):
        """Apply application theme."""
        # Load stylesheet
        theme_path = Path(__file__).parent.parent / 'resources' / 'styles' / 'light.qss'
        if theme_path.exists():
            with open(theme_path) as f:
                self.setStyleSheet(f.read())

    def _connect_signals(self):
        """Connect service signals to slots."""
        # Download service signals
        self.download_service.download_added.connect(self._on_download_added)
        self.download_service.download_started.connect(self._on_download_started)
        self.download_service.download_completed.connect(self._on_download_completed)
        self.download_service.download_failed.connect(self._on_download_failed)
        self.download_service.queue_completed.connect(self._on_queue_completed)

    async def _initialize_services(self):
        """Initialize all services."""
        await self.download_service.initialize()
        await self.search_service.initialize()
        await self.auth_service.initialize()

    def _on_services_ready(self, result):
        """Called when services are initialized."""
        logger.info("All services initialized successfully")
        self.status_bar.showMessage("Ready to download")

    def _on_services_error(self, error: Exception):
        """Called when service initialization fails."""
        logger.error(f"Service initialization failed: {error}")
        QMessageBox.critical(
            self,
            "Initialization Error",
            f"Failed to initialize services:\n{error}"
        )

    @pyqtSlot()
    def _on_download_clicked(self):
        """Handle download button click."""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(
                self,
                "No URL",
                "Please enter a URL to download."
            )
            return

        # Add to download queue
        self.download_service.add_url(url)
        self.url_input.clear()

        # Start queue if not running
        status = self.download_service.get_queue_status()
        if not status['is_running']:
            self._on_start_queue()

    @pyqtSlot()
    def _on_search_clicked(self):
        """Handle search button click."""
        dialog = SearchDialog(self.search_service, self.download_service, self)
        dialog.exec()

    @pyqtSlot()
    def _on_settings_clicked(self):
        """Handle settings button click."""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            # Reload configuration
            self.config = dialog.get_config()
            logger.info("Configuration updated")

    @pyqtSlot()
    def _on_start_queue(self):
        """Start download queue."""
        self.async_runner.run_coroutine(
            self.download_service.start_queue()
        )
        self.status_bar.showMessage("Download queue started")

    @pyqtSlot()
    def _on_stop_queue(self):
        """Stop download queue."""
        self.download_service.stop_queue()
        self.status_bar.showMessage("Download queue stopped")

    @pyqtSlot()
    def _on_clear_queue(self):
        """Clear download queue."""
        reply = QMessageBox.question(
            self,
            "Clear Queue",
            "Are you sure you want to clear the download queue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.download_service.clear_queue()
            self.status_bar.showMessage("Queue cleared")

    @pyqtSlot()
    def _on_open_download_folder(self):
        """Open download folder in file manager."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl

        folder = self.config.session.downloads.folder
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    @pyqtSlot(str)
    def _on_login(self, service: str):
        """Handle login to streaming service."""
        dialog = LoginDialog(service, self.auth_service, self)
        dialog.exec()

    @pyqtSlot()
    def _on_about_clicked(self):
        """Show about dialog."""
        dialog = AboutDialog(self)
        dialog.exec()

    @pyqtSlot()
    def _on_docs_clicked(self):
        """Open documentation in browser."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl

        QDesktopServices.openUrl(
            QUrl("https://github.com/nathom/streamrip/wiki")
        )

    @pyqtSlot(object)
    def _on_download_added(self, item):
        """Handle download added to queue."""
        logger.info(f"Download added: {item.url}")

    @pyqtSlot(object)
    def _on_download_started(self, item):
        """Handle download started."""
        logger.info(f"Download started: {item.url}")
        self.status_bar.showMessage(f"Downloading: {item.title or item.url}")

    @pyqtSlot(object)
    def _on_download_completed(self, item):
        """Handle download completed."""
        logger.info(f"Download completed: {item.url}")
        # Could show notification here

    @pyqtSlot(object, Exception)
    def _on_download_failed(self, item, error):
        """Handle download failed."""
        logger.error(f"Download failed: {item.url} - {error}")
        QMessageBox.warning(
            self,
            "Download Failed",
            f"Failed to download {item.url}:\n{error}"
        )

    @pyqtSlot()
    def _on_queue_completed(self):
        """Handle queue completed."""
        logger.info("Download queue completed")
        self.status_bar.showMessage("All downloads completed")
        # Could show notification here

    def closeEvent(self, event):
        """Handle window close event."""
        # Check if downloads are in progress
        status = self.download_service.get_queue_status()
        if status['active'] > 0:
            reply = QMessageBox.question(
                self,
                "Downloads in Progress",
                "Downloads are still in progress. Are you sure you want to quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        # Cleanup services
        self.async_runner.run_coroutine(self._cleanup_services())
        event.accept()

    async def _cleanup_services(self):
        """Cleanup all services."""
        await self.download_service.cleanup()
        await self.search_service.cleanup()
        await self.auth_service.cleanup()
```

---

*This guide continues with sections 7-15 covering remaining implementation details...*

**Due to length constraints, the remaining sections (Async Integration, Configuration Management, Download Queue, OAuth, Progress Tracking, FFmpeg, Database, Error Handling, and Packaging) would follow similar detailed patterns with:**

- Complete code examples
- Signal/slot connections
- Async/await integration
- Qt-specific patterns
- Platform-specific considerations

**Total estimated guide length: ~3,500 lines across all sections**

Would you like me to continue with specific sections, or would you prefer the packaging and distribution details next?
