# src/services/prompt_builder.py
import re
import logging
from typing import Dict, Any

class PromptBuilder:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def build_schema_context(self, schema_info: Dict[str, Any], user_query: str) -> str:
        """Build intelligent schema context based on query relevance."""
        if not schema_info:
            return "No schema information available."
        
        # Find tables relevant to the query
        relevant_tables = self._find_relevant_tables(schema_info, user_query)
        
        if not relevant_tables:
            # If no tables match, use all tables (first 5 to avoid prompt overflow)
            relevant_tables = list(schema_info.keys())[:5]
        
        schema_context = "Database Schema:\n"
        
        for table_name in relevant_tables:
            if table_name in schema_info:
                table_info = schema_info[table_name]
                schema_context += f"Table: {table_name}\n"
                
                for col in table_info.get('columns', []):
                    nullable_str = "NOT NULL" if not col.get('nullable', True) else "NULL"
                    schema_context += f"  - {col['name']} ({col['type']}) - {nullable_str}\n"
                
                # Add foreign keys if available
                foreign_keys = table_info.get('foreign_keys', [])
                if foreign_keys:
                    schema_context += "  Foreign Keys:\n"
                    for fk in foreign_keys:
                        schema_context += f"    - {fk}\n"
                
                schema_context += "\n"
        
        return schema_context
    
    def _find_relevant_tables(self, schema_info: Dict[str, Any], user_query: str) -> list:
        """Find tables relevant to the user query."""
        query_lower = user_query.lower()
        relevant_tables = []
        
        for table_name, table_info in schema_info.items():
            # Check if table name is in query
            table_in_query = table_name.lower() in query_lower
            
            # Check if any column names are in query
            columns_in_query = False
            for col in table_info.get('columns', []):
                if col['name'].lower() in query_lower:
                    columns_in_query = True
                    break
            
            if table_in_query or columns_in_query:
                relevant_tables.append(table_name)
        
        return relevant_tables
    
    def build_enhanced_prompt(self, question: str, schema_context: str) -> str:
        """Build structured prompt for causal LM models."""
        return f"""### Task: Convert the following natural language question into a SQLite SQL query.

### Database Schema:
{schema_context}

### Instructions:
- Use only tables and columns mentioned in the schema
- Use proper SQLite syntax
- Use JOINs when needed to connect related tables
- Use ORDER BY and LIMIT 1 for "top", "highest", "best", or "first" queries
- For questions like "number of orders per customer", use COUNT() with GROUP BY and JOIN
- Use WHERE for filtering conditions
- Use GROUP BY and aggregates (COUNT, SUM, AVG, MAX, MIN) only when explicitly requested
- Return only the SQL query without any explanations
- Ensure the query is executable in SQLite

### Question: {question}

### SQL Query:
```sql
"""
    
    def extract_sql_from_response(self, response: str) -> str:
        """Extract SQL from model response."""
        # Remove markdown code blocks
        sql = re.sub(r'```sql\s*', '', response)
        sql = re.sub(r'```\s*', '', sql)
        
        # Find SQL statement
        sql_match = re.search(
            r'(SELECT|INSERT|UPDATE|DELETE|WITH|CREATE|DROP|ALTER).*?(?=```|$)', 
            sql, 
            re.IGNORECASE | re.DOTALL
        )
        
        if sql_match:
            sql = sql_match.group(0).strip()
        
        # Clean up trailing whitespace
        sql = re.sub(r'[\s\n]*$', '', sql)
        
        # Add semicolon if missing
        if sql and not sql.endswith(';'):
            sql += ';'
        
        return sql