## 2025-03-20 - Database Connection Pooling
**Learning:** `streamrip/db.py` creates a new `sqlite3.connect` for *every single database operation* (`contains`, `add`, `all`). In bulk operations like resolving a playlist with hundreds of tracks, this introduces significant overhead.
**Action:** Use a single persistent connection per database instance instead of creating a new one on every method call.

## 2025-03-20 - Non-Async API Calls Blocking the Event Loop
**Learning:** In `streamrip/client/deezer.py`, synchronous calls to `deezer-python` methods like `client.gw.get_track` were executing directly in `async` functions, completely blocking the asyncio event loop and preventing concurrent tasks.
**Action:** Use `await asyncio.to_thread(sync_function, *args)` around any synchronous library calls inside `async` functions to offload them to a background thread.
