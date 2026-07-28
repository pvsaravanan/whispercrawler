import os
import tempfile

from whispercrawler.core.storage import SQLiteStorageSystem


class TestSQLiteStorageSystem:
    """Test SQLiteStorageSystem functionality"""

    def test_sqlite_storage_creation(self):
        """Test SQLite storage system creation"""
        # Use an in-memory database for testing
        storage = SQLiteStorageSystem(storage_file=":memory:")
        assert storage is not None

    def test_sqlite_storage_with_file(self):
        """Test SQLite storage with an actual file"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        storage = None
        try:
            storage = SQLiteStorageSystem(storage_file=db_path)
            assert storage is not None
            assert os.path.exists(db_path)
        finally:
            # Close the database connection before deleting (required on Windows)
            if storage is not None:
                storage.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_sqlite_storage_initialization_args(self):
        """Test SQLite storage with various initialization arguments"""
        # Test with URL parameter
        storage = SQLiteStorageSystem(storage_file=":memory:", url="https://example.com")
        assert storage is not None
        assert storage.url == "https://example.com"

    def test_close_is_idempotent(self):
        """Closing twice must not raise.

        `__del__` calls `close()` unconditionally, so any caller that closes
        explicitly - which the `close()` docstring recommends for Scrapy's
        `spider_closed` - would otherwise get a ProgrammingError raised from the
        destructor when the object is later garbage collected.
        """
        storage = SQLiteStorageSystem(storage_file=":memory:")
        storage.close()
        storage.close()

    def test_del_after_explicit_close_does_not_raise(self):
        """Destruction after an explicit close must be silent."""
        storage = SQLiteStorageSystem(storage_file=":memory:")
        storage.close()
        storage.__del__()
