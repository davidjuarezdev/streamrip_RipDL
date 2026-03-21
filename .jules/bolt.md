## 2025-03-20 - Database Connection Pooling
**Learning:** `streamrip/db.py` creates a new `sqlite3.connect` for *every single database operation* (`contains`, `add`, `all`). In bulk operations like resolving a playlist with hundreds of tracks, this introduces significant overhead.
**Action:** Use a single persistent connection per database instance instead of creating a new one on every method call.

## 2026-03-20 - Non-blocking I/O in Deezer client
**Learning:** `streamrip/client/deezer.py` uses the synchronous `deezer-python` library. Direct calls like `client.gw.get_track()` and `client.get_track_url()` block the entire `asyncio` event loop. While the metadata fetching methods (`get_track`, `get_album`, etc.) correctly wrapped these calls in `await asyncio.to_thread(...)`, `get_downloadable` missed this, causing heavy blocking during concurrent downloads.
**Action:** Ensure all synchronous third-party API calls in async methods are wrapped with `await asyncio.to_thread(...)`.
## 2026-03-21 - Concurrent API Pagination for Tidal
**Learning:** Tidal API provides `numberOfTracks` on the initial metadata request. Instead of walking the playlist pages sequentially (which takes O(N) network round-trips), we can calculate the exact offsets needed `range(100, total_tracks, 100)` and dispatch all remaining page fetches concurrently using `asyncio.gather`.
**Action:** When working with APIs that return the total count in the first request, always pre-calculate offsets and fetch the rest concurrently instead of paginating sequentially.
