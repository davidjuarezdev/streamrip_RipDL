## 2025-03-20 - Database Connection Pooling
**Learning:** `streamrip/db.py` creates a new `sqlite3.connect` for *every single database operation* (`contains`, `add`, `all`). In bulk operations like resolving a playlist with hundreds of tracks, this introduces significant overhead.
**Action:** Use a single persistent connection per database instance instead of creating a new one on every method call.

## 2026-03-20 - Non-blocking I/O in Deezer client
**Learning:** `streamrip/client/deezer.py` uses the synchronous `deezer-python` library. Direct calls like `client.gw.get_track()` and `client.get_track_url()` block the entire `asyncio` event loop. While the metadata fetching methods (`get_track`, `get_album`, etc.) correctly wrapped these calls in `await asyncio.to_thread(...)`, `get_downloadable` missed this, causing heavy blocking during concurrent downloads.
**Action:** Ensure all synchronous third-party API calls in async methods are wrapped with `await asyncio.to_thread(...)`.

## 2026-04-02 - Short-circuiting Async Requests
**Learning:** In `streamrip/client/qobuz.py`, `_get_valid_secret` was using `asyncio.gather` to test multiple potential API secrets. This forced the application to wait for the slowest secret test to complete before proceeding, causing unnecessary slow-tail latency and wasted network I/O.
**Action:** Use `asyncio.as_completed` to yield the first successful valid secret immediately, and explicitly cancel the remaining pending tasks in a `finally` block to prevent background task leakage.
