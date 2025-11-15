# src/services/prompt_builder.py
import re
import logging
from typing import Dict, Any, List, Tuple, Optional

class InputValidationError(Exception):
    """Custom exception for input validation errors."""
    pass

class PromptBuilder:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Security patterns to detect malicious input
        # Patterns that should block (high risk)
        self.BLOCK_PATTERNS = [
            r';\s*DROP\s+',
            r';\s*DELETE\s+FROM\s+\w+\s*;',  # DELETE without WHERE
            r';\s*TRUNCATE\s+',
            r'xp_cmdshell',
            r'exec\s*\(',
            r'execute\s*\(',
        ]
        # Patterns that should warn but might be legitimate
        self.WARN_PATTERNS = [
            r'UNION\s+SELECT',  # Could be legitimate
            r'--',  # SQL comments
            r'/\*.*?\*/',  # Multi-line comments
        ]
        
        # Max lengths to prevent resource exhaustion (configurable via env if needed)
        import os
        self.MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", "2000"))  # Increased from 500
        self.MAX_SCHEMA_TABLES = int(os.getenv("MAX_SCHEMA_TABLES", "10"))
        self.MIN_QUERY_LENGTH = 3
    
    def validate_user_input(self, user_query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate user input for security and quality.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Check if query is empty or None
        if not user_query or not user_query.strip():
            return False, "Query cannot be empty"
        
        query = user_query.strip()
        
        # Check minimum length
        if len(query) < self.MIN_QUERY_LENGTH:
            return False, f"Query too short (minimum {self.MIN_QUERY_LENGTH} characters)"
        
        # Check maximum length
        if len(query) > self.MAX_QUERY_LENGTH:
            return False, f"Query too long (maximum {self.MAX_QUERY_LENGTH} characters)"
        
        # Check for blocking patterns (high risk)
        for pattern in self.BLOCK_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                self.logger.warning(f"Blocking pattern detected in query: {pattern}")
                return False, "Query contains potentially dangerous SQL patterns"
        
        # Check for warning patterns (log but don't block)
        for pattern in self.WARN_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                self.logger.warning(f"Suspicious pattern detected in query (allowed): {pattern}")
        
        # Check for excessive special characters (possible obfuscation)
        special_char_count = sum(1 for c in query if not c.isalnum() and not c.isspace())
        if special_char_count > len(query) * 0.3:  # More than 30% special chars
            return False, "Query contains too many special characters"
        
        # Check for multiple consecutive semicolons
        if ';;' in query:
            return False, "Query contains invalid syntax"
        
        # Check for encoded characters that might bypass filters
        if any(pattern in query for pattern in ['%00', '%27', '%3B', 'char(', 'chr(']):
            return False, "Query contains encoded or suspicious characters"
        
        return True, None
    
    def sanitize_user_input(self, user_query: str) -> str:
        """
        Sanitize user input by removing potentially dangerous elements.
        Use this as a defensive layer even after validation.
        """
        if not user_query:
            return ""
        
        query = user_query.strip()
        
        # Remove SQL comments
        query = re.sub(r'--.*?$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # Remove multiple spaces
        query = re.sub(r'\s+', ' ', query)
        
        # Remove leading/trailing whitespace
        query = query.strip()
        
        return query
    
    def validate_schema_info(self, schema_info: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate schema information before processing.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not schema_info:
            return False, "Schema information is empty"
        
        if not isinstance(schema_info, dict):
            return False, "Schema information must be a dictionary"
        
        # Limit number of tables if too many
        if len(schema_info) > self.MAX_SCHEMA_TABLES:
            self.logger.warning(f"Schema has {len(schema_info)} tables, will limit to {self.MAX_SCHEMA_TABLES} in context")
        
        # Validate structure of each table
        for table_name, table_info in schema_info.items():
            if not isinstance(table_info, dict):
                return False, f"Invalid structure for table {table_name}"
            
            if 'columns' not in table_info:
                return False, f"Table {table_name} missing columns information"
            
            if not isinstance(table_info['columns'], list):
                return False, f"Columns for table {table_name} must be a list"
            
            if not table_info['columns']:
                return False, f"Table {table_name} has no columns"
        
        return True, None
    
    def build_schema_context(self, schema_info: Dict[str, Any], user_query: str) -> str:
        """Build intelligent schema context based on query relevance."""
        # Validate inputs first
        is_valid, error_msg = self.validate_schema_info(schema_info)
        if not is_valid:
            self.logger.error(f"Schema validation failed: {error_msg}")
            return "No valid schema information available."
        
        is_valid, error_msg = self.validate_user_input(user_query)
        if not is_valid:
            self.logger.error(f"User query validation failed: {error_msg}")
            raise InputValidationError(error_msg)
        
        # Sanitize the query
        sanitized_query = self.sanitize_user_input(user_query)
        
        # Find tables relevant to the query
        relevant_tables = self._find_relevant_tables(schema_info, sanitized_query)
        
        if not relevant_tables:
            # If no tables match, use all tables (limited to MAX_SCHEMA_TABLES)
            relevant_tables = list(schema_info.keys())[:self.MAX_SCHEMA_TABLES]
        
        schema_context = "Database Schema:\n"
        
        for table_name in relevant_tables[:self.MAX_SCHEMA_TABLES]:
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
    
    def _find_relevant_tables(self, schema_info: Dict[str, Any], user_query: str) -> List[str]:
        """
        Find tables relevant to the user query using improved matching.
        """
        query_lower = user_query.lower()
        relevant_tables = []
        table_scores = {}  # Track relevance scores
        
        for table_name, table_info in schema_info.items():
            score = 0
            table_name_lower = table_name.lower()
            
            # Check if table name is in query (exact match)
            if table_name_lower in query_lower:
                score += 10
            
            # Check for partial matches (e.g., "order" matches "orders")
            if table_name_lower[:-1] in query_lower or table_name_lower + 's' in query_lower:
                score += 5
            
            # Check if any column names are in query
            for col in table_info.get('columns', []):
                col_name_lower = col['name'].lower()
                if col_name_lower in query_lower:
                    score += 3
            
            # Add table if it has any relevance
            if score > 0:
                table_scores[table_name] = score
        
        # Sort tables by relevance score (highest first)
        relevant_tables = sorted(table_scores.keys(), key=lambda x: table_scores[x], reverse=True)
        
        return relevant_tables
    
    def build_enhanced_prompt(self, question: str, schema_context: str, 
                            db_type: str = "SQLite") -> str:
        """
        Build structured prompt for causal LM models with validation.
        Uses query intent analysis to provide better guidance.
        
        Args:
            question: User's natural language question
            schema_context: Formatted schema information
            db_type: Database type (SQLite, PostgreSQL, MySQL)
        """
        # Validate and sanitize question
        is_valid, error_msg = self.validate_user_input(question)
        if not is_valid:
            raise InputValidationError(error_msg)
        
        sanitized_question = self.sanitize_user_input(question)
        
        # Analyze query intent for better prompt construction
        intent = self.get_query_intent(sanitized_question)
        
        # Customize instructions based on database type
        syntax_instruction = {
            "SQLite": "Use proper SQLite syntax",
            "PostgreSQL": "Use proper PostgreSQL syntax",
            "MySQL": "Use proper MySQL syntax"
        }.get(db_type, "Use proper SQL syntax")
        
        # Build intent-specific instructions
        intent_instructions = []
        
        if intent["requires_aggregation"]:
            intent_instructions.append("- Use aggregate functions (COUNT, SUM, AVG, MAX, MIN) as needed")
        
        if intent["requires_grouping"]:
            intent_instructions.append("- Use GROUP BY to group results")
        
        if intent["requires_join"]:
            intent_instructions.append("- Use JOINs to connect related tables")
        
        if intent["requires_ordering"]:
            intent_instructions.append("- Use ORDER BY with LIMIT to get top/best results")
        
        if intent["time_based"]:
            intent_instructions.append("- Use date/time functions for filtering and sorting")
        
        # Combine base instructions with intent-specific ones
        base_instructions = [
            "- Use only tables and columns mentioned in the schema",
            f"- {syntax_instruction}",
            "- Use JOINs when needed to connect related tables",
            "- Use ORDER BY and LIMIT 1 for \"top\", \"highest\", \"best\", or \"first\" queries",
            "- For questions like \"number of orders per customer\", use COUNT() with GROUP BY and JOIN",
            "- Use WHERE for filtering conditions",
            "- Use GROUP BY and aggregates (COUNT, SUM, AVG, MAX, MIN) only when explicitly requested",
            "- Return ONLY the SQL query, nothing else",
            "- Do NOT include semicolons to chain multiple statements"
        ]
        
        all_instructions = base_instructions + intent_instructions
        
        instructions_text = "\n".join(all_instructions)
        
        return f"""Convert the following natural language question into a {db_type} SQL query.

{schema_context}

Instructions:
{instructions_text}

Question: {sanitized_question}

SQL:"""
    
    def extract_sql_from_response(self, response: str) -> str:
        """Extract SQL from model response.
        
        Handles cases where the model output contains:
        - Full prompt text (instructions, schema, etc.)
        - Explanations before/after SQL
        - Markdown code blocks
        - Multiple SQL statements (returns first one)
        - Extra text or formatting
        """
        if not response:
            return ""
        
        # First, try to extract from markdown code blocks (most reliable)
        # Look for ```sql ... ``` pattern
        code_block_pattern = r'```sql\s*(.*?)\s*```'
        code_block_match = re.search(code_block_pattern, response, re.IGNORECASE | re.DOTALL)
        if code_block_match:
            sql = code_block_match.group(1).strip()
            # If we found SQL in code block, clean it and return
            sql = self._clean_extracted_sql(sql)
            if sql:
                return sql
        
        # If no code block found, look for SQL statement directly
        # Remove all markdown formatting first
        sql = re.sub(r'```sql\s*', '', response)
        sql = re.sub(r'```\s*', '', sql)
        
        # Look for patterns like "SQL:" or "SQL Query:" followed by SQL
        sql_label_patterns = [
            r'SQL:\s*(SELECT|INSERT|UPDATE|DELETE|WITH|CREATE|DROP|ALTER)',
            r'SQL\s+Query:\s*(SELECT|INSERT|UPDATE|DELETE|WITH|CREATE|DROP|ALTER)',
            r'```sql\s*(SELECT|INSERT|UPDATE|DELETE|WITH|CREATE|DROP|ALTER)',
        ]
        
        sql_text = None
        for pattern in sql_label_patterns:
            match = re.search(pattern, sql, re.IGNORECASE | re.DOTALL)
            if match:
                # Extract SQL starting from the keyword after the label
                start_pos = match.end() - len(match.group(1))
                sql_text = sql[start_pos:]
                break
        
        # If no label pattern found, try to find SQL statement directly
        if sql_text is None:
            sql_keywords = r'(SELECT|INSERT|UPDATE|DELETE|WITH|CREATE|DROP|ALTER)'
            sql_match = re.search(
                sql_keywords + r'.*?',
                sql,
                re.IGNORECASE | re.DOTALL
            )
            
            if sql_match:
                # Extract from the match position
                start_pos = sql_match.start()
                sql_text = sql[start_pos:]
        
        if sql_text:
            
            # Find where SQL ends - look for semicolon followed by newline or end of string
            # This is the most reliable way to detect end of SQL
            semicolon_match = re.search(r';\s*(?:\n|$)', sql_text)
            if semicolon_match:
                sql_cleaned = sql_text[:semicolon_match.end()].strip()
            else:
                # If no semicolon, try to find end by looking for non-SQL patterns
                # Stop at common explanation keywords or prompt-like text
                end_keywords = [
                    r'###\s+',  # Markdown headers
                    r'Explanation',
                    r'Note:',
                    r'This query',
                    r'The SQL',
                    r'Use\s+(WHERE|GROUP BY|JOIN)',  # Instruction text
                    r'Return only',
                    r'Ensure the query',
                ]
                
                sql_cleaned = sql_text
                for pattern in end_keywords:
                    match = re.search(pattern, sql_text, re.IGNORECASE)
                    if match:
                        sql_cleaned = sql_text[:match.start()].strip()
                        break
                
                # If still no clear end, extract up to first line that looks like instructions
                if sql_cleaned == sql_text:
                    lines = sql_text.split('\n')
                    sql_lines = []
                    for line in lines:
                        line_stripped = line.strip()
                        # Stop if we hit instruction-like text
                        if any(keyword in line_stripped.lower() for keyword in [
                            'use ', 'return only', 'ensure', 'instruction', 
                            'database schema', 'task:', 'question:'
                        ]):
                            break
                        # Stop if line is too long and doesn't look like SQL
                        if len(line_stripped) > 100 and not re.search(
                            r'\b(SELECT|FROM|WHERE|JOIN|GROUP|ORDER|LIMIT|INSERT|UPDATE|DELETE|AND|OR|IN|LIKE|COUNT|SUM|AVG|MAX|MIN|AS|ON|USING|INNER|LEFT|RIGHT|OUTER)\b',
                            line, re.IGNORECASE
                        ):
                            break
                        sql_lines.append(line)
                    sql_cleaned = '\n'.join(sql_lines).strip()
            
            sql = sql_cleaned
        else:
            # If no SQL keyword found, return empty
            return ""
        
        # Clean the extracted SQL
        sql = self._clean_extracted_sql(sql)
        
        # Additional validation: check for multiple statements
        if sql.count(';') > 1:
            self.logger.warning("Multiple SQL statements detected, using first one")
            sql = sql.split(';')[0] + ';'
        
        return sql
    
    def _clean_extracted_sql(self, sql: str) -> str:
        """Clean extracted SQL by removing non-SQL content."""
        if not sql:
            return ""
        
        # Remove instruction text patterns that might appear before SQL
        # Patterns like "with GROUP BY and JOIN - Do NOT include semicolons SQL:"
        instruction_patterns = [
            r'^.*?with\s+GROUP\s+BY.*?SQL:\s*',  # "with GROUP BY ... SQL:"
            r'^.*?Do\s+NOT\s+include.*?SQL:\s*',  # "Do NOT include ... SQL:"
            r'^.*?Return\s+ONLY.*?SQL:\s*',  # "Return ONLY ... SQL:"
            r'^.*?SQL:\s*',  # Generic "SQL:" label
            r'^.*?SQL\s+Query:\s*',  # "SQL Query:"
        ]
        
        for pattern in instruction_patterns:
            sql = re.sub(pattern, '', sql, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove any lines that are clearly instructions or prompt text
        lines = sql.split('\n')
        cleaned_lines = []
        sql_keywords_pattern = r'\b(SELECT|FROM|WHERE|JOIN|GROUP|ORDER|LIMIT|INSERT|UPDATE|DELETE|AND|OR|IN|LIKE|COUNT|SUM|AVG|MAX|MIN|AS|ON|USING|INNER|LEFT|RIGHT|OUTER|HAVING|UNION|EXCEPT|INTERSECT)\b'
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines at the start
            if not line_stripped and not cleaned_lines:
                continue
            
            # Skip lines that are clearly instructions (more comprehensive list)
            instruction_keywords = [
                'use ', 'return only', 'ensure', 'instruction', 
                'database schema', 'task:', 'question:', '###',
                'with group by', 'do not include', 'semicolons',
                'chain multiple', 'statements'
            ]
            if any(keyword in line_stripped.lower() for keyword in instruction_keywords):
                # But allow if it's part of actual SQL (e.g., "USE database;" is valid SQL)
                if not line_stripped.upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH', 'CREATE', 'DROP', 'ALTER')):
                    continue
            
            # Skip lines that are too long and don't contain SQL keywords
            if len(line_stripped) > 80 and not re.search(sql_keywords_pattern, line, re.IGNORECASE):
                # Check if it contains SQL-like characters
                if not any(char in line for char in ['(', ')', '=', '<', '>', ',', '.', "'", '"']):
                    continue
            
            cleaned_lines.append(line)
        
        sql = '\n'.join(cleaned_lines).strip()
        
        # Remove any remaining markdown or formatting
        sql = re.sub(r'^[`\s]*', '', sql)
        sql = re.sub(r'[`\s]*$', '', sql)
        
        # Remove instruction text that might be at the start
        # Look for patterns like "with X and Y - instruction text SQL:"
        sql = re.sub(r'^.*?-\s*[^-]*?SQL:\s*', '', sql, flags=re.IGNORECASE)
        
        # Remove any leading/trailing whitespace from each line
        sql_lines = [line.strip() for line in sql.split('\n') if line.strip()]
        sql = ' '.join(sql_lines)  # Join into single line (SQL can be on one line)
        
        # Remove any remaining instruction text at the start
        # Pattern: "with GROUP BY and JOIN - Do NOT include semicolons to chain multiple statements"
        sql = re.sub(r'^with\s+.*?statements?\s*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'^.*?do\s+not\s+include.*?statements?\s*', '', sql, flags=re.IGNORECASE)
        
        # Ensure it ends with semicolon if it's a valid SQL statement
        if sql and not sql.endswith(';'):
            if re.search(r'\b(SELECT|INSERT|UPDATE|DELETE)\b', sql, re.IGNORECASE):
                sql += ';'
        
        return sql
    
    def get_query_intent(self, user_query: str) -> Dict[str, Any]:
        """
        Analyze user query to understand intent.
        Useful for better prompt construction and validation.
        
        Returns:
            Dict with intent information (query_type, requires_aggregation, etc.)
        """
        query_lower = user_query.lower()
        
        intent = {
            "query_type": "select",  # select, count, aggregate, comparison
            "requires_aggregation": False,
            "requires_join": False,
            "requires_ordering": False,
            "requires_grouping": False,
            "time_based": False
        }
        
        # Check for aggregation keywords
        aggregation_keywords = ['count', 'sum', 'average', 'avg', 'total', 'maximum', 'max', 'minimum', 'min']
        if any(keyword in query_lower for keyword in aggregation_keywords):
            intent["requires_aggregation"] = True
            intent["query_type"] = "aggregate"
        
        # Check for grouping indicators
        grouping_keywords = ['per', 'each', 'by', 'for every']
        if any(keyword in query_lower for keyword in grouping_keywords):
            intent["requires_grouping"] = True
        
        # Check for ordering keywords
        ordering_keywords = ['top', 'best', 'worst', 'highest', 'lowest', 'first', 'last']
        if any(keyword in query_lower for keyword in ordering_keywords):
            intent["requires_ordering"] = True
        
        # Check for time-based queries
        time_keywords = ['date', 'time', 'year', 'month', 'day', 'week', 'recent', 'latest', 'oldest']
        if any(keyword in query_lower for keyword in time_keywords):
            intent["time_based"] = True
        
        # Check for potential joins (multiple entity references)
        join_indicators = ['and', 'with', 'from', 'in', 'of']
        # This is a simple heuristic - could be improved
        if sum(1 for keyword in join_indicators if keyword in query_lower) >= 2:
            intent["requires_join"] = True
        
        return intent