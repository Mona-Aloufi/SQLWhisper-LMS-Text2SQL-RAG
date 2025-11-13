import os
import sqlite3
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def get_db_type(connection_string: str) -> str:
    if connection_string.startswith(("postgresql://", "postgres://")):
        return "postgresql"
    if connection_string.startswith("mysql://"):
        return "mysql"
    if connection_string.startswith("sqlite://") or connection_string.endswith((".db", ".sqlite", ".sqlite3")):
        return "sqlite"
    if os.path.exists(connection_string) and connection_string.endswith((".db", ".sqlite", ".sqlite3")):
        return "sqlite"
    return "unknown"


def validate_sqlite_file(file_path: str) -> bool:
    try:
        if not os.path.exists(file_path):
            return False
        conn = sqlite3.connect(file_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;")
        conn.close()
        return True
    except Exception as e:
        logger.debug(f"SQLite validation failed: {e}")
        return False


def sanitize_table_name(table_name: str) -> str:
    return "".join(c for c in table_name if c.isalnum() or c in ("_", "-"))


def get_supported_db_types() -> List[str]:
    return ["sqlite", "postgresql", "mysql"]


def format_schema_for_model(schema_info: Dict[str, Any]) -> str:
    lines: List[str] = []
    for table, info in schema_info.items():
        lines.append(f"Table: {table}")
        lines.append("Columns:")
        for col in info.get("columns", []):
            lines.append(f"  - {col['name']} ({col.get('type')}) - Nullable: {col.get('nullable', True)}")
        if info.get("primary_keys"):
            lines.append("Primary Keys: " + ", ".join(info["primary_keys"]))
        if info.get("foreign_keys"):
            lines.append("Foreign Keys:")
            for fk in info["foreign_keys"]:
                lines.append(f"  - {fk}")
        if info.get("indexes"):
            lines.append("Indexes:")
            for idx in info["indexes"]:
                lines.append(f"  - {idx}")
        lines.append("") 
    return "\n".join(lines)
