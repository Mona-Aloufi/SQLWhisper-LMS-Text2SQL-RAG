import sqlite3
from typing import Dict, Any, Optional
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Lightweight multi-DB connection wrapper.
    Supports: sqlite, postgresql (psycopg2), mysql (pymysql).
    """

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.connection = None
        self.db_type = db_config.get("type", "sqlite")

    def connect(self) -> bool:
        """Establish database connection based on config."""
        try:
            if self.db_type == "sqlite":
                path = self.db_config["path"]
                self.connection = sqlite3.connect(path, check_same_thread=False)
            elif self.db_type == "postgresql":
                import psycopg2
                self.connection = psycopg2.connect(
                    host=self.db_config["host"],
                    port=self.db_config.get("port", 5432),
                    database=self.db_config["database"],
                    user=self.db_config["user"],
                    password=self.db_config["password"],
                )
            elif self.db_type == "mysql":
                import pymysql
                self.connection = pymysql.connect(
                    host=self.db_config["host"],
                    port=self.db_config.get("port", 3306),
                    database=self.db_config["database"],
                    user=self.db_config["user"],
                    password=self.db_config["password"],
                )
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")

            logger.info(f"Connected to {self.db_type} database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to DB: {e}")
            return False

    def disconnect(self) -> None:
        """Close the open connection if any."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    @contextmanager
    def get_cursor(self):
        """
        Yield a cursor. Commits on success, rollbacks on exception.
        """
        if not self.connection:
            if not self.connect():
                raise Exception("Cannot establish DB connection")

        cursor = self.connection.cursor()
        try:
            yield cursor
            try:
                self.connection.commit()
            except Exception:
                pass
        except Exception as e:
            try:
                self.connection.rollback()
            except Exception:
                pass
            raise e
        finally:
            try:
                cursor.close()
            except Exception:
                pass

    # Allow SchemaExtractor and other code to call .cursor()
    def cursor(self):
        if not self.connection:
            if not self.connect():
                raise Exception("Cannot establish DB connection")
        return self.connection.cursor()

    def test_connection(self) -> bool:
        """Simple test query."""
        try:
            with self.get_cursor() as cur:
                cur.execute("SELECT 1")
                _ = cur.fetchone()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        """Execute SELECT-like queries and return rows."""
        try:
            with self.get_cursor() as cur:
                cur.execute(query, params or ())
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute INSERT/UPDATE/DELETE and return rowcount."""
        try:
            with self.get_cursor() as cur:
                cur.execute(query, params or ())
                return getattr(cur, "rowcount", -1)
        except Exception as e:
            logger.error(f"Non-query failed: {e}")
            raise
