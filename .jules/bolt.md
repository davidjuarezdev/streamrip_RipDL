## 2025-03-20 - Database Connection Pooling
**Learning:** `streamrip/db.py` creates a new `sqlite3.connect` for *every single database operation* (`contains`, `add`, `all`). In bulk operations like resolving a playlist with hundreds of tracks, this introduces significant overhead.
**Action:** Use a single persistent connection per database instance instead of creating a new one on every method call.

## 2026-03-20 - Non-blocking I/O in Deezer client
**Learning:** `streamrip/client/deezer.py` uses the synchronous `deezer-python` library. Direct calls like `client.gw.get_track()` and `client.get_track_url()` block the entire `asyncio` event loop. While the metadata fetching methods (`get_track`, `get_album`, etc.) correctly wrapped these calls in `await asyncio.to_thread(...)`, `get_downloadable` missed this, causing heavy blocking during concurrent downloads.
**Action:** Ensure all synchronous third-party API calls in async methods are wrapped with `await asyncio.to_thread(...)`.

## 2025-03-20 - Synchronous Disk I/O Blocking Asyncio Loop
**Learning:** `mutagen`'s reading and writing of audio tags (like `FLAC(path)` or `audio.save()`) perform heavy, synchronous disk I/O operations. In an asynchronous context like `streamrip/metadata/tagger.py`'s `tag_file` function, running these synchronously blocks the entire asyncio event loop, causing concurrent downloads or API requests to stall during the tagging phase.
**Action:** Always wrap heavy synchronous disk I/O from third-party libraries (like Mutagen's loading/saving) in `await asyncio.to_thread(...)` to ensure the asyncio event loop remains non-blocking.
