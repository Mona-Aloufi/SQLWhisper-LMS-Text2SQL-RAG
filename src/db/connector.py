import os
from typing import Dict, Any, Optional
import logging
from .connection import DatabaseConnection
from .schema_extractor import SchemaExtractor

logger = logging.getLogger(__name__)


class ConnectionConfig:
    """Optional small wrapper for a connection config dict"""
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.config)


class DatabaseConnector:
    """
    Manage external and in-memory DatabaseConnection objects.
    Use connect_external() to create and store a connection,
    test_connection() to test credentials without storing.
    """

    def __init__(self):
        self.connections: Dict[str, DatabaseConnection] = {}

    def validate_connection_params(self, connection_params: Dict[str, Any]) -> tuple[bool, str]:
        db_type = connection_params.get("type", "sqlite")
        if db_type not in ("sqlite", "postgresql", "mysql"):
            return False, f"Unsupported type: {db_type}"

        if db_type == "sqlite":
            if "path" not in connection_params:
                return False, "Missing 'path' for sqlite"
            if not os.path.exists(connection_params["path"]):
                return False, "SQLite path does not exist"
            return True, "ok"

        required = ["host", "database", "user", "password"]
        missing = [p for p in required if p not in connection_params]
        if missing:
            return False, f"Missing parameters: {missing}"
        return True, "ok"

    def test_connection(self, connection_params: Dict[str, Any]) -> bool:
        """
        Try to create a DatabaseConnection and run a test query; do not store it.
        Returns True on success.
        """
        try:
            db = DatabaseConnection(connection_params)
            ok = db.test_connection()
            db.disconnect()
            return ok
        except Exception as e:
            logger.error(f"Test connection failed: {e}")
            return False

    def connect_external(self, connection_params: Dict[str, Any]) -> Optional[DatabaseConnection]:
        """
        Create and store a DatabaseConnection object if test succeeds.
        Returns the DatabaseConnection instance or None.
        """
        valid, msg = self.validate_connection_params(connection_params)
        if not valid:
            logger.error(f"Invalid connection params: {msg}")
            return None

        db = DatabaseConnection(connection_params)
        if not db.test_connection():
            logger.error("Failed to connect (test failed)")
            return None

        connection_id = f"{connection_params.get('type')}_{hash(str(connection_params))}"
        self.connections[connection_id] = db
        return db

    def close_connection(self, connection_id: str) -> None:
        if connection_id in self.connections:
            self.connections[connection_id].disconnect()
            del self.connections[connection_id]

    def close_all_connections(self) -> None:
        for cid in list(self.connections.keys()):
            self.close_connection(cid)

    def get_schema(self, db_connection: DatabaseConnection) -> Dict[str, Any]:
        try:
            extractor = SchemaExtractor(db_connection)
            return extractor.extract_schema()
        except Exception as e:
            logger.error(f"Get schema failed: {e}")
            return {}
