import logging

class SchemaExtractor:
    def __init__(self, db_connection=None):
        self.logger = logging.getLogger(__name__)
        self.db_connection = db_connection
        self.db_type = getattr(db_connection, "db_type", None)
    
    def set_connection(self, db_connection):
        """Assign or update the database connection after initialization."""
        self.db_connection = db_connection
        self.db_type = getattr(db_connection, "db_type", None)
        self.logger.info(f"SchemaExtractor connection set for: {self.db_type}")
    
    def extract_schema(self):
        """Extract schema information from the current database connection."""
        if not self.db_connection:
            raise ValueError("❌ Database connection not set in SchemaExtractor.")
        
        cursor = self.db_connection.cursor()
        schema_info = {}

        try:
            # Handle SQLite
            if self.db_type == "sqlite":
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                for (table_name,) in tables:
                    cursor.execute(f"PRAGMA table_info('{table_name}')")
                    columns = cursor.fetchall()
                    schema_info[table_name] = [col[1] for col in columns]

            # Handle PostgreSQL
            elif self.db_type == "postgresql":
                cursor.execute("""
                    SELECT table_name, column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public';
                """)
                rows = cursor.fetchall()
                for table, column in rows:
                    schema_info.setdefault(table, []).append(column)

            # Handle MySQL
            elif self.db_type == "mysql":
                cursor.execute("SHOW TABLES;")
                tables = [row[0] for row in cursor.fetchall()]
                for table_name in tables:
                    cursor.execute(f"DESCRIBE `{table_name}`;")
                    columns = [row[0] for row in cursor.fetchall()]
                    schema_info[table_name] = columns

            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")

            return schema_info

        except Exception as e:
            self.logger.error(f"Error extracting schema: {e}")
            raise e
