## 2025-03-20 - Database Connection Pooling
**Learning:** `streamrip/db.py` creates a new `sqlite3.connect` for *every single database operation* (`contains`, `add`, `all`). In bulk operations like resolving a playlist with hundreds of tracks, this introduces significant overhead.
**Action:** Use a single persistent connection per database instance instead of creating a new one on every method call.

## 2026-03-20 - Non-blocking I/O in Deezer client
**Learning:** `streamrip/client/deezer.py` uses the synchronous `deezer-python` library. Direct calls like `client.gw.get_track()` and `client.get_track_url()` block the entire `asyncio` event loop. While the metadata fetching methods (`get_track`, `get_album`, etc.) correctly wrapped these calls in `await asyncio.to_thread(...)`, `get_downloadable` missed this, causing heavy blocking during concurrent downloads.
**Action:** Ensure all synchronous third-party API calls in async methods are wrapped with `await asyncio.to_thread(...)`.

## 2026-04-03 - Optimizing the first matching concurrent tasks
**Learning:** `streamrip/client/qobuz.py` checks multiple potential app secrets to find one that works. Previously it used `asyncio.gather`, which waited for *all* requests to complete (even the slow timeouts or failing ones) before checking the results and taking the first valid one. Since we only need the *first* successful response, `asyncio.as_completed` allows us to short-circuit the execution immediately when the first valid secret is found, drastically reducing latency by not waiting for the slowest request.
**Action:** Use `asyncio.as_completed` with task cancellation (`try...finally` block cancelling all unfinished tasks) when concurrently fetching data where only the first valid response is needed.
