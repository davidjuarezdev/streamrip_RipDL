from ..client import Client, DeezerClient, QobuzClient, SoundcloudClient, TidalClient
from ..config import Config
from .prompter import get_prompter
from ..console import console
import logging

logger = logging.getLogger("streamrip")

class ClientManager:
    """Manages client initialization and login."""

    def __init__(self, config: Config):
        self.config = config
        self.clients: dict[str, Client] = {
            "qobuz": QobuzClient(config),
            "tidal": TidalClient(config),
            "deezer": DeezerClient(config),
            "soundcloud": SoundcloudClient(config),
        }

    async def get_logged_in_client(self, source: str) -> Client:
        """Return a functioning client instance for `source`."""
        client = self.clients.get(source)
        if client is None:
            raise Exception(
                f"No client named {source} available. Only have {list(self.clients.keys())}",
            )
        if not client.logged_in:
            prompter = get_prompter(client, self.config)
            if not prompter.has_creds():
                # Get credentials from user and log into client
                await prompter.prompt_and_login()
                prompter.save()
            else:
                with console.status(f"[cyan]Logging into {source}", spinner="dots"):
                    # Log into client using credentials from config
                    await client.login()

        assert client.logged_in
        return client

    async def close_all(self):
        """Ensure all client sessions are closed."""
        for client in self.clients.values():
            if hasattr(client, "session") and client.session:
                await client.session.close()
