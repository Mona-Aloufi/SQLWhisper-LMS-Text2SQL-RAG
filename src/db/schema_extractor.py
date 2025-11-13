from typing import Dict, List, Any
import logging
from .connection import DatabaseConnection

logger = logging.getLogger(__name__)


class SchemaExtractor:
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
        self.db_type = db_connection.db_type

    def extract_schema(self) -> Dict[str, Any]:
        schema: Dict[str, Any] = {}
        try:
            tables = self.get_table_names()
            for t in tables:
                schema[t] = {
                    "columns": self.get_table_columns(t),
                    "primary_keys": self.get_primary_keys(t),
                    "foreign_keys": self.get_foreign_keys(t),
                    "indexes": self.get_indexes(t),
                }
            logger.info(f"Extracted schema for {len(schema)} tables")
            return schema
        except Exception as e:
            logger.error(f"Schema extraction failed: {e}")
            return {}

    def get_table_names(self) -> List[str]:
        if self.db_type == "sqlite":
            q = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            with self.db_connection.get_cursor() as cur:
                cur.execute(q)
                return [r[0] for r in cur.fetchall()]

        elif self.db_type == "postgresql":
            q = "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
            with self.db_connection.get_cursor() as cur:
                cur.execute(q)
                return [r[0] for r in cur.fetchall()]

        elif self.db_type == "mysql":
            dbname = self.db_connection.db_config.get("database")
            q = "SELECT table_name FROM information_schema.tables WHERE table_schema=%s;"
            with self.db_connection.get_cursor() as cur:
                cur.execute(q, (dbname,))
                return [r[0] for r in cur.fetchall()]

        else:
            raise ValueError(f"Unsupported DB type: {self.db_type}")

    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        cols: List[Dict[str, Any]] = []
        if self.db_type == "sqlite":
            q = f"PRAGMA table_info('{table_name}');"
            with self.db_connection.get_cursor() as cur:
                cur.execute(q)
                for r in cur.fetchall():
                    cols.append({
                        "name": r[1],
                        "type": r[2],
                        "nullable": not bool(r[3]),
                        "default": r[4],
                        "primary_key": bool(r[5]),
                    })

        elif self.db_type == "postgresql":
            q = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name=%s
                ORDER BY ordinal_position;
            """
            with self.db_connection.get_cursor() as cur:
                cur.execute(q, (table_name,))
                for r in cur.fetchall():
                    cols.append({
                        "name": r[0],
                        "type": r[1],
                        "nullable": (r[2] == "YES"),
                        "default": r[3],
                    })

        elif self.db_type == "mysql":
            dbname = self.db_connection.db_config.get("database")
            q = """
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM information_schema.COLUMNS
                WHERE TABLE_NAME=%s AND TABLE_SCHEMA=%s
                ORDER BY ORDINAL_POSITION;
            """
            with self.db_connection.get_cursor() as cur:
                cur.execute(q, (table_name, dbname))
                for r in cur.fetchall():
                    cols.append({
                        "name": r[0],
                        "type": r[1],
                        "nullable": (r[2] == "YES"),
                        "default": r[3],
                    })
        return cols

    def get_primary_keys(self, table_name: str) -> List[str]:
        if self.db_type == "sqlite":
            return [c["name"] for c in self.get_table_columns(table_name) if c.get("primary_key")]

        elif self.db_type == "postgresql":
            q = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY';
            """
            with self.db_connection.get_cursor() as cur:
                cur.execute(q, (table_name,))
                return [r[0] for r in cur.fetchall()]

        elif self.db_type == "mysql":
            dbname = self.db_connection.db_config.get("database")
            q = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name=%s AND tc.table_schema=%s AND tc.constraint_type='PRIMARY KEY';
            """
            with self.db_connection.get_cursor() as cur:
                cur.execute(q, (table_name, dbname))
                return [r[0] for r in cur.fetchall()]

        return []

    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        fks: List[Dict[str, Any]] = []
        if self.db_type == "sqlite":
            q = f"PRAGMA foreign_key_list('{table_name}');"
            with self.db_connection.get_cursor() as cur:
                cur.execute(q)
                for r in cur.fetchall():
                    fks.append({
                        "from_column": r[3],
                        "to_table": r[2],
                        "to_column": r[4],
                        "on_update": r[5],
                        "on_delete": r[6],
                    })

        elif self.db_type == "postgresql":
            q = """
            SELECT kcu.column_name, ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_name=%s;
            """
            with self.db_connection.get_cursor() as cur:
                cur.execute(q, (table_name,))
                for r in cur.fetchall():
                    fks.append({
                        "from_column": r[0],
                        "to_table": r[1],
                        "to_column": r[2],
                    })

        elif self.db_type == "mysql":
            dbname = self.db_connection.db_config.get("database")
            q = """
            SELECT kcu.column_name, referenced_table_name, referenced_column_name
            FROM information_schema.key_column_usage
            WHERE table_name=%s AND table_schema=%s AND referenced_table_name IS NOT NULL;
            """
            with self.db_connection.get_cursor() as cur:
                cur.execute(q, (table_name, dbname))
                for r in cur.fetchall():
                    fks.append({
                        "from_column": r[0],
                        "to_table": r[1],
                        "to_column": r[2],
                    })
        return fks

    def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        idxs: List[Dict[str, Any]] = []
        if self.db_type == "sqlite":
            q = f"PRAGMA index_list('{table_name}');"
            with self.db_connection.get_cursor() as cur:
                cur.execute(q)
                for r in cur.fetchall():
                    idxs.append({
                        "name": r[1],
                        "unique": bool(r[2]),
                        "origin": r[3],
                    })

        elif self.db_type == "postgresql":
            q = "SELECT indexname, indexdef FROM pg_indexes WHERE tablename=%s;"
            with self.db_connection.get_cursor() as cur:
                cur.execute(q, (table_name,))
                for r in cur.fetchall():
                    idxs.append({"name": r[0], "definition": r[1]})

        elif self.db_type == "mysql":
            dbname = self.db_connection.db_config.get("database")
            q = """
            SELECT INDEX_NAME, NON_UNIQUE, COLUMN_NAME
            FROM information_schema.statistics
            WHERE TABLE_NAME=%s AND TABLE_SCHEMA=%s;
            """
            with self.db_connection.get_cursor() as cur:
                cur.execute(q, (table_name, dbname))
                for r in cur.fetchall():
                    idxs.append({
                        "name": r[0],
                        "unique": (r[1] == 0),
                        "column": r[2],
                    })
        return idxs
