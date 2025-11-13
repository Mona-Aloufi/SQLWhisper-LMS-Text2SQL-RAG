# src/app/main.py
from fastapi import FastAPI, UploadFile, Body
from src.db.connection import DatabaseConnection
from src.db.schema_extractor import SchemaExtractor
from src.services.text2sql_service import EnhancedText2SQLService
import logging
import tempfile
import shutil
import os

app = FastAPI(title="SQLWhisper - Text2SQL API")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Initialize core components ---
db_connection: DatabaseConnection = None
schema_extractor: SchemaExtractor = SchemaExtractor(db_connection=None)
text2sql_service = EnhancedText2SQLService()


@app.post("/upload-db")
async def upload_sqlite(file: UploadFile):
    try:
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        global db_connection
        db_connection = DatabaseConnection({"type": "sqlite", "path": file_path})
        if not db_connection.connect():
            raise ValueError("Failed to connect to SQLite database.")

        schema_extractor.set_connection(db_connection)
        schema = schema_extractor.extract_schema()
        return {"message": "Database uploaded and connected successfully.", "schema": schema}

    except Exception as e:
        logger.error(f"Error uploading DB: {e}")
        return {"error": str(e)}



@app.post("/connect-db")
async def connect_external_db(payload: dict = Body(...)):
    try:
        db_type = payload.get("db_type")
        host = payload.get("host")
        database = payload.get("database")
        user = payload.get("user")
        password = payload.get("password")
        port = payload.get("port", 5432)

        config = {
            "type": db_type,
            "host": host,
            "database": database,
            "user": user,
            "password": password,
            "port": port
        }

        global db_connection
        db_connection = DatabaseConnection(config)
        if not db_connection.connect():
            raise ValueError(f"Failed to connect to {db_type} database.")

        schema_extractor.set_connection(db_connection)
        schema = schema_extractor.extract_schema()
        return {"message": f"Connected to {db_type} successfully", "schema": schema}

    except Exception as e:
        logger.error(f"Connection error: {e}")
        return {"error": str(e)}



@app.post("/generate-sql")
async def generate_sql(payload: dict = Body(...)):
    try:
        question = payload.get("question")
        if not question:
            return {"error": "Missing 'question' in request payload."}

        if not db_connection:
            raise ValueError("No database connection. Please upload or connect first.")

        # Use underlying connection for Text2SQL service
        result = text2sql_service.generate_sql(question, db_connection.connection)
        return result

    except Exception as e:
        logger.error(f"SQL generation failed: {e}")
        return {"error": str(e)}



@app.post("/execute-sql")
async def execute_sql(payload: dict = Body(...)):
    try:
        sql = payload.get("sql")
        if not sql:
            return {"error": "Missing 'sql' in request payload."}

        if not db_connection:
            raise ValueError("No active database connection.")

        result = text2sql_service.execute_sql(db_connection.connection, sql)
        return result

    except Exception as e:
        logger.error(f"Query execution error: {e}")
        return {"error": str(e)}
