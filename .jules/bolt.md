## 2025-03-20 - Database Connection Pooling
**Learning:** `streamrip/db.py` creates a new `sqlite3.connect` for *every single database operation* (`contains`, `add`, `all`). In bulk operations like resolving a playlist with hundreds of tracks, this introduces significant overhead.
**Action:** Use a single persistent connection per database instance instead of creating a new one on every method call.

## 2026-03-20 - Non-blocking I/O in Deezer client
**Learning:** `streamrip/client/deezer.py` uses the synchronous `deezer-python` library. Direct calls like `client.gw.get_track()` and `client.get_track_url()` block the entire `asyncio` event loop. While the metadata fetching methods (`get_track`, `get_album`, etc.) correctly wrapped these calls in `await asyncio.to_thread(...)`, `get_downloadable` missed this, causing heavy blocking during concurrent downloads.
**Action:** Ensure all synchronous third-party API calls in async methods are wrapped with `await asyncio.to_thread(...)`.

## 2024-05-18 - [Optimizing concurrent API calls when only a single successful result is needed]
**Learning:** In Qobuz client authentication, we test multiple secrets concurrently. However, using `asyncio.gather` forced the application to wait for all 15+ network requests to finish, causing slow-tail latency and wasted bandwidth if one endpoint was slow or failing.
**Action:** Replace `asyncio.gather` with `asyncio.as_completed` when we only need the first valid response, and cancel the remaining pending tasks to save network I/O and short-circuit early.
