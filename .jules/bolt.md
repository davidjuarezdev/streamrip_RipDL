## 2025-03-20 - Database Connection Pooling
**Learning:** `streamrip/db.py` creates a new `sqlite3.connect` for *every single database operation* (`contains`, `add`, `all`). In bulk operations like resolving a playlist with hundreds of tracks, this introduces significant overhead.
**Action:** Use a single persistent connection per database instance instead of creating a new one on every method call.

## 2026-03-20 - Non-blocking I/O in Deezer client
**Learning:** `streamrip/client/deezer.py` uses the synchronous `deezer-python` library. Direct calls like `client.gw.get_track()` and `client.get_track_url()` block the entire `asyncio` event loop. While the metadata fetching methods (`get_track`, `get_album`, etc.) correctly wrapped these calls in `await asyncio.to_thread(...)`, `get_downloadable` missed this, causing heavy blocking during concurrent downloads.
**Action:** Ensure all synchronous third-party API calls in async methods are wrapped with `await asyncio.to_thread(...)`.

## 2025-03-25 - PIL Image operations block async event loops
**Learning:** `streamrip/media/artwork.py` performs CPU-bound synchronous operations using PIL (`Image.open`, `image.resize`, `image.save`) within the `downscale_image` function. When called directly from the async `download_artwork` function, it blocks the main `asyncio` event loop. This leads to substantial slowdowns when downloading playlists or albums where artwork needs downscaling, as other async network/I/O tasks are blocked from progressing.
**Action:** Always wrap synchronous, CPU-bound operations from third-party libraries (like image processing) in async functions with `await asyncio.to_thread(...)` to ensure the main event loop remains unblocked.
