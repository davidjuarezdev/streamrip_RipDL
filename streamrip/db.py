"""Wrapper over a database that stores item IDs."""

import logging
from dataclasses import dataclass

from .db_core import DatabaseBase, DatabaseInterface, Dummy
from .db_tables import Downloads, Failed

logger = logging.getLogger("streamrip")


@dataclass(slots=True)
class Database:
    downloads: DatabaseInterface
    failed: DatabaseInterface

    def downloaded(self, item_id: str) -> bool:
        return self.downloads.contains(id=item_id)

    def set_downloaded(self, item_id: str):
        self.downloads.add((item_id,))

    def get_failed_downloads(self) -> list[tuple[str, str, str]]:
        return self.failed.all()

    def set_failed(self, source: str, media_type: str, id: str):
        self.failed.add((source, media_type, id))
