import re
import logging
from typing import Dict, Any

class SQLValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    # ---------------------------------------------------------
    # 1. CLEAN SQL
    # ---------------------------------------------------------
    def clean_sql(self, sql: str) -> str:
        """Clean SQL extracted from LLM or user input."""
        if not sql:
            return ""

        # Remove markdown 
        sql = re.sub(r'sql|```', '', sql, flags=re.IGNORECASE).strip()

        # Extract starting from first SQL keyword
        m = re.search(r'\b(SELECT|WITH)\b', sql, re.IGNORECASE)
        if m:
            sql = sql[m.start():]

        # Remove explanations after SQL
        lines = sql.split("\n")
        cleaned = []
        for line in lines:
            if any(k in line.lower() for k in ["explanation", "note", "this query", "returns"]):
                break
            cleaned.append(line)

        return "\n".join(cleaned).strip().rstrip(";")

    # ---------------------------------------------------------
    # 2. SAFETY CHECK  (NO UPDATE/DELETE/etc.)
    # ---------------------------------------------------------
    def is_safe_sql(self, sql: str) -> Dict[str, Any]:
        """Allow only SELECT or WITH queries."""
        sql_upper = sql.upper().strip()

        if not sql:
            return {'safe': False, 'reason': 'No SQL found'}

        # Only SELECT and WITH allowed
        if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
            return {'safe': False, 'reason': 'Only SELECT/WITH queries allowed'}

        # Detect forbidden statements
        forbidden = [
            r'\bDROP\b',
            r'\bDELETE\b',
            r'\bUPDATE\b',
            r'\bINSERT\b',
            r'\bALTER\b',
            r'\bTRUNCATE\b',
            r'\bCREATE\b'
        ]

        for pattern in forbidden:
            if re.search(pattern, sql_upper):
                return {'safe': False, 'reason': f'Dangerous statement detected: {pattern}'}

        return {'safe': True, 'reason': 'SQL is safe'}

    # ---------------------------------------------------------
    # 3. SYNTAX VALIDATION
    # ---------------------------------------------------------
    def validate_sql_syntax(self, sql: str, db_connection) -> Dict[str, Any]:
        """Validate SQL syntax using EXPLAIN safely."""
        try:
            cursor = db_connection.cursor()
            try:
                cursor.execute(f"EXPLAIN {sql}")
            except Exception:
                cursor.execute(f"EXPLAIN QUERY PLAN {sql}")

            return {'valid': True, 'error': None}

        except Exception as e:
            return {'valid': False, 'error': str(e)}

    # ---------------------------------------------------------
    # 4. COMBINED VALIDATION
    # ---------------------------------------------------------
    def validate_and_clean(self, sql: str, db_connection) -> Dict[str, Any]:
        result = {
            'original_sql': sql,
            'cleaned_sql': None,
            'is_valid': False,
            'is_safe': False,
            'syntax_error': None,
            'safety_issues': None
        }

        # Step 1: clean SQL
        cleaned = self.clean_sql(sql)
        result['cleaned_sql'] = cleaned

        if not cleaned:
            result['syntax_error'] = 'No valid SQL found'
            return result

        # Step 2: safety
        safety = self.is_safe_sql(cleaned)
        result['is_safe'] = safety['safe']

        if not safety['safe']:
            result['safety_issues'] = safety['reason']
            return result

        # Step 3: syntax
        syntax = self.validate_sql_syntax(cleaned, db_connection)
        result['is_valid'] = syntax['valid']

        if not syntax['valid']:
            result['syntax_error'] = syntax['error']

        return result