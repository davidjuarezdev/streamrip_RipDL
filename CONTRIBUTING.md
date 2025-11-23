# Contributing to streamrip

First off, thank you for considering contributing to streamrip! It's people like you that make streamrip such a great tool.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Review Process](#review-process)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is expected to uphold a respectful and inclusive environment. Please:

- Be respectful and constructive in discussions
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the [existing issues](https://github.com/nathom/streamrip/issues) to avoid duplicates.

When creating a bug report, please use the **Bug Report** template and include:

- A clear and descriptive title
- Steps to reproduce the behavior
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment details (OS, Python version, streamrip version)
- Relevant logs (with sensitive information redacted)

**Important:** Always use the provided issue templates. Issues that don't follow the templates may be closed.

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. Use the **Feature Request** template and include:

- A clear and descriptive title
- Detailed description of the proposed feature
- Use cases and benefits
- Possible implementation approach (if you have ideas)
- Alternative solutions you've considered

### Contributing Code

We welcome code contributions! Here are some areas where you can help:

- **Bug fixes** - Fix reported issues
- **New features** - Implement requested features
- **Performance improvements** - Optimize existing code
- **Documentation** - Improve docs, add examples
- **Tests** - Increase test coverage
- **Refactoring** - Improve code quality

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Poetry (for dependency management)
- FFmpeg (optional, but recommended for testing)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/streamrip.git
   cd streamrip
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/nathom/streamrip.git
   ```

## Development Setup

### Install Poetry

```bash
# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

### Install Dependencies

```bash
# Install all dependencies (including dev dependencies)
poetry install

# Activate the virtual environment
poetry shell
```

### Install FFmpeg (Optional)

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Configure for Development

```bash
# Create a config file for testing
rip config open

# Use test credentials (do not use your main accounts)
```

## Development Workflow

### 1. Create a Branch

Always create a new branch for your changes:

```bash
# Sync with upstream
git fetch upstream
git checkout dev
git merge upstream/dev

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

**Branch Naming Conventions:**
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Test additions/improvements

### 2. Make Your Changes

- Write clean, readable code
- Follow the [coding standards](#coding-standards)
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 3. Test Your Changes

```bash
# Run tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_config.py

# Run with coverage
poetry run pytest --cov=streamrip --cov-report=html

# Check linting
poetry run ruff check streamrip

# Format code
poetry run ruff format streamrip
```

### 4. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add support for new streaming service

- Implement XYZ client class
- Add URL parsing for XYZ
- Add tests for XYZ integration
- Update documentation

Fixes #123"
```

**Commit Message Guidelines:**
- Use the imperative mood ("Add feature" not "Added feature")
- First line: brief summary (50 chars or less)
- Blank line, then detailed description if needed
- Reference issues with "Fixes #123" or "Closes #456"

### 5. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 6. Open a Pull Request

- Go to your fork on GitHub
- Click "New Pull Request"
- Target the `dev` branch (not `main`)
- Fill out the PR template completely
- Link related issues

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications. Use the provided tools:

```bash
# Format code with ruff
ruff format streamrip

# Check for linting issues
ruff check streamrip

# Fix auto-fixable issues
ruff check streamrip --fix
```

### Code Style Specifics

#### 1. Type Hints

Always use type hints for function parameters and return values:

```python
# Good
async def download_track(url: str, quality: int) -> Track:
    pass

# Avoid
async def download_track(url, quality):
    pass
```

#### 2. Async/Await

Use async/await for I/O operations:

```python
# Good
async def fetch_metadata(track_id: str) -> dict:
    async with self.session.get(url) as response:
        return await response.json()

# Avoid blocking I/O in async functions
async def read_file(path: str) -> str:
    # Bad: blocking I/O
    with open(path) as f:
        return f.read()

    # Good: async I/O
    async with aiofiles.open(path) as f:
        return await f.read()
```

#### 3. Error Handling

Use specific exceptions and handle errors appropriately:

```python
# Good
try:
    track = await client.get_track(track_id)
except AuthenticationError as e:
    logger.error(f"Authentication failed: {e}")
    raise
except NetworkError as e:
    logger.warning(f"Network error, retrying: {e}")
    await retry_with_backoff()

# Avoid bare except
try:
    track = await client.get_track(track_id)
except:  # Bad: catches everything
    pass
```

#### 4. Docstrings

Use docstrings for public functions and classes:

```python
async def download_album(self, album_id: str, quality: int = 2) -> Album:
    """Download an album from the streaming service.

    Args:
        album_id: The unique identifier for the album
        quality: Quality level (0-4, where 4 is highest)

    Returns:
        Album object with downloaded tracks

    Raises:
        AuthenticationError: If not logged in
        NonStreamableError: If album is not available
    """
    pass
```

#### 5. Logging

Use the logging module appropriately:

```python
import logging

logger = logging.getLogger("streamrip")

# Use appropriate levels
logger.debug("Detailed diagnostic information")
logger.info("General informational messages")
logger.warning("Warning messages")
logger.error("Error messages")
logger.critical("Critical errors")

# Use f-strings or lazy formatting
logger.info(f"Downloading {track.name}")  # Good
logger.info("Downloading %s", track.name)  # Also good
logger.info("Downloading " + track.name)  # Avoid
```

### Project Structure Guidelines

When adding new code:

- **Clients** → `streamrip/client/`
- **Media types** → `streamrip/media/`
- **Metadata handlers** → `streamrip/metadata/`
- **CLI commands** → `streamrip/rip/cli.py`
- **Utilities** → `streamrip/utils/`
- **Tests** → `tests/`

## Testing

### Writing Tests

All new features and bug fixes should include tests:

```python
import pytest
from streamrip.client import QobuzClient

@pytest.mark.asyncio
async def test_qobuz_login_success(mock_config):
    """Test successful Qobuz login."""
    client = QobuzClient(mock_config)
    await client.login()
    assert client.logged_in is True

@pytest.mark.asyncio
async def test_qobuz_login_failure(mock_config):
    """Test Qobuz login with invalid credentials."""
    client = QobuzClient(mock_config)
    with pytest.raises(AuthenticationError):
        await client.login()
```

### Test Organization

- **Unit tests** - Test individual functions/classes in isolation
- **Integration tests** - Test interactions between components
- **End-to-end tests** - Test complete workflows

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_config.py

# Run specific test
poetry run pytest tests/test_config.py::test_config_load

# Run with verbose output
poetry run pytest -v

# Run with coverage
poetry run pytest --cov=streamrip --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Test Coverage Goals

- Aim for >70% overall coverage
- Critical paths should have >90% coverage
- All bug fixes must include regression tests

## Submitting Changes

### Pull Request Process

1. **Update documentation** - If you changed functionality, update docs
2. **Add tests** - Ensure your changes are tested
3. **Run the test suite** - All tests must pass
4. **Update CHANGELOG** - Add entry under "Unreleased" section (if exists)
5. **Follow the PR template** - Fill out all sections

### Pull Request Template

Your PR should include:

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- List of changes made
- Be specific and clear

## Testing
- How did you test this?
- What tests were added?

## Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG updated (if applicable)
```

### What to Expect

- **Initial Review** - Maintainers will review within a few days
- **Feedback** - You may be asked to make changes
- **CI Checks** - All CI checks must pass (tests, linting, type checking)
- **Approval** - At least one maintainer approval required
- **Merge** - Maintainers will merge when ready

## Review Process

### For Reviewers

When reviewing PRs:

- Be respectful and constructive
- Test the changes locally if possible
- Check for edge cases and error handling
- Verify tests are comprehensive
- Ensure documentation is updated

### For Contributors

When receiving feedback:

- Be open to suggestions
- Ask questions if something is unclear
- Make requested changes promptly
- Respond to comments
- Push additional commits to the same branch

## Community

### Getting Help

- **GitHub Discussions** - Ask questions, share ideas
- **GitHub Issues** - Report bugs, request features
- **Wiki** - Read documentation and guides

### Recognition

Contributors are recognized in:

- Git commit history
- Release notes
- GitHub contributors page

### Stay Updated

- Watch the repository for updates
- Star the project to show support
- Follow development on the `dev` branch

## Development Tips

### Debugging

```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use debugger
import pdb; pdb.set_trace()

# Or with async
import asyncio
await asyncio.sleep(0)  # Breakpoint for async debugging
```

### Common Issues

**Issue: Tests fail with "No such file or directory"**
```bash
# Ensure you're in the project root
pwd
# Should show .../streamrip

# Install in development mode
poetry install
```

**Issue: Import errors**
```bash
# Activate virtual environment
poetry shell

# Verify installation
poetry run python -c "import streamrip; print(streamrip.__file__)"
```

**Issue: Linting errors**
```bash
# Auto-fix most issues
ruff check streamrip --fix

# Format code
ruff format streamrip
```

### Performance Testing

```bash
# Profile code
python -m cProfile -o output.prof rip url <URL>

# View results
python -m pstats output.prof
```

### Building Documentation

```bash
# If documentation is added in the future
cd docs
make html
open _build/html/index.html
```

## Additional Resources

- [Python AsyncIO Documentation](https://docs.python.org/3/library/asyncio.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)

## Questions?

If you have questions not covered here:

1. Check the [Wiki](https://github.com/nathom/streamrip/wiki/)
2. Search [existing issues](https://github.com/nathom/streamrip/issues)
3. Open a [new discussion](https://github.com/nathom/streamrip/discussions)

## Thank You!

Your contributions make streamrip better for everyone. We appreciate your time and effort!

---

**Last Updated:** 2025-11-23
**Contributing Guide Version:** 1.0
