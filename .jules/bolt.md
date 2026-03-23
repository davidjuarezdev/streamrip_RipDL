## 2025-03-20 - Database Connection Pooling
**Learning:** `streamrip/db.py` creates a new `sqlite3.connect` for *every single database operation* (`contains`, `add`, `all`). In bulk operations like resolving a playlist with hundreds of tracks, this introduces significant overhead.
**Action:** Use a single persistent connection per database instance instead of creating a new one on every method call.

## 2026-03-20 - Non-blocking I/O in Deezer client
**Learning:** `streamrip/client/deezer.py` uses the synchronous `deezer-python` library. Direct calls like `client.gw.get_track()` and `client.get_track_url()` block the entire `asyncio` event loop. While the metadata fetching methods (`get_track`, `get_album`, etc.) correctly wrapped these calls in `await asyncio.to_thread(...)`, `get_downloadable` missed this, causing heavy blocking during concurrent downloads.
**Action:** Ensure all synchronous third-party API calls in async methods are wrapped with `await asyncio.to_thread(...)`.

## 2023-10-27 - Offloading CPU-bound operations in async contexts
**Learning:** `streamrip/media/artwork.py` uses `PIL.Image.open` and `resize` within an async function (`download_artwork`). PIL operations are synchronous and CPU-bound, which completely blocks the `asyncio` event loop while processing image resizing.
**Action:** Always wrap synchronous, CPU-bound library calls (like PIL image resizing) in `await asyncio.to_thread(...)` when executed inside an async context to prevent stalling other concurrent operations (like downloads).
