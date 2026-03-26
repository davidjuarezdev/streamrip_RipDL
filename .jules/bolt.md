## 2025-03-20 - Database Connection Pooling
**Learning:** `streamrip/db.py` creates a new `sqlite3.connect` for *every single database operation* (`contains`, `add`, `all`). In bulk operations like resolving a playlist with hundreds of tracks, this introduces significant overhead.
**Action:** Use a single persistent connection per database instance instead of creating a new one on every method call.

## 2026-03-20 - Non-blocking I/O in Deezer client
**Learning:** `streamrip/client/deezer.py` uses the synchronous `deezer-python` library. Direct calls like `client.gw.get_track()` and `client.get_track_url()` block the entire `asyncio` event loop. While the metadata fetching methods (`get_track`, `get_album`, etc.) correctly wrapped these calls in `await asyncio.to_thread(...)`, `get_downloadable` missed this, causing heavy blocking during concurrent downloads.
**Action:** Ensure all synchronous third-party API calls in async methods are wrapped with `await asyncio.to_thread(...)`.

## 2026-03-21 - Non-blocking PIL image processing
**Learning:** Synchronous, CPU-bound tasks from third-party libraries (such as PIL image processing operations like `Image.open`, `image.resize`, `image.save`) within async functions (e.g. `downscale_image` in `download_artwork`) block the main asyncio event loop, slowing down concurrent operations.
**Action:** Wrap synchronous CPU-bound operations in async methods with `await asyncio.to_thread(...)` to prevent blocking the event loop.
