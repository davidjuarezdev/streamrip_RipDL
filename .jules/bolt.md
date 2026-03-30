## 2025-03-20 - Database Connection Pooling
**Learning:** `streamrip/db.py` creates a new `sqlite3.connect` for *every single database operation* (`contains`, `add`, `all`). In bulk operations like resolving a playlist with hundreds of tracks, this introduces significant overhead.
**Action:** Use a single persistent connection per database instance instead of creating a new one on every method call.

## 2026-03-20 - Non-blocking I/O in Deezer client
**Learning:** `streamrip/client/deezer.py` uses the synchronous `deezer-python` library. Direct calls like `client.gw.get_track()` and `client.get_track_url()` block the entire `asyncio` event loop. While the metadata fetching methods (`get_track`, `get_album`, etc.) correctly wrapped these calls in `await asyncio.to_thread(...)`, `get_downloadable` missed this, causing heavy blocking during concurrent downloads.
**Action:** Ensure all synchronous third-party API calls in async methods are wrapped with `await asyncio.to_thread(...)`.

## 2025-03-30 - Short-circuiting concurrent asyncio requests
**Learning:** `streamrip/client/qobuz.py` was using `asyncio.gather()` to test a batch of app secrets in parallel. `gather()` waits for *all* tasks to finish, which leads to slow-tail latency and wasted network I/O when only the first successful response is needed.
**Action:** For concurrent tasks where only the first successful result is required, use `asyncio.as_completed()` and immediately `cancel()` the remaining pending tasks after the first valid response is received to save time and resources.
