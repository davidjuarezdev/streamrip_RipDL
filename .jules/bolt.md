## 2025-03-20 - Database Connection Pooling
**Learning:** `streamrip/db.py` creates a new `sqlite3.connect` for *every single database operation* (`contains`, `add`, `all`). In bulk operations like resolving a playlist with hundreds of tracks, this introduces significant overhead.
**Action:** Use a single persistent connection per database instance instead of creating a new one on every method call.

## 2026-03-20 - Non-blocking I/O in Deezer client
**Learning:** `streamrip/client/deezer.py` uses the synchronous `deezer-python` library. Direct calls like `client.gw.get_track()` and `client.get_track_url()` block the entire `asyncio` event loop. While the metadata fetching methods (`get_track`, `get_album`, etc.) correctly wrapped these calls in `await asyncio.to_thread(...)`, `get_downloadable` missed this, causing heavy blocking during concurrent downloads.
**Action:** Ensure all synchronous third-party API calls in async methods are wrapped with `await asyncio.to_thread(...)`.
## 2025-03-20 - Non-blocking concurrent requests with asyncio.as_completed
**Learning:** In `streamrip/client/qobuz.py`, when testing a list of potential app secrets, `asyncio.gather` was used, which waits for *all* test requests to complete before returning the first valid secret. By migrating to `asyncio.as_completed`, the application can short-circuit the network I/O validation process and cancel the remaining pending requests as soon as the first valid secret is found. This saves time and avoids unnecessary network calls.
**Action:** Prefer `asyncio.as_completed` over `asyncio.gather` for concurrent requests when only the first successful response is needed, ensuring to cancel any pending tasks to free up resources.
