from dataclasses import dataclass

@dataclass(slots=True)
class QobuzConfig:
    use_auth_token: bool
    email_or_userid: str
    # This is an md5 hash of the plaintext password
    password_or_token: str
    # Do not change
    app_id: str
    quality: int
    # This will download booklet pdfs that are included with some albums
    download_booklets: bool
    # Do not change
    secrets: list[str]


@dataclass(slots=True)
class TidalConfig:
    # Do not change any of the fields below
    user_id: str
    country_code: str
    access_token: str
    refresh_token: str
    # Tokens last 1 week after refresh. This is the Unix timestamp of the expiration
    # time. If you haven't used streamrip in more than a week, you may have to log
    # in again using `rip config --tidal`
    token_expiry: str
    # 0: 256kbps AAC, 1: 320kbps AAC, 2: 16/44.1 "HiFi" FLAC, 3: 24/44.1 "MQA" FLAC
    quality: int
    # This will download videos included in Video Albums.
    download_videos: bool


@dataclass(slots=True)
class DeezerConfig:
    # An authentication cookie that allows streamrip to use your Deezer account
    # See https://github.com/nathom/streamrip/wiki/Finding-Your-Deezer-ARL-Cookie
    # for instructions on how to find this
    arl: str
    # 0, 1, or 2
    # This only applies to paid Deezer subscriptions. Those using deezloader
    # are automatically limited to quality = 1
    quality: int
    # If the target quality is not available, fallback to best quality available
    lower_quality_if_not_available: bool
    # This allows for free 320kbps MP3 downloads from Deezer
    # If an arl is provided, deezloader is never used
    use_deezloader: bool
    # This warns you when the paid deezer account is not logged in and rip falls
    # back to deezloader, which is unreliable
    deezloader_warnings: bool


@dataclass(slots=True)
class SoundcloudConfig:
    # This changes periodically, so it needs to be updated
    client_id: str
    app_version: str
    # Only 0 is available for now
    quality: int


@dataclass(slots=True)
class YoutubeConfig:
    # The path to download the videos to
    video_downloads_folder: str
    # Only 0 is available for now
    quality: int
    # Download the video along with the audio
    download_videos: bool


@dataclass(slots=True)
class DatabaseConfig:
    downloads_enabled: bool
    downloads_path: str
    failed_downloads_enabled: bool
    failed_downloads_path: str


@dataclass(slots=True)
class ConversionConfig:
    enabled: bool
    # FLAC, ALAC, OPUS, MP3, VORBIS, or AAC
    codec: str
    # In Hz. Tracks are downsampled if their sampling rate is greater than this.
    # Value of 48000 is recommended to maximize quality and minimize space
    sampling_rate: int
    # Only 16 and 24 are available. It is only applied when the bit depth is higher
    # than this value.
    bit_depth: int
    # Only applicable for lossy codecs
    lossy_bitrate: int


@dataclass(slots=True)
class QobuzDiscographyFilterConfig:
    # Remove Collectors Editions, live recordings, etc.
    extras: bool
    # Picks the highest quality out of albums with identical titles.
    repeats: bool
    # Remove EPs and Singles
    non_albums: bool
    # Remove albums whose artist is not the one requested
    features: bool
    # Skip non studio albums
    non_studio_albums: bool
    # Only download remastered albums
    non_remaster: bool


@dataclass(slots=True)
class ArtworkConfig:
    # Write the image to the audio file
    embed: bool
    # The size of the artwork to embed. Options: thumbnail, small, large, original.
    # "original" images can be up to 30MB, and may fail embedding.
    # Using "large" is recommended.
    embed_size: str
    # Both of these options limit the size of the embedded artwork. If their values
    # are larger than the actual dimensions of the image, they will be ignored.
    # If either value is -1, the image is left untouched.
    embed_max_width: int
    # Save the cover image at the highest quality as a seperate jpg file
    save_artwork: bool
    # If artwork is saved, downscale it to these dimensions, or ignore if -1
    saved_max_width: int


@dataclass(slots=True)
class MetadataConfig:
    # Sets the value of the 'ALBUM' field in the metadata to the playlist's name.
    # This is useful if your music library software organizes tracks based on album name.
    set_playlist_to_album: bool
    # If part of a playlist, sets the `tracknumber` field in the metadata to the track's
    # position in the playlist instead of its position in its album
    renumber_playlist_tracks: bool
    # The following metadata tags won't be applied
    # See https://github.com/nathom/streamrip/wiki/Metadata-Tag-Names for more info
    exclude: list[str]


@dataclass(slots=True)
class FilepathsConfig:
    # Create folders for single tracks within the downloads directory using the folder_format
    # template
    add_singles_to_folder: bool
    # Available keys: "albumartist", "title", "year", "bit_depth", "sampling_rate",
    # "container", "id", and "albumcomposer"
    folder_format: str
    # Available keys: "tracknumber", "artist", "albumartist", "composer", "title",
    # and "albumcomposer"
    track_format: str
    # Only allow printable ASCII characters in filenames.
    restrict_characters: bool
    # Truncate the filename if it is greater than 120 characters
    # Setting this to false may cause downloads to fail on some systems
    truncate_to: int


@dataclass(slots=True)
class DownloadsConfig:
    # Folder where tracks are downloaded to
    folder: str
    # Put Qobuz albums in a 'Qobuz' folder, Tidal albums in 'Tidal' etc.
    source_subdirectories: bool
    # Put tracks in an album with 2 or more discs into a subfolder named `Disc N`
    disc_subdirectories: bool
    # Download (and convert) tracks all at once, instead of sequentially.
    # If you are converting the tracks, or have fast internet, this will
    # substantially improve processing speed.
    concurrency: bool
    # The maximum number of tracks to download at once
    # If you have very fast internet, you will benefit from a higher value,
    # A value that is too high for your bandwidth may cause slowdowns
    max_connections: int
    requests_per_minute: int
    # Verify SSL certificates for API connections
    # Set to false if you encounter SSL certificate verification errors (not recommended)
    verify_ssl: bool


@dataclass(slots=True)
class LastFmConfig:
    # The source on which to search for the tracks.
    source: str
    # If no results were found with the primary source, the item is searched for
    # on this one.
    fallback_source: str


@dataclass(slots=True)
class CliConfig:
    # Print "Downloading {Album name}" etc. to screen
    text_output: bool
    # Show resolve, download progress bars
    progress_bars: bool
    # The maximum number of search results to show in the interactive menu
    max_search_results: int


@dataclass(slots=True)
class MiscConfig:
    version: str
    check_for_updates: bool
