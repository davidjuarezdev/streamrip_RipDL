"""Wrapper over a database that stores item IDs."""

import logging
import os
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Final

logger = logging.getLogger("streamrip")


class DatabaseInterface(ABC):
    @abstractmethod
    def create(self):
        pass

    @abstractmethod
    def contains(self, **items) -> bool:
        pass

    @abstractmethod
    def add(self, kvs):
        pass

    @abstractmethod
    def remove(self, kvs):
        pass

    @abstractmethod
    def all(self) -> list:
        pass


class Dummy(DatabaseInterface):
    """This exists as a mock to use in case databases are disabled."""

    def create(self):
        pass

    def contains(self, **_):
        return False

    def add(self, *_):
        pass

    def remove(self, *_):
        pass

    def all(self):
        return []


class DatabaseBase(DatabaseInterface):
    """A wrapper for an sqlite database."""

    structure: dict
    name: str

    def __init__(self, path: str):
        """Create a Database instance.

        :param path: Path to the database file.
        """
        assert self.structure != {}
        assert self.name
        assert path

        self.path = path

        # sqlite3.connect creates the file if it does not exist, so we check
        # existence beforehand to know if we need to call create() later
        exists = os.path.exists(self.path)

        # ⚡ Bolt: Cache persistent SQLite connection to avoid recreating it
        # on every db check/add. This gives ~10x speedup for database operations
        # like downloading a playlist where it does hundreds of ID checks sequentially.
        self.conn = sqlite3.connect(self.path, check_same_thread=False)

        if not exists or not self._table_exists():
            self.create()

    def __del__(self):
        """Ensure connection is closed on exit."""
        if hasattr(self, "conn") and self.conn:
            self.conn.close()

    def _table_exists(self) -> bool:
        command = f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{self.name}'"
        return bool(self.conn.execute(command).fetchone()[0])

    def create(self):
        """Create a database."""
        params = ", ".join(
            f"{key} {' '.join(map(str.upper, props))} NOT NULL"
            for key, props in self.structure.items()
        )
        command = f"CREATE TABLE IF NOT EXISTS {self.name} ({params})"

        logger.debug("executing %s", command)

        self.conn.execute(command)
        self.conn.commit()

    def keys(self):
        """Get the column names of the table."""
        return self.structure.keys()

    def contains(self, **items) -> bool:
        """Check whether items matches an entry in the table.

        :param items: a dict of column-name + expected value
        :rtype: bool
        """
        allowed_keys = set(self.structure.keys())
        # Sentinel 🛡️: Use ValueError instead of assert to prevent SQL injection
        # because assert statements can be optimized away (e.g. with `python -O`),
        # which would allow arbitrary kwargs to bypass validation and inject SQL.
        if not all(key in allowed_keys for key in items.keys()):
            raise ValueError(f"Invalid key. Valid keys: {allowed_keys}")

        items = {k: str(v) for k, v in items.items()}

        conditions = " AND ".join(f"{key}=?" for key in items.keys())
        command = f"SELECT EXISTS(SELECT 1 FROM {self.name} WHERE {conditions})"

        logger.debug("Executing %s", command)

        return bool(self.conn.execute(command, tuple(items.values())).fetchone()[0])

    def add(self, items: tuple[str]):
        """Add a row to the table.

        :param items: Column-name + value. Values must be provided for all cols.
        :type items: Tuple[str]
        """
        assert len(items) == len(self.structure)

        params = ", ".join(self.structure.keys())
        question_marks = ", ".join("?" for _ in items)
        command = f"INSERT INTO {self.name} ({params}) VALUES ({question_marks})"

        logger.debug("Executing %s", command)
        logger.debug("Items to add: %s", items)

        try:
            self.conn.execute(command, tuple(items))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            # tried to insert an item that was already there
            logger.debug(e)

    def remove(self, **items):
        """Remove items from a table.

        Warning: NOT TESTED!

        :param items:
        """
        allowed_keys = set(self.structure.keys())
        # Sentinel 🛡️: Validate dynamically unpacked keys for SQL parameterization,
        # otherwise untrusted kwargs could execute arbitrary SQL DELETE injections.
        if not all(key in allowed_keys for key in items.keys()):
            raise ValueError(f"Invalid key. Valid keys: {allowed_keys}")

        conditions = " AND ".join(f"{key}=?" for key in items.keys())
        command = f"DELETE FROM {self.name} WHERE {conditions}"

        logger.debug(command)
        self.conn.execute(command, tuple(items.values()))
        self.conn.commit()

    def all(self):
        """Iterate through the rows of the table."""
        return list(self.conn.execute(f"SELECT * FROM {self.name}"))

    def reset(self):
        """Delete the database file."""
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
            self.conn = None
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.create()


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
