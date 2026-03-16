# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Streamrip is an async music downloader for Qobuz, Tidal, Deezer, and SoundCloud. It's a CLI tool invoked via the `rip` command, built with Click and powered by `aiohttp` for concurrent downloads. Python 3.10-3.13.

## Build & Development Commands

```bash
# Install dependencies
poetry install

# Run all tests
poetry run pytest

# Run a single test file
poetry run pytest tests/test_config.py

# Run a specific test
poetry run pytest tests/test_config.py::test_name -v

# Lint
poetry run ruff check streamrip/
poetry run ruff format --check streamrip/

# Format
poetry run ruff format streamrip/

# Run the CLI
poetry run rip
```

## Architecture

### Data Pipeline

The core flow is: **URL → Parsed URL → Pending → Media → Downloadable → audio file**

- `rip/cli.py` — Click CLI entry point (`rip` command group). Uses `coro()` wrapper to run async code.
- `rip/main.py` — `Main` class orchestrates the full pipeline: client login, URL parsing, resolving pending items, downloading media.
- `rip/parse_url.py` — Parses streaming service URLs into structured objects with source/type/id.

### Client Layer (`client/`)

`Client` is the abstract base class. Each streaming service has its own implementation:
- `QobuzClient`, `TidalClient`, `DeezerClient`, `SoundcloudClient`
- Clients handle: login/auth, metadata fetching, search, and producing `Downloadable` objects
- Rate limiting via `aiolimiter`, sessions via `aiohttp`

### Media Layer (`media/`)

Two-phase pattern using abstract base classes:
- `Pending` — represents an unresolved download request. `resolve()` fetches metadata and returns a `Media`.
- `Media` — represents a resolved, downloadable item. `rip()` calls `preprocess()` → `download()` → `postprocess()`.
- Concrete types: `Track`, `Album`, `Artist`, `Playlist`, `Label` (each has a `Pending*` counterpart)

### Metadata Layer (`metadata/`)

Dataclasses that normalize metadata across sources: `AlbumMetadata`, `TrackMetadata`, `SearchResults`. Includes `tagger.py` for writing tags to audio files via `mutagen`.

### Other Key Modules

- `config.py` — Dataclass-based config loaded from TOML (`config.toml`). Uses `tomlkit` for round-trip parsing. Config lives at `click.get_app_dir("streamrip")/config.toml`.
- `db.py` — SQLite databases tracking downloaded and failed items to avoid re-downloads.
- `converter.py` — Audio format conversion via `ffmpeg`.
- `progress.py` — Rich-based progress bars for downloads.

## Testing

Tests use `pytest` with `pytest-asyncio` (auto mode — no need for `@pytest.mark.asyncio`). Fixtures are in `tests/fixtures/`. Some tests require network access and valid credentials (Qobuz, Deezer, Tidal tests).

## Code Style

- Formatter: Black-compatible (ruff format with double quotes, spaces)
- Linter: ruff with rules: E4, E7, E9, F, I, ASYNC, N, RUF, ERA001
- Async throughout — use `async/await`, not blocking I/O
- Windows compatibility: uses `WindowsSelectorEventLoopPolicy` on Windows; `pick` library instead of `simple-term-menu`

## Key Dependencies

- `aiohttp` / `aiofiles` — async HTTP and file I/O
- `click` + `click-help-colors` — CLI framework
- `rich` — terminal output, progress bars
- `mutagen` — audio metadata tagging
- `tomlkit` — config file parsing (preserves comments/formatting)
- `deezer-py` — Deezer API client
- `pycryptodomex` — Deezer track decryption
- `Pillow` — cover art processing
