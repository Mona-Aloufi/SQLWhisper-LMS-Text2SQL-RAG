import os
import shutil
from typing import Any, Dict, Optional
import logging
from .connection import DatabaseConnection
from .utils import validate_sqlite_file

logger = logging.getLogger(__name__)


class DatabaseUploader:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.allowed_extensions = {".db", ".sqlite", ".sqlite3"}
        self.max_file_size = 100 * 1024 * 1024  # 100 MB
        os.makedirs(self.data_dir, exist_ok=True)

    def save_uploaded_file(self, file_object: Any, filename: str) -> str:
        """
        Save uploaded file-like object or bytes to data directory.
        - file_object: has .read() (stream), or bytes, or a local path (str).
        Returns saved path.
        """
        file_path = os.path.join(self.data_dir, filename)

        # file-like object
        if hasattr(file_object, "read"):
            with open(file_path, "wb") as f:
                f.write(file_object.read())
        # raw bytes
        elif isinstance(file_object, (bytes, bytearray)):
            with open(file_path, "wb") as f:
                f.write(file_object)
        # a file path string
        elif isinstance(file_object, str) and os.path.exists(file_object):
            shutil.copy2(file_object, file_path)
        else:
            # If nothing matched, raise
            raise ValueError("Unsupported file_object passed to save_uploaded_file")

        return file_path

    def handle_upload(self, file_object: Any, filename: str) -> Optional[Dict[str, str]]:
        """
        Save and validate a SQLite DB upload. Returns connection config (dict) on success.
        """
        try:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in self.allowed_extensions:
                raise ValueError(f"Unsupported file extension: {ext}")

            saved_path = self.save_uploaded_file(file_object, filename)

            # size check
            if os.path.getsize(saved_path) > self.max_file_size:
                os.remove(saved_path)
                raise ValueError("Uploaded file too large")

            if not validate_sqlite_file(saved_path):
                os.remove(saved_path)
                raise ValueError("Uploaded file is not a valid SQLite database")

            return {"type": "sqlite", "path": saved_path}
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None

    def create_connection_from_upload(self, file_path: str) -> Optional[DatabaseConnection]:
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError("File not found")
            return DatabaseConnection({"type": "sqlite", "path": file_path})
        except Exception as e:
            logger.error(f"Create connection from upload failed: {e}")
            return None

    def list_uploaded_databases(self) -> list:
        results = []
        for fn in os.listdir(self.data_dir):
            if os.path.splitext(fn)[1].lower() in self.allowed_extensions:
                path = os.path.join(self.data_dir, fn)
                if validate_sqlite_file(path):
                    results.append({"name": fn, "path": path, "size": os.path.getsize(path)})
        return results

    def delete_database(self, filename: str) -> bool:
        path = os.path.join(self.data_dir, filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
