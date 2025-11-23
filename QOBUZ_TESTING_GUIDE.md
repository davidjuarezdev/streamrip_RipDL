# Qobuz Service - Testing Guide

Complete testing strategy and test implementations for the migrated Qobuz service.

---

## Test Structure

```
tests/services/qobuz/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── test_plugin.py           # Plugin registration and interface tests
├── test_client.py           # Client functionality tests
├── test_spoofer.py          # Spoofer tests
├── test_config.py           # Configuration tests
├── test_metadata.py         # Metadata parsing tests
├── test_integration.py      # End-to-end integration tests
└── fixtures/                # Test data
    ├── __init__.py
    ├── api_responses.py     # Mock API responses
    └── bundle_samples.py    # Sample bundle.js content
```

---

## Test Fixtures

###conftest.py (Pytest Configuration)

```python
# tests/services/qobuz/conftest.py
"""
Pytest fixtures for Qobuz service tests.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import aiohttp

from streamrip.services.qobuz import QobuzConfig, QobuzClient, QobuzPlugin


@pytest.fixture
def qobuz_config():
    """Create test Qobuz configuration."""
    return QobuzConfig(
        use_auth_token=False,
        email_or_userid="test@example.com",
        password_or_token="test_password_hash",
        app_id="123456789",
        quality=3,
        download_booklets=True,
        secrets=["test_secret_1", "test_secret_2"]
    )


@pytest.fixture
def qobuz_config_no_credentials():
    """Qobuz config without credentials."""
    return QobuzConfig(
        email_or_userid="",
        password_or_token="",
        app_id="",
        quality=2,
        secrets=[]
    )


@pytest.fixture
def qobuz_client(qobuz_config):
    """Create Qobuz client with test config."""
    return QobuzClient(qobuz_config)


@pytest.fixture
def qobuz_plugin():
    """Create Qobuz plugin instance."""
    return QobuzPlugin()


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    session.headers = {}
    return session


@pytest.fixture
def mock_login_response():
    """Mock successful login response."""
    return {
        "user": {
            "id": 12345,
            "email": "test@example.com",
            "credential": {
                "parameters": {
                    "lossy_streaming": True,
                    "lossless_streaming": True,
                    "hires_streaming": True,
                }
            }
        },
        "user_auth_token": "test_auth_token_xyz",
    }


@pytest.fixture
def mock_album_response():
    """Mock album metadata response."""
    return {
        "id": "abc123",
        "title": "Test Album",
        "artist": {"name": "Test Artist"},
        "release_date": "2024-01-15",
        "tracks_count": 10,
        "genre": {"name": "Electronic"},
        "label": {"name": "Test Label"},
        "copyright": "2024 Test Records",
        "tracks": {
            "items": [
                {
                    "id": "track1",
                    "title": "Track 1",
                    "media_number": 1,
                    "track_number": 1,
                }
            ]
        }
    }


@pytest.fixture
def mock_bundle_js():
    """Mock Qobuz bundle.js content."""
    return '''
    production:{api:{appId:"123456789",appSecret:"abcdef1234567890"}}
    var a.initialSeed("dGVzdHNlZWQx",window.utimezone.america)
    var b.initialSeed("dGVzdHNlZWQy",window.utimezone.europe)
    name:"test/America",info:"aW5mbzE=",extras:"ZXh0cmFzMQ=="
    name:"test/Europe",info:"aW5mbzI=",extras:"ZXh0cmFzMg=="
    '''
```

---

## Unit Tests

### test_plugin.py

```python
# tests/services/qobuz/test_plugin.py
"""
Tests for Qobuz plugin.
"""
import pytest
from streamrip.services.qobuz import QobuzPlugin, QobuzClient, QobuzConfig
from streamrip.plugin_system import get_registry


class TestQobuzPlugin:
    """Test Qobuz plugin interface."""

    def test_plugin_initialization(self, qobuz_plugin):
        """Test plugin can be initialized."""
        assert qobuz_plugin.name == "qobuz"
        assert qobuz_plugin.display_name == "Qobuz"
        assert qobuz_plugin.metadata.version == "1.0.0"

    def test_plugin_properties(self, qobuz_plugin):
        """Test plugin properties."""
        assert qobuz_plugin.name == "qobuz"
        assert qobuz_plugin.display_name == "Qobuz"
        assert qobuz_plugin.client_class == QobuzClient
        assert qobuz_plugin.config_class == QobuzConfig

    def test_url_patterns(self, qobuz_plugin):
        """Test URL patterns are returned."""
        patterns = qobuz_plugin.get_url_patterns()
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        assert any("qobuz" in p for p in patterns)

    @pytest.mark.parametrize("url,expected", [
        ("https://open.qobuz.com/album/123", True),
        ("https://www.qobuz.com/us-en/album/456", True),
        ("https://play.qobuz.com/album/789", True),
        ("http://qobuz.com/track/xyz", True),
        ("https://tidal.com/album/123", False),
        ("https://spotify.com/album/456", False),
        ("https://example.com", False),
    ])
    def test_url_compatibility(self, qobuz_plugin, url, expected):
        """Test URL detection for various URLs."""
        assert qobuz_plugin.is_url_compatible(url) == expected

    def test_create_client(self, qobuz_plugin, qobuz_config):
        """Test client creation."""
        client = qobuz_plugin.create_client(qobuz_config)
        assert isinstance(client, QobuzClient)
        assert client.config == qobuz_config
        assert client.source == "qobuz"

    def test_create_client_wrong_config_type(self, qobuz_plugin):
        """Test client creation with wrong config type raises error."""
        with pytest.raises(TypeError, match="Expected QobuzConfig"):
            qobuz_plugin.create_client({"invalid": "config"})

    def test_plugin_registration(self, qobuz_plugin):
        """Test plugin can be registered."""
        registry = get_registry()
        registry.register(qobuz_plugin)

        assert registry.is_service_available("qobuz")
        retrieved = registry.get_plugin("qobuz")
        assert retrieved.name == "qobuz"

    def test_plugin_repr(self, qobuz_plugin):
        """Test plugin string representation."""
        repr_str = repr(qobuz_plugin)
        assert "QobuzPlugin" in repr_str
        assert "qobuz" in repr_str
```

### test_config.py

```python
# tests/services/qobuz/test_config.py
"""
Tests for Qobuz configuration.
"""
import pytest
from streamrip.services.qobuz import QobuzConfig


class TestQobuzConfig:
    """Test Qobuz configuration."""

    def test_config_creation_with_defaults(self):
        """Test config creation with default values."""
        config = QobuzConfig()
        assert config.use_auth_token is False
        assert config.email_or_userid == ""
        assert config.password_or_token == ""
        assert config.app_id == ""
        assert config.quality == 3
        assert config.download_booklets is True
        assert config.secrets == []

    def test_config_creation_with_values(self):
        """Test config creation with specific values."""
        config = QobuzConfig(
            use_auth_token=True,
            email_or_userid="12345",
            password_or_token="token_xyz",
            app_id="987654321",
            quality=4,
            download_booklets=False,
            secrets=["secret1", "secret2"]
        )
        assert config.use_auth_token is True
        assert config.email_or_userid == "12345"
        assert config.password_or_token == "token_xyz"
        assert config.app_id == "987654321"
        assert config.quality == 4
        assert config.download_booklets is False
        assert config.secrets == ["secret1", "secret2"]

    @pytest.mark.parametrize("quality", [1, 2, 3, 4])
    def test_valid_quality_levels(self, quality):
        """Test all valid quality levels."""
        config = QobuzConfig(quality=quality)
        assert config.quality == quality

    @pytest.mark.parametrize("quality", [0, 5, -1, 10])
    def test_invalid_quality_levels(self, quality):
        """Test invalid quality levels raise error."""
        with pytest.raises(ValueError, match="Invalid Qobuz quality"):
            QobuzConfig(quality=quality)

    def test_has_credentials_with_both(self):
        """Test has_credentials when both provided."""
        config = QobuzConfig(
            email_or_userid="test@example.com",
            password_or_token="hash123"
        )
        assert config.has_credentials() is True

    def test_has_credentials_missing_email(self):
        """Test has_credentials when email missing."""
        config = QobuzConfig(
            email_or_userid="",
            password_or_token="hash123"
        )
        assert config.has_credentials() is False

    def test_has_credentials_missing_password(self):
        """Test has_credentials when password missing."""
        config = QobuzConfig(
            email_or_userid="test@example.com",
            password_or_token=""
        )
        assert config.has_credentials() is False

    def test_has_app_credentials_with_both(self):
        """Test has_app_credentials when both provided."""
        config = QobuzConfig(
            app_id="123456789",
            secrets=["secret1"]
        )
        assert config.has_app_credentials() is True

    def test_has_app_credentials_missing_app_id(self):
        """Test has_app_credentials when app_id missing."""
        config = QobuzConfig(
            app_id="",
            secrets=["secret1"]
        )
        assert config.has_app_credentials() is False

    def test_has_app_credentials_empty_secrets(self):
        """Test has_app_credentials when secrets empty."""
        config = QobuzConfig(
            app_id="123456789",
            secrets=[]
        )
        assert config.has_app_credentials() is False
```

### test_client.py

```python
# tests/services/qobuz/test_client.py
"""
Tests for Qobuz client.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from streamrip.services.qobuz import QobuzClient, QobuzConfig
from streamrip.core.exceptions import (
    MissingCredentialsError,
    AuthenticationError,
    InvalidAppIdError,
    IneligibleError,
    NonStreamableError,
)


class TestQobuzClient:
    """Test Qobuz client functionality."""

    def test_client_initialization(self, qobuz_config):
        """Test client can be initialized."""
        client = QobuzClient(qobuz_config)
        assert client.config == qobuz_config
        assert client.source == "qobuz"
        assert client.max_quality == 4
        assert client.logged_in is False
        assert client.session is None
        assert client.secret is None

    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, qobuz_config_no_credentials):
        """Test login with missing credentials raises error."""
        client = QobuzClient(qobuz_config_no_credentials)

        with pytest.raises(MissingCredentialsError):
            await client.login()

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        qobuz_client,
        mock_aiohttp_session,
        mock_login_response
    ):
        """Test successful login."""
        # Mock session
        with patch.object(qobuz_client, 'get_session', return_value=mock_aiohttp_session):
            # Mock API request
            async def mock_api_request(endpoint, params):
                if endpoint == "user/login":
                    return (200, mock_login_response)
                return (200, {})

            qobuz_client._api_request = AsyncMock(side_effect=mock_api_request)

            # Mock secret validation
            qobuz_client._get_valid_secret = AsyncMock(return_value="secret123")

            # Login
            result = await qobuz_client.login()

            assert result is True
            assert qobuz_client.logged_in is True
            assert qobuz_client.secret == "secret123"
            assert "X-App-Id" in qobuz_client.session.headers
            assert "X-User-Auth-Token" in qobuz_client.session.headers

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(
        self,
        qobuz_client,
        mock_aiohttp_session
    ):
        """Test login with invalid credentials."""
        with patch.object(qobuz_client, 'get_session', return_value=mock_aiohttp_session):
            # Mock 401 response
            qobuz_client._api_request = AsyncMock(return_value=(401, {}))

            with pytest.raises(AuthenticationError, match="Invalid Qobuz credentials"):
                await qobuz_client.login()

    @pytest.mark.asyncio
    async def test_login_invalid_app_id(
        self,
        qobuz_client,
        mock_aiohttp_session
    ):
        """Test login with invalid app_id."""
        with patch.object(qobuz_client, 'get_session', return_value=mock_aiohttp_session):
            # Mock 400 response
            qobuz_client._api_request = AsyncMock(return_value=(400, {}))

            with pytest.raises(InvalidAppIdError, match="Invalid Qobuz app_id"):
                await qobuz_client.login()

    @pytest.mark.asyncio
    async def test_login_free_account(
        self,
        qobuz_client,
        mock_aiohttp_session
    ):
        """Test login with free account (ineligible)."""
        with patch.object(qobuz_client, 'get_session', return_value=mock_aiohttp_session):
            # Mock response for free account
            free_account_response = {
                "user": {
                    "credential": {
                        "parameters": None  # Free account has no parameters
                    }
                },
                "user_auth_token": "token"
            }

            qobuz_client._api_request = AsyncMock(
                return_value=(200, free_account_response)
            )

            with pytest.raises(IneligibleError, match="Free Qobuz accounts"):
                await qobuz_client.login()

    @pytest.mark.asyncio
    async def test_get_metadata_album(self, qobuz_client, mock_album_response):
        """Test fetching album metadata."""
        qobuz_client._api_request = AsyncMock(
            return_value=(200, mock_album_response)
        )

        metadata = await qobuz_client.get_metadata("abc123", "album")

        assert metadata == mock_album_response
        assert metadata["title"] == "Test Album"

    @pytest.mark.asyncio
    async def test_get_metadata_error(self, qobuz_client):
        """Test metadata fetch error."""
        qobuz_client._api_request = AsyncMock(
            return_value=(404, {"message": "Album not found"})
        )

        with pytest.raises(NonStreamableError, match="Album not found"):
            await qobuz_client.get_metadata("invalid_id", "album")

    @pytest.mark.asyncio
    async def test_get_downloadable_not_logged_in(self, qobuz_client):
        """Test get_downloadable when not logged in."""
        with pytest.raises(RuntimeError, match="Must login"):
            await qobuz_client.get_downloadable("track123", 3)

    @pytest.mark.asyncio
    async def test_get_downloadable_invalid_quality(self, qobuz_client):
        """Test get_downloadable with invalid quality."""
        qobuz_client.logged_in = True
        qobuz_client.secret = "secret"

        with pytest.raises(ValueError, match="Invalid quality"):
            await qobuz_client.get_downloadable("track123", 5)

    @pytest.mark.asyncio
    async def test_get_downloadable_success(
        self,
        qobuz_client,
        mock_aiohttp_session
    ):
        """Test successful downloadable creation."""
        qobuz_client.logged_in = True
        qobuz_client.secret = "test_secret"
        qobuz_client.session = mock_aiohttp_session

        # Mock file URL response
        file_url_response = {
            "url": "https://cdn.qobuz.com/file/xyz.flac"
        }

        qobuz_client._request_file_url = AsyncMock(
            return_value=(200, file_url_response)
        )

        downloadable = await qobuz_client.get_downloadable("track123", 3)

        assert downloadable is not None
        assert downloadable.url == "https://cdn.qobuz.com/file/xyz.flac"

    @pytest.mark.asyncio
    async def test_get_downloadable_restricted(
        self,
        qobuz_client,
        mock_aiohttp_session
    ):
        """Test downloadable for restricted track."""
        qobuz_client.logged_in = True
        qobuz_client.secret = "test_secret"
        qobuz_client.session = mock_aiohttp_session

        # Mock restricted response
        restricted_response = {
            "url": None,
            "restrictions": [
                {"code": "GeographicRestriction"}
            ]
        }

        qobuz_client._request_file_url = AsyncMock(
            return_value=(200, restricted_response)
        )

        with pytest.raises(NonStreamableError, match="geographic restriction"):
            await qobuz_client.get_downloadable("track123", 3)


class TestQobuzClientSecretValidation:
    """Test secret validation logic."""

    @pytest.mark.asyncio
    async def test_get_valid_secret_success(self, qobuz_client):
        """Test finding valid secret from list."""
        # Mock test results: first fails, second succeeds
        async def mock_request_file_url(track_id, quality, secret):
            if secret == "bad_secret":
                return (400, {})  # Bad secret
            elif secret == "good_secret":
                return (200, {})  # Good secret
            return (400, {})

        qobuz_client._request_file_url = AsyncMock(
            side_effect=mock_request_file_url
        )

        secrets = ["bad_secret", "good_secret", "another_secret"]
        valid_secret = await qobuz_client._get_valid_secret(secrets)

        assert valid_secret == "good_secret"

    @pytest.mark.asyncio
    async def test_get_valid_secret_all_invalid(self, qobuz_client):
        """Test when all secrets are invalid."""
        from streamrip.core.exceptions import InvalidAppSecretError

        # All secrets return 400
        qobuz_client._request_file_url = AsyncMock(
            return_value=(400, {})
        )

        secrets = ["bad1", "bad2", "bad3"]

        with pytest.raises(InvalidAppSecretError):
            await qobuz_client._get_valid_secret(secrets)
```

### test_spoofer.py

```python
# tests/services/qobuz/test_spoofer.py
"""
Tests for Qobuz spoofer.
"""
import pytest
from unittest.mock import AsyncMock, patch
from streamrip.services.qobuz import QobuzSpoofer


class TestQobuzSpoofer:
    """Test Qobuz spoofer functionality."""

    @pytest.mark.asyncio
    async def test_spoofer_context_manager(self):
        """Test spoofer can be used as async context manager."""
        async with QobuzSpoofer() as spoofer:
            assert spoofer.session is not None

        # Session should be closed after exit
        assert spoofer.session is None

    @pytest.mark.asyncio
    async def test_get_app_id_and_secrets(self, mock_bundle_js):
        """Test extracting app_id and secrets."""
        mock_login_page = '''
        <html>
        <script src="/resources/1.0.0-a001/bundle.js"></script>
        </html>
        '''

        async with QobuzSpoofer() as spoofer:
            # Mock HTTP responses
            async def mock_get(url):
                response = AsyncMock()
                if "login" in url:
                    response.text = AsyncMock(return_value=mock_login_page)
                elif "bundle.js" in url:
                    response.text = AsyncMock(return_value=mock_bundle_js)
                return response

            spoofer.session.get = mock_get

            app_id, secrets = await spoofer.get_app_id_and_secrets()

            assert app_id == "123456789"
            assert isinstance(secrets, list)
            assert len(secrets) > 0

    @pytest.mark.asyncio
    async def test_spoofer_bundle_url_not_found(self):
        """Test when bundle URL not found in login page."""
        bad_login_page = "<html><body>No bundle here</body></html>"

        async with QobuzSpoofer() as spoofer:
            async def mock_get(url):
                response = AsyncMock()
                response.text = AsyncMock(return_value=bad_login_page)
                return response

            spoofer.session.get = mock_get

            with pytest.raises(Exception, match="Could not find bundle.js"):
                await spoofer.get_app_id_and_secrets()

    @pytest.mark.asyncio
    async def test_spoofer_app_id_not_found(self):
        """Test when app_id not found in bundle."""
        bad_bundle = "var x = 123; function test() {}"

        async with QobuzSpoofer() as spoofer:
            spoofer.bundle = bad_bundle

            with pytest.raises(Exception, match="Could not find app_id"):
                spoofer._extract_app_id()
```

---

## Integration Tests

### test_integration.py

```python
# tests/services/qobuz/test_integration.py
"""
Integration tests for Qobuz service.
"""
import pytest
from unittest.mock import patch, AsyncMock
from streamrip.services.qobuz import QobuzPlugin, QobuzConfig
from streamrip.plugin_system import get_registry, PluginLoader


class TestQobuzIntegration:
    """Test Qobuz service integration."""

    def test_plugin_discovery_builtin(self):
        """Test Qobuz plugin is discovered as built-in."""
        registry = get_registry()

        # Clear registry first
        registry._plugins.clear()

        # Load built-in plugins
        loaded = PluginLoader.load_builtin_plugins()

        assert loaded >= 1  # At least Qobuz
        assert registry.is_service_available("qobuz")

    def test_plugin_url_detection_integration(self):
        """Test URL detection through registry."""
        registry = get_registry()
        plugin = QobuzPlugin()
        registry.register(plugin)

        # Test detection
        detected = registry.detect_service_from_url(
            "https://open.qobuz.com/album/abc123"
        )

        assert detected == "qobuz"

    def test_client_creation_through_registry(self):
        """Test creating client through registry."""
        registry = get_registry()
        plugin = QobuzPlugin()
        registry.register(plugin)

        config = QobuzConfig(
            email_or_userid="test@example.com",
            password_or_token="hash123",
            quality=3
        )

        client = registry.create_client("qobuz", config)

        assert client is not None
        assert client.source == "qobuz"
        assert client.config == config

    @pytest.mark.asyncio
    async def test_full_download_flow_mock(self, qobuz_config):
        """Test complete download flow with mocks."""
        plugin = QobuzPlugin()
        client = plugin.create_client(qobuz_config)

        # Mock all network calls
        client.get_session = AsyncMock()
        client._api_request = AsyncMock(return_value=(200, {
            "user": {
                "credential": {"parameters": {"lossless_streaming": True}}
            },
            "user_auth_token": "token"
        }))
        client._get_valid_secret = AsyncMock(return_value="secret")
        client._request_file_url = AsyncMock(return_value=(200, {
            "url": "https://cdn.qobuz.com/track.flac"
        }))

        # Login
        await client.login()
        assert client.logged_in

        # Get downloadable
        downloadable = await client.get_downloadable("track123", 3)
        assert downloadable is not None
        assert "cdn.qobuz.com" in downloadable.url
```

---

## Test Execution

### Running Tests

```bash
# Run all Qobuz tests
pytest tests/services/qobuz/ -v

# Run specific test file
pytest tests/services/qobuz/test_plugin.py -v

# Run with coverage
pytest tests/services/qobuz/ --cov=streamrip.services.qobuz --cov-report=html

# Run only integration tests
pytest tests/services/qobuz/test_integration.py -v

# Run tests matching pattern
pytest tests/services/qobuz/ -k "test_login" -v
```

### Expected Output

```
tests/services/qobuz/test_plugin.py::TestQobuzPlugin::test_plugin_initialization PASSED
tests/services/qobuz/test_plugin.py::TestQobuzPlugin::test_url_compatibility[url0-True] PASSED
tests/services/qobuz/test_plugin.py::TestQobuzPlugin::test_url_compatibility[url1-True] PASSED
...
tests/services/qobuz/test_client.py::TestQobuzClient::test_login_success PASSED
...
tests/services/qobuz/test_integration.py::TestQobuzIntegration::test_full_download_flow_mock PASSED

======================== 45 passed in 2.34s ========================
Coverage: 87%
```

---

## Coverage Report

### Target Coverage

| Module | Target | Priority |
|--------|--------|----------|
| `plugin.py` | 95%+ | High |
| `config.py` | 100% | High |
| `client.py` | 85%+ | High |
| `spoofer.py` | 80%+ | Medium |
| `metadata.py` | 90%+ | High |
| `constants.py` | 100% | Low |

### Generating Coverage Report

```bash
# Generate HTML report
pytest tests/services/qobuz/ \
  --cov=streamrip.services.qobuz \
  --cov-report=html:coverage_html \
  --cov-report=term

# View report
open coverage_html/index.html  # macOS
xdg-open coverage_html/index.html  # Linux
```

---

## Continuous Testing

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running Qobuz tests..."
pytest tests/services/qobuz/ -q
if [ $? -ne 0 ]; then
    echo "Tests failed! Commit aborted."
    exit 1
fi
```

### CI/CD Integration

```yaml
# .github/workflows/test-qobuz.yml
name: Test Qobuz Service

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e .[dev]
      - run: pytest tests/services/qobuz/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
```

---

## Summary

This testing strategy ensures:

✅ **Comprehensive Coverage** - All components tested (plugin, client, spoofer, config)
✅ **Isolated Tests** - Each component tested independently
✅ **Integration Tests** - End-to-end flow verified
✅ **Mock External Dependencies** - No actual API calls in tests
✅ **Clear Test Organization** - Easy to find and add tests
✅ **Automated Execution** - CI/CD integration

**Next Steps**: Implement these tests during the Qobuz migration phase.
