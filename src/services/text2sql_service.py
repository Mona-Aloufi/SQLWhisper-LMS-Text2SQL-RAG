# ============================================================
# Text-to-SQL Service — Enhanced with Token-Level Confidence
# ============================================================
import os
import re
import logging
import sqlite3
from typing import Dict, List, Optional, Any
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EnhancedText2SQLService:
    def __init__(self, model_name=None, device=None):
<<<<<<< HEAD
        """
        Enhanced Text2SQL service with Hugging Face token support

        Using yasserrmd/Text2SQL-1.5B model (Causal LM)
        """
=======
>>>>>>> 2eed77e66f92ec4f5c66d23bc14fa3709c254859
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name or os.getenv("MODEL_NAME", "yasserrmd/Text2SQL-1.5B")
        self.hf_token = os.getenv("HF_TOKEN")

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initializing Text2SQL service with model: {self.model_name}")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                token=self.hf_token,
                trust_remote_code=True
            )
<<<<<<< HEAD

            # Use AutoModelForCausalLM for decoder-only models
=======
>>>>>>> 2eed77e66f92ec4f5c66d23bc14fa3709c254859
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                token=self.hf_token,
                trust_remote_code=True,
                dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            ).to(self.device)

            self.logger.info("✅ Model loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            self._load_fallback_model()

<<<<<<< HEAD
=======
    # ============================================================
    # Token-Level Confidence — Logit-Based Certainty
    # ============================================================
    def _token_confidence(self, inputs):
        """Compute average token-level confidence from softmax probabilities."""
        try:
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    num_return_sequences=1,
                    temperature=0.1,
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    early_stopping=True,
                    output_scores=True,
                    return_dict_in_generate=True,
                )

            confidences = [
                F.softmax(score, dim=-1).max().item()
                for score in outputs.scores
            ]
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            self.logger.info(f"Token confidence: {round(avg_conf * 100, 2)}%")
            return round(avg_conf, 3)

        except Exception as e:
            self.logger.warning(f"Token-level confidence computation failed: {e}")
            return None

    def interpret_confidence(self, score: float) -> str:
        if score is None:
            return "Unknown"
        if score >= 0.85:
            return "High"
        elif score >= 0.65:
            return "Medium"
        else:
            return "Low"

    # ============================================================
    # Fallback Model
    # ============================================================
>>>>>>> 2eed77e66f92ec4f5c66d23bc14fa3709c254859
    def _load_fallback_model(self):
        try:
            self.logger.info("Trying fallback model: google/flan-t5-base")
            self.model_name = "google/flan-t5-base"
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            from transformers import AutoModelForSeq2SeqLM
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self.device)
            self.logger.info("Fallback model loaded successfully")
        except Exception as e:
            self.logger.error(f"Fallback model also failed: {e}")
            raise e

<<<<<<< HEAD
=======
    # ============================================================
    # Schema & Prompt Utilities
    # ============================================================
>>>>>>> 2eed77e66f92ec4f5c66d23bc14fa3709c254859
    def get_database_schema(self, db_connection) -> Dict:
        schema_info = {}
        cursor = db_connection.cursor()
<<<<<<< HEAD

=======
>>>>>>> 2eed77e66f92ec4f5c66d23bc14fa3709c254859
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
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
<<<<<<< HEAD

        return schema_info

    def create_schema_context(self, schema_info: Dict, user_query: str) -> str:
        """Create intelligent schema context based on query"""
        relevant_tables = []
        query_lower = user_query.lower()

        for table_name, columns in schema_info.items():
            table_in_query = table_name.lower() in query_lower
            columns_in_query = any(
                col['name'].lower() in query_lower for col in columns
            )
            if table_in_query or columns_in_query:
                relevant_tables.append(table_name)

=======
        return schema_info

    def create_schema_context(self, schema_info: Dict, user_query: str) -> str:
        relevant_tables = []
        query_lower = user_query.lower()
        for table_name, columns in schema_info.items():
            if table_name.lower() in query_lower or any(col['name'].lower() in query_lower for col in columns):
                relevant_tables.append(table_name)
>>>>>>> 2eed77e66f92ec4f5c66d23bc14fa3709c254859
        if not relevant_tables:
            relevant_tables = list(schema_info.keys())

        schema_context = "Database Schema:\n"
        for table in relevant_tables[:3]:
            schema_context += f"Table: {table}\n"
            for col in schema_info[table]:
                schema_context += f"  - {col['name']} ({col['type']})\n"
            schema_context += "\n"
<<<<<<< HEAD

=======
>>>>>>> 2eed77e66f92ec4f5c66d23bc14fa3709c254859
        return schema_context

    def create_enhanced_prompt(self, question: str, schema_context: str) -> str:
        return f"""### Task: Convert the following natural language question into a SQLite SQL query.

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
<<<<<<< HEAD
        return prompt

    def clean_sql_output(self, sql: str) -> str:
        """Clean and validate SQL output"""
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*', '', sql)

        sql_match = re.search(r'(SELECT|INSERT|UPDATE|DELETE|WITH).*?(?=```|$)', sql, re.IGNORECASE | re.DOTALL)
        if sql_match:
            sql = sql_match.group(0).strip()

        sql = re.sub(r'[\s\n]*$', '', sql)
        if not sql.endswith(';'):
            sql += ';'

=======

    # ============================================================
    # SQL Cleaning, Validation, and Generation
    # ============================================================
    def clean_sql_output(self, sql: str) -> str:
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*', '', sql)
        sql_match = re.search(r'(SELECT|INSERT|UPDATE|DELETE|WITH).*?(?=```|$)', sql, re.IGNORECASE | re.DOTALL)
        if sql_match:
            sql = sql_match.group(0).strip()
        sql = re.sub(r'[\s\n]*$', '', sql)
        if not sql.endswith(';'):
            sql += ';'
>>>>>>> 2eed77e66f92ec4f5c66d23bc14fa3709c254859
        return sql

    def validate_sql_syntax(self, sql: str, db_connection) -> bool:
        try:
            cursor = db_connection.cursor()
            cursor.execute(f"EXPLAIN {sql}")
            return True
        except Exception as e:
            self.logger.warning(f"SQL syntax validation failed: {e}")
            return False

    def generate_sql(self, question: str, db_connection, max_retries: int = 2) -> Dict:
        try:
            schema_info = self.get_database_schema(db_connection)
            schema_context = self.create_schema_context(schema_info, question)
<<<<<<< HEAD

            prompt = self.create_enhanced_prompt(question, schema_context)

            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                max_length=1024,
                truncation=True
            ).to(self.device)

=======
            prompt = self.create_enhanced_prompt(question, schema_context)

            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=1024, truncation=True).to(self.device)
>>>>>>> 2eed77e66f92ec4f5c66d23bc14fa3709c254859
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=256,
                num_return_sequences=1,
                temperature=0.1,
<<<<<<< HEAD
                do_sample=True,
=======
                do_sample=False,
>>>>>>> 2eed77e66f92ec4f5c66d23bc14fa3709c254859
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                early_stopping=True,
                output_scores=True,
                return_dict_in_generate=True
            )

<<<<<<< HEAD
            raw_sql = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            raw_sql = raw_sql.replace(prompt, "").strip()
            cleaned_sql = self.clean_sql_output(raw_sql)

=======
            # ✅ Correct access to generated sequence
            raw_sql = self.tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)
            raw_sql = raw_sql.replace(prompt, "").strip()
            cleaned_sql = self.clean_sql_output(raw_sql)

            # ✅ Compute token-level confidence
            token_conf = None
            try:
                confidences = [F.softmax(score, dim=-1).max().item() for score in outputs.scores]
                token_conf = sum(confidences) / len(confidences) if confidences else 0.0
                self.logger.info(f"Token confidence: {round(token_conf * 100, 2)}%")
            except Exception as e:
                self.logger.warning(f"Token confidence error: {e}")

>>>>>>> 2eed77e66f92ec4f5c66d23bc14fa3709c254859
            is_valid = self.validate_sql_syntax(cleaned_sql, db_connection)

            return {
                "sql": cleaned_sql,
                "valid": is_valid,
                "raw_output": raw_sql,
                "schema_used": schema_context,
                "confidence": round(token_conf * 100, 2) if token_conf is not None else None,
                "confidence_label": self.interpret_confidence(token_conf)
            }

        except Exception as e:
            self.logger.error(f"Error generating SQL: {e}")
            return {
                "sql": "SELECT 1;",
                "valid": False,
                "error": str(e),
                "raw_output": ""
            }
<<<<<<< HEAD

    # ---------------------- ✅ NEW FUNCTION ---------------------- #
    def execute_sql(self, db_connection, sql: str) -> Dict[str, Any]:
        """Execute the generated SQL and return results."""
        try:
            cursor = db_connection.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description] if cursor.description else []
            db_connection.commit()

            return {
                "success": True,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows)
            }
        except Exception as e:
            self.logger.error(f"SQL Execution Error: {e}")
            return {"success": False, "error": str(e)}

=======
>>>>>>> 2eed77e66f92ec4f5c66d23bc14fa3709c254859
