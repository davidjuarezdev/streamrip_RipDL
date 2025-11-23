# Downloads Directory

This directory is where streamrip saves all downloaded music files.

## Structure

The directory structure is determined by your configuration in `config/config.toml`. Default structure:

```
downloads/
├── Artist Name/
│   ├── Album Name (Year) [Quality]/
│   │   ├── 01. Track Name.flac
│   │   ├── 02. Track Name.flac
│   │   └── cover.jpg
│   └── Another Album (Year) [Quality]/
│       └── ...
└── Another Artist/
    └── ...
```

## Customization

You can customize the folder and file naming patterns in `config/config.toml`:

```toml
[downloads]
folder = "{artist}/{album} ({year}) [{quality}]"
track = "{tracknumber}. {title}"
```

### Available Template Variables

- `{artist}` - Artist name
- `{album}` - Album name
- `{title}` - Track title
- `{year}` - Release year
- `{quality}` - Audio quality
- `{tracknumber}` - Track number
- `{genre}` - Music genre
- `{label}` - Record label

## Volume Mount

This directory is mounted from the host to the Docker container:
- **Host**: `./downloads`
- **Container**: `/home/streamrip/downloads`

## File Permissions

If you built the Docker image with your user ID, files will be owned by your user:

```bash
# Check ownership
ls -la downloads/

# If permissions are wrong, rebuild with correct user ID
USER_ID=$(id -u) GROUP_ID=$(id -g) docker-compose build
```

## Storage Considerations

- **Space Requirements**: High-quality FLAC files can be 30-100 MB per track
- **Format**: Default is FLAC (lossless), configurable to MP3, AAC, OPUS, etc.
- **Compression**: FLAC quality level (0-8) configurable in config.toml

## Backup

This is your music library - back it up regularly:

```bash
# Example: Sync to external drive
rsync -avz downloads/ /mnt/external/music/

# Example: Create archive
tar -czf music-backup-$(date +%Y%m%d).tar.gz downloads/
```

## Cleanup

To remove all downloads:

```bash
# Be careful - this deletes everything!
rm -rf downloads/*
```

To start fresh but keep download history:

```bash
# Downloads will be tracked as already downloaded
# and won't be re-downloaded
rm -rf downloads/*
# download.db in config/ remains intact
```
