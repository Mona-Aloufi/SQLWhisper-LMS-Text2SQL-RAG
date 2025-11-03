# app.py - Updated with enhanced service and testing endpoints
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import logging
from src.services.text2sql_service import EnhancedText2SQLService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SQLWhisper API", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the enhanced service
t2s_service = EnhancedText2SQLService()

# Request/Response models
class Question(BaseModel):
    question: str
    database_path: str = "data/my_database.sqlite"

class Text2SQLResponse(BaseModel):
    question: str
    sql: str
    valid: bool
    execution_result: Optional[List[Dict]] = None
    error: Optional[str] = None
    raw_output: Optional[str] = None

class TestQuery(BaseModel):
    question: str
    expected_sql: Optional[str] = None

class BatchTestResponse(BaseModel):
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]

# Database connection dependency
def get_db_connection(database_path: str = "data/my_database.sqlite"):
    """Get SQLite database connection"""
    try:
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/")
def root():
    return {
        "message": "SQLWhisper API is running!",
        "version": "2.0.0",
        "endpoints": {
            "text2sql": "POST /text2sql - Generate SQL from natural language",
            "test_query": "POST /test-query - Test a query with execution",
            "batch_test": "POST /batch-test - Test multiple queries",
            "db_info": "GET /db-info - Get database schema info",
            "health": "GET /health - API health check"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "text2sql"}

@app.get("/db-info")
def get_database_info(database_path: str = "data/my_database.sqlite"):
    """Get complete database schema information"""
    try:
        conn = get_db_connection(database_path)
        
        # Get all tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        schema_info = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            schema_info[table] = [
                {
                    "name": col[1],
                    "type": col[2], 
                    "nullable": not col[3],
                    "primary_key": col[5] == 1
                }
                for col in columns
            ]
        
        conn.close()
        
        return {
            "database_path": database_path,
            "tables": tables,
            "schema": schema_info,
            "total_tables": len(tables)
        }
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/text2sql", response_model=Text2SQLResponse)
def text2sql(payload: Question):
    """
    Generate SQL from natural language question
    """
    question = payload.question.strip()
    database_path = payload.database_path
    
    if not question:
        raise HTTPException(status_code=400, detail="Empty question provided")
    
    try:
        # Get database connection
        conn = get_db_connection(database_path)
        
        # Generate SQL using enhanced service
        result = t2s_service.generate_sql(question, conn)
        
        # Close connection
        conn.close()
        
        return Text2SQLResponse(
            question=question,
            sql=result["sql"],
            valid=result["valid"],
            raw_output=result.get("raw_output", "")
        )
        
    except Exception as e:
        logger.error(f"Error in text2sql: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test-query", response_model=Text2SQLResponse)
def test_query(payload: Question):
    """
    Generate SQL and execute it to test the results
    """
    question = payload.question.strip()
    database_path = payload.database_path
    
    if not question:
        raise HTTPException(status_code=400, detail="Empty question provided")
    
    try:
        # Get database connection
        conn = get_db_connection(database_path)
        
        # Generate SQL
        result = t2s_service.generate_sql(question, conn)
        
        # Execute SQL if valid
        execution_result = None
        error = None
        
        if result["valid"]:
            try:
                cursor = conn.cursor()
                cursor.execute(result["sql"])
                rows = cursor.fetchall()
                execution_result = [dict(row) for row in rows]
            except Exception as e:
                error = f"Execution failed: {str(e)}"
        
        conn.close()
        
        return Text2SQLResponse(
            question=question,
            sql=result["sql"],
            valid=result["valid"],
            execution_result=execution_result,
            error=error,
            raw_output=result.get("raw_output", "")
        )
        
    except Exception as e:
        logger.error(f"Error in test_query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch-test")
def batch_test(queries: List[TestQuery], database_path: str = "data/my_database.sqlite"):
    """
    Test multiple queries at once
    """
    if not queries:
        raise HTTPException(status_code=400, detail="No queries provided")
    
    try:
        conn = get_db_connection(database_path)
        results = []
        
        for i, query in enumerate(queries):
            try:
                result = t2s_service.generate_sql(query.question, conn)
                
                # Execute to verify
                execution_success = False
                row_count = 0
                
                if result["valid"]:
                    try:
                        cursor = conn.cursor()
                        cursor.execute(result["sql"])
                        rows = cursor.fetchall()
                        execution_success = True
                        row_count = len(rows)
                    except:
                        execution_success = False
                
                results.append({
                    "index": i + 1,
                    "question": query.question,
                    "generated_sql": result["sql"],
                    "valid_syntax": result["valid"],
                    "execution_success": execution_success,
                    "rows_returned": row_count,
                    "raw_output": result.get("raw_output", ""),
                    "expected_sql": query.expected_sql
                })
                
            except Exception as e:
                results.append({
                    "index": i + 1,
                    "question": query.question,
                    "error": str(e),
                    "valid_syntax": False,
                    "execution_success": False,
                    "rows_returned": 0
                })
        
        conn.close()
        
        # Calculate summary
        valid_queries = sum(1 for r in results if r["valid_syntax"])
        executed_queries = sum(1 for r in results if r["execution_success"])
        
        summary = {
            "total_queries": len(queries),
            "valid_syntax": valid_queries,
            "execution_success": executed_queries,
            "success_rate": f"{(valid_queries/len(queries))*100:.1f}%"
        }
        
        return BatchTestResponse(results=results, summary=summary)
        
    except Exception as e:
        logger.error(f"Error in batch_test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sample-queries")
def get_sample_queries():
    """
    Get sample queries for testing
    """
    sample_queries = [
        "Show all tables in the database",
        "Count the total number of records",
        "List the first 5 rows from all tables",
        "What is the database schema?",
        "Show me all column names",
        "How many tables are there?",
        "Display sample data from each table"
    ]
    
    return {
        "sample_queries": sample_queries,
        "count": len(sample_queries)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)