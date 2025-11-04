# Standard library imports
import os
import re
import logging
import sqlite3
from typing import Dict, List, Tuple, Optional, Any, Union

# Third-party imports
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EnhancedText2SQLService:
    def __init__(self, model_name=None, device=None):
        """
        Enhanced Text2SQL service with Hugging Face token support
        
        Using yasserrmd/Text2SQL-1.5B model (Causal LM)
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        # This will use the model name from your .env file, or default to yasserrmd/Text2SQL-1.5B
        self.model_name = model_name or os.getenv("MODEL_NAME", "yasserrmd/Text2SQL-1.5B")
        self.hf_token = os.getenv("HF_TOKEN")
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initializing Text2SQL service with model: {self.model_name}")
        
        try:
            # Initialize tokenizer and model with HF token
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                token=self.hf_token,
                trust_remote_code=True
            )
            
            # Use AutoModelForCausalLM for decoder-only models
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                token=self.hf_token,
                trust_remote_code=True,
                dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            ).to(self.device)
            
            self.logger.info("✅ Model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            # Fallback to a smaller model if the preferred one fails
            self._load_fallback_model()
    
    def _load_fallback_model(self):
        """Load a fallback model if the primary one fails"""
        try:
            self.logger.info("Trying fallback model: google/flan-t5-base")
            self.model_name = "google/flan-t5-base"
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            # For fallback, use Seq2Seq model
            from transformers import AutoModelForSeq2SeqLM
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self.device)
            self.logger.info("Fallback model loaded successfully")
        except Exception as e:
            self.logger.error(f"Fallback model also failed: {e}")
            raise e
        
    def get_database_schema(self, db_connection) -> Dict:
        """Extract complete schema information"""
        schema_info = {}
        cursor = db_connection.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            # Get columns for each table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            schema_info[table_name] = [
                {
                    "name": col[1], 
                    "type": col[2], 
                    "nullable": not col[3],
                    "primary_key": col[5] == 1
                }
                for col in columns
            ]
        
        return schema_info
    
    def create_schema_context(self, schema_info: Dict, user_query: str) -> str:
        """Create intelligent schema context based on query"""
        # Simple keyword matching to identify relevant tables
        relevant_tables = []
        query_lower = user_query.lower()
        
        for table_name, columns in schema_info.items():
            # Check if table name or column names appear in query
            table_in_query = table_name.lower() in query_lower
            columns_in_query = any(
                col['name'].lower() in query_lower for col in columns
            )
            
            if table_in_query or columns_in_query:
                relevant_tables.append(table_name)
        
        # If no tables found, use all tables
        if not relevant_tables:
            relevant_tables = list(schema_info.keys())
        
        # Build schema context
        schema_context = "Database Schema:\n"
        for table in relevant_tables[:3]:  # Limit to 3 most relevant tables
            schema_context += f"Table: {table}\n"
            for col in schema_info[table]:
                schema_context += f"  - {col['name']} ({col['type']})\n"
            schema_context += "\n"
        
        return schema_context
    
    def create_enhanced_prompt(self, question: str, schema_context: str) -> str:
        """Create a more structured prompt for causal LM models"""
        prompt = f"""### Task: Convert the following natural language question into a SQLite SQL query.

### Database Schema:
{schema_context}

### Instructions:
- Use only tables and columns mentioned in the schema
- Use proper SQLite syntax
- Use JOINs when needed
- Use WHERE for filtering
- Use GROUP BY and aggregates when needed
- Return only the SQL query without any explanations

### Question: {question}

### SQL Query:
```sql
"""
        return prompt
    
    def clean_sql_output(self, sql: str) -> str:
        """Clean and validate SQL output"""
        # Remove any code block markers
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*', '', sql)
        
        # Extract only the SQL query (stop at the next ``` or end of string)
        sql_match = re.search(r'(SELECT|INSERT|UPDATE|DELETE|WITH).*?(?=```|$)', sql, re.IGNORECASE | re.DOTALL)
        if sql_match:
            sql = sql_match.group(0).strip()
        
        # Remove any trailing incomplete SQL
        sql = re.sub(r'[\s\n]*$', '', sql)
        
        if not sql.endswith(';'):
            sql += ';'
            
        return sql
    
    def validate_sql_syntax(self, sql: str, db_connection) -> bool:
        """Basic SQL syntax validation"""
        try:
            cursor = db_connection.cursor()
            cursor.execute(f"EXPLAIN {sql}")
            return True
        except Exception as e:
            self.logger.warning(f"SQL syntax validation failed: {e}")
            return False
    
    def generate_sql(self, question: str, db_connection, max_retries: int = 2) -> Dict:
        """
        Enhanced SQL generation with schema awareness and validation
        Returns: {"sql": str, "confidence": str, "explanation": str, "valid": bool}
        """
        try:
            schema_info = self.get_database_schema(db_connection)
            schema_context = self.create_schema_context(schema_info, question)
            
            prompt = self.create_enhanced_prompt(question, schema_context)
            
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt", 
                max_length=1024, 
                truncation=True
            ).to(self.device)
            
            # Generate with causal LM
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=256,
                num_return_sequences=1,
                temperature=0.1, 
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                early_stopping=True
            )
            
            raw_sql = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Remove the prompt from the output
            raw_sql = raw_sql.replace(prompt, "").strip()
            cleaned_sql = self.clean_sql_output(raw_sql)
            
            # Validate SQL
            is_valid = self.validate_sql_syntax(cleaned_sql, db_connection)
            
            return {
                "sql": cleaned_sql,
                "valid": is_valid,
                "raw_output": raw_sql,
                "schema_used": schema_context
            }
            
        except Exception as e:
            self.logger.error(f"Error generating SQL: {e}")
            return {
                "sql": "SELECT 1;",  # Fallback
                "valid": False,
                "error": str(e),
                "raw_output": ""
            }