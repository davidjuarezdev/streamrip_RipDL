# Configuration Directory

This directory is used by the streamrip Docker container to store configuration files and databases.

## Contents

After running streamrip for the first time, this directory will contain:

- **config.toml** - Main configuration file with service credentials and download settings
- **downloads.db** - SQLite database tracking successfully downloaded items
- **failed_downloads.db** - SQLite database tracking failed downloads for retry

## Setup

### First-Time Configuration

Run the setup command to generate the default configuration:

```bash
docker-compose run --rm streamrip config --setup
```

### Adding Service Credentials

Edit the `config.toml` file and add credentials for the services you want to use:

#### Qobuz
```toml
[qobuz]
email = "your-email@example.com"
password = "your-password"
# Or use auth_token instead
```

#### Tidal
```bash
# Use interactive login (recommended)
docker-compose run --rm streamrip login tidal
```

#### Deezer
```toml
[deezer]
arl = "your-arl-cookie"
```

#### SoundCloud
```toml
[soundcloud]
client_id = "your-client-id"
app_version = "version-number"
```

## Security

**IMPORTANT**: This directory contains sensitive credentials.

- Keep it private and secure
- Do not commit it to version control
- Ensure proper file permissions: `chmod 600 config.toml`

## Persistence

This directory is mounted as a volume in the Docker container, ensuring:
- Configuration persists between container restarts
- Download history is maintained
- Service authentication tokens are preserved

## Backup

Consider backing up this directory regularly to preserve:
- Your service credentials
- Download history database
- Custom configuration settings

```bash
# Example backup
tar -czf streamrip-config-backup-$(date +%Y%m%d).tar.gz config/
```

## Troubleshooting

If you encounter issues:

1. **Reset configuration**: Delete `config.toml` and run setup again
2. **Clear download history**: Delete `downloads.db` and `failed_downloads.db`
3. **Re-authenticate**: Run `docker-compose run --rm streamrip login [service]`
