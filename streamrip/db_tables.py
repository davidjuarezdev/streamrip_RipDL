from typing import Final

from .db_core import DatabaseBase


class Downloads(DatabaseBase):
    """A table that stores the downloaded IDs."""

    name = "downloads"
    structure: Final[dict] = {
        "id": ["text", "unique"],
    }


class Failed(DatabaseBase):
    """A table that stores information about failed downloads."""

    name = "failed_downloads"
    structure: Final[dict] = {
        "source": ["text"],
        "media_type": ["text"],
        "id": ["text", "unique"],
    }
