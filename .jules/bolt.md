## 2025-03-20 - Database Connection Pooling
**Learning:** `streamrip/db.py` creates a new `sqlite3.connect` for *every single database operation* (`contains`, `add`, `all`). In bulk operations like resolving a playlist with hundreds of tracks, this introduces significant overhead.
**Action:** Use a single persistent connection per database instance instead of creating a new one on every method call.

## 2026-03-20 - Non-blocking I/O in Deezer client
**Learning:** `streamrip/client/deezer.py` uses the synchronous `deezer-python` library. Direct calls like `client.gw.get_track()` and `client.get_track_url()` block the entire `asyncio` event loop. While the metadata fetching methods (`get_track`, `get_album`, etc.) correctly wrapped these calls in `await asyncio.to_thread(...)`, `get_downloadable` missed this, causing heavy blocking during concurrent downloads.
**Action:** Ensure all synchronous third-party API calls in async methods are wrapped with `await asyncio.to_thread(...)`.

## 2023-11-20 - Short-circuiting concurrent requests
**Learning:** `streamrip/client/qobuz.py` used `asyncio.gather()` to test multiple Qobuz app secrets concurrently. This caused all network requests to complete even if the first one succeeded, wasting time and network I/O.
**Action:** Use `asyncio.as_completed()` to iterate over tasks as they finish, returning early when a successful result is found. Crucially, always wrap this in a `try...finally` block to `.cancel()` any remaining pending tasks to avoid "Task was destroyed but it is pending!" errors and background leakage.
