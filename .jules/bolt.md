## 2025-03-20 - Database Connection Pooling
**Learning:** `streamrip/db.py` creates a new `sqlite3.connect` for *every single database operation* (`contains`, `add`, `all`). In bulk operations like resolving a playlist with hundreds of tracks, this introduces significant overhead.
**Action:** Use a single persistent connection per database instance instead of creating a new one on every method call.

## 2026-03-20 - Non-blocking I/O in Deezer client
**Learning:** `streamrip/client/deezer.py` uses the synchronous `deezer-python` library. Direct calls like `client.gw.get_track()` and `client.get_track_url()` block the entire `asyncio` event loop. While the metadata fetching methods (`get_track`, `get_album`, etc.) correctly wrapped these calls in `await asyncio.to_thread(...)`, `get_downloadable` missed this, causing heavy blocking during concurrent downloads.
**Action:** Ensure all synchronous third-party API calls in async methods are wrapped with `await asyncio.to_thread(...)`.

## 2024-03-31 - Network Requests early exit via as_completed
**Learning:** Using `asyncio.gather` for checking API secrets sequentially blocked execution until the slowest request finished (or failed), even if a valid secret was found instantly. Task cancellation combined with `asyncio.as_completed` prevents slow-tail latency and leakage of background tasks.
**Action:** When validating a list of items where only the first success matters, always use `asyncio.as_completed` and cancel remaining tasks within a `finally` block instead of waiting for all with `asyncio.gather`.
