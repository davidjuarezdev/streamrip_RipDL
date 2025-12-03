# Project Overview

This project is a command-line tool named `streamrip` for downloading music from various streaming services, including Qobuz, Tidal, Deezer, and SoundCloud. It is written in Python and utilizes `aiohttp` for asynchronous, concurrent downloads.

The project is structured as a Python package and uses Poetry for dependency management. The main application logic is located in the `streamrip` directory, with the command-line interface defined in `streamrip/rip/cli.py`. The core functionality is orchestrated by the `Main` class in `streamrip/rip/main.py`.

## Building and Running

The project uses Poetry for dependency management and packaging.

### Installation

To install the project and its dependencies, run the following command:

```bash
poetry install
```

### Running the application

The application can be run using the `rip` command, which is an entry point defined in `pyproject.toml`.

```bash
poetry run rip --help
```

This will show the main help page for the `streamrip` command-line tool.

### Running tests

The project uses `pytest` for testing. The tests are located in the `tests` directory. To run the tests, use the following command:

```bash
poetry run pytest
```

## Development Conventions

### Code Style

The project uses `black` for code formatting and `ruff` for linting. The configuration for these tools can be found in the `pyproject.toml` file.

To format the code, run:

```bash
poetry run black .
```

To check for linting errors, run:

```bash
poetry run ruff check .
```

### Contribution Guidelines

The `README.md` file contains a section on contributions. It encourages users to open issues and submit pull requests. It also specifies that pull requests should be made to the `dev` branch.
