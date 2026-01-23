import os
import pytest
from unittest.mock import Mock, patch
from util import arun

from streamrip.client.downloadable import DeezerDownloadable
from streamrip.client.deezer import DeezerClient
from streamrip.config import Config
from streamrip.exceptions import NonStreamableError

@pytest.fixture(scope="session")
def deezer_client():
    """Integration test fixture - requires DEEZER_ARL environment variable"""
    config = Config.defaults()
    config.session.deezer.arl = os.environ.get("DEEZER_ARL", "")
    config.session.deezer.quality = 2  # FLAC
    config.session.deezer.lower_quality_if_not_available = True
    client = DeezerClient(config)
    arun(client.login())

    yield client

    arun(client.session.close())

@pytest.fixture
def mock_deezer_client():
    """Unit test fixture - mocked client for fast testing"""
    config = Config.defaults()
    config.session.deezer.arl = "test_arl"
    config.session.deezer.quality = 2
    config.session.deezer.lower_quality_if_not_available = True

    client = DeezerClient(config)
    client.client = Mock()
    client.client.gw = Mock()
    client.session = Mock()

    return client


# ===== UNIT TESTS =====

def test_deezer_track_metadata_quality_selection():
    """Unit test: TrackMetadata.from_deezer sets quality to highest available"""
    from streamrip.metadata import AlbumMetadata, TrackMetadata

    # Mock album metadata
    mock_album_resp = {
        "id": "123",
        "title": "Test Album",
        "artist": {"name": "Test Artist", "id": "456"},
        "release_date": "2020-01-01",
        "genres": {"data": [{"name": "Pop"}]},
        "tracks": [{"disk_number": 1}],
        "cover_xl": "https://test.jpg",
        "cover_big": "https://test.jpg",
        "cover_medium": "https://test.jpg",
        "cover_small": "https://test.jpg",
        "nb_tracks": 1,
        "track_total": 1
    }
    album = AlbumMetadata.from_deezer(mock_album_resp)

    # Mock track response with mixed quality availability
    mock_track_resp = {
        "id": "789",
        "title": "Test Track",
        "isrc": "TEST123456789",
        "contributors": [{"name": "Test Artist", "id": "456"}],
        "track_position": 1,
        "disk_number": 1,
        "explicit_lyrics": False,
        "qualities": [
            "FILESIZE_MP3_128",  # Quality 0 available
            None,                # Quality 1 unavailable
            "FILESIZE_FLAC"      # Quality 2 available
        ]
    }

    # Create track metadata
    track = TrackMetadata.from_deezer(album, mock_track_resp)

    # Should select highest available quality (2 = FLAC)
    assert track.info.quality == 2
    assert track.info.streamable == True

    # Test with no qualities available
    mock_track_resp["qualities"] = [None, None, None]
    track_no_quality = TrackMetadata.from_deezer(album, mock_track_resp)
    assert track_no_quality.info.quality == 0  # Default fallback
    assert track_no_quality.info.streamable == False


def test_deezer_quality_mapping(mock_deezer_client):
    """Unit test: quality int correctly maps to Deezer format"""
    mock_track_info = {
        "FILESIZE_FLAC": 25000000,
        "FILESIZE_MP3_320": 5000000,
        "FILESIZE_MP3_128": 2000000,
        "TRACK_TOKEN": "test_token"
    }

    mock_deezer_client.client.gw.get_track.return_value = mock_track_info
    mock_deezer_client.client.get_track_url.return_value = "https://test.flac"

    with patch.object(mock_deezer_client, 'get_session'):
        # Test quality 2 (FLAC)
        downloadable = arun(mock_deezer_client.get_downloadable("123", quality=2))
        assert downloadable.quality == 2

        # Test quality 1 (MP3_320)
        mock_deezer_client.client.get_track_url.return_value = "https://test.mp3"
        downloadable = arun(mock_deezer_client.get_downloadable("123", quality=1))
        assert downloadable.quality == 1

        # Test quality 0 (MP3_128)
        downloadable = arun(mock_deezer_client.get_downloadable("123", quality=0))
        assert downloadable.quality == 0


def test_deezer_fallback_logic_with_mock_data(mock_deezer_client):
    """Unit test: fallback logic works with mocked track data"""
    # Mock track info where FLAC is unavailable but MP3_320 is available
    # quality_map: [(9, "MP3_128"), (3, "MP3_320"), (1, "FLAC")]
    # So FILESIZE_MP3_128 = quality 0, FILESIZE_MP3_320 = quality 1, FILESIZE_FLAC = quality 2
    mock_track_info = {
        "FILESIZE_FLAC": 0,      # FLAC unavailable (quality 2)
        "FILESIZE_MP3_320": 5000000, # MP3_320 available (quality 1)
        "FILESIZE_MP3_128": 2000000, # MP3_128 available (quality 0)
        "TRACK_TOKEN": "test_token"
    }

    # Mock the client methods
    mock_deezer_client.client.gw.get_track.return_value = mock_track_info
    mock_deezer_client.client.get_track_url.return_value = "https://test.mp3"

    # Test fallback behavior
    with patch.object(mock_deezer_client, 'get_session'):
        downloadable = arun(mock_deezer_client.get_downloadable("123", quality=2))

        # Should have fallen back to quality 1 (MP3_320) since FLAC is unavailable
        assert downloadable.quality == 1


def test_deezer_no_fallback_when_quality_available(mock_deezer_client):
    """Unit test: no fallback when requested quality is available"""
    # Mock track info where FLAC is available
    # quality_map: [(9, "MP3_128"), (3, "MP3_320"), (1, "FLAC")]
    mock_track_info = {
        "FILESIZE_FLAC": 25000000, # FLAC available (quality 2)
        "FILESIZE_MP3_320": 5000000,  # MP3_320 available (quality 1)
        "FILESIZE_MP3_128": 2000000,  # MP3_128 available (quality 0)
        "TRACK_TOKEN": "test_token"
    }

    mock_deezer_client.client.gw.get_track.return_value = mock_track_info
    mock_deezer_client.client.get_track_url.return_value = "https://test.flac"

    with patch.object(mock_deezer_client, 'get_session'):
        downloadable = arun(mock_deezer_client.get_downloadable("123", quality=2))

        # Should use requested quality 2 (FLAC)
        assert downloadable.quality == 2


def test_deezer_fallback_to_lowest_available_quality(mock_deezer_client):
    """Unit test: fallback walks down quality list until finding available quality"""
    # Mock track info where only MP3_128 is available
    # quality_map: [(9, "MP3_128"), (3, "MP3_320"), (1, "FLAC")]
    mock_track_info = {
        "FILESIZE_FLAC": 0,      # FLAC unavailable (quality 2)
        "FILESIZE_MP3_320": 0,      # MP3_320 unavailable (quality 1)
        "FILESIZE_MP3_128": 2000000, # MP3_128 available (quality 0)
        "TRACK_TOKEN": "test_token"
    }

    mock_deezer_client.client.gw.get_track.return_value = mock_track_info
    mock_deezer_client.client.get_track_url.return_value = "https://test.mp3"

    with patch.object(mock_deezer_client, 'get_session'):
        downloadable = arun(mock_deezer_client.get_downloadable("123", quality=2))

        # Should have fallen back to quality 0 (MP3_128) since higher qualities unavailable
        assert downloadable.quality == 0


def test_deezer_no_fallback_when_disabled(mock_deezer_client):
    """Unit test: no fallback when lower_quality_if_not_available is False"""
    # Disable fallback
    mock_deezer_client.config.lower_quality_if_not_available = False

    # Mock track info where FLAC is unavailable
    # quality_map: [(9, "MP3_128"), (3, "MP3_320"), (1, "FLAC")]
    mock_track_info = {
        "FILESIZE_FLAC": 0,      # FLAC unavailable (quality 2)
        "FILESIZE_MP3_320": 5000000, # MP3_320 available (quality 1)
        "FILESIZE_MP3_128": 2000000, # MP3_128 available (quality 0)
        "TRACK_TOKEN": "test_url"
    }

    mock_deezer_client.client.gw.get_track.return_value = mock_track_info
    mock_deezer_client.client.get_track_url.return_value = "https://test.mp3"

    # Should raise an error when requested quality is unavailable and fallback is disabled
    with patch.object(mock_deezer_client, 'get_session'):
        with pytest.raises(NonStreamableError, match="The requested quality 2 is not available and fallback is disabled"):
            arun(mock_deezer_client.get_downloadable("123", quality=2))


# ===== INTEGRATION TESTS =====

@pytest.mark.skipif(
    "DEEZER_ARL" not in os.environ, reason="Deezer ARL not found in env."
)
def test_deezer_get_track_metadata(deezer_client):
    """Integration test: verify track metadata contains highest available quality"""
    # Get track metadata which should contain highest available quality
    track_data = arun(deezer_client.get_track("77874822"))

    # Verify qualities array is populated
    assert "qualities" in track_data
    qualities = track_data["qualities"]
    assert len(qualities) == 3  # [MP3_128, MP3_320, FLAC]

    # Find highest available quality
    available_indices = [i for i, q in enumerate(qualities) if q is not None]
    assert len(available_indices) > 0, "Should have at least one available quality"
    highest_quality = max(available_indices)

    print(f"Track qualities: {qualities}")
    print(f"Highest available quality: {highest_quality}")

    # Test downloadable creation works with the metadata
    downloadable = arun(deezer_client.get_downloadable("77874822", quality=highest_quality))
    assert downloadable.quality == highest_quality
    assert downloadable.url.startswith("https://")
    assert arun(downloadable.size()) > 0


@pytest.mark.skipif(
    "DEEZER_ARL" not in os.environ, reason="Deezer ARL not found in env."
)
def test_deezer_fallback_actually_occurred(deezer_client):
    """Integration test: verify fallback works with real track 77874822"""
    # We know track 77874822 doesn't have FLAC available, so test fallback scenario
    downloadable = arun(deezer_client.get_downloadable("77874822", quality=2))

    # Since we requested FLAC (quality=2) but it's not available,
    # we should have fallen back to the next available quality (1 = MP3_320)
    assert downloadable.quality == 1, "Should have fallen back to MP3_320 when FLAC unavailable"
    print("Fallback occurred: FLAC unavailable, fell back to MP3_320")

    # Verify the URL is actually accessible and working
    assert downloadable.url.startswith("https://")
    assert downloadable._size > 0, "Downloadable should have a valid file size"
    assert downloadable.extension == "mp3", "MP3_320 should have .mp3 extension"
