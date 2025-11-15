# src/services/sql_validator.py
import re
import logging
from typing import Dict, Any

class SQLValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.safe_keywords = {
            'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER JOIN', 'LEFT JOIN', 
            'RIGHT JOIN', 'OUTER JOIN', 'GROUP BY', 'ORDER BY', 'LIMIT',
            'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'DISTINCT', 'HAVING',
            'UNION', 'UNION ALL', 'EXISTS', 'IN', 'NOT IN', 'LIKE',
            'BETWEEN', 'AND', 'OR', 'NOT', 'IS NULL', 'IS NOT NULL',
            'AS', 'ON', 'USING', 'CREATE', 'DROP', 'ALTER', 'INSERT',
            'UPDATE', 'DELETE', 'COMMIT', 'ROLLBACK', 'BEGIN'
        }
    
    def clean_sql(self, sql: str) -> str:
        """Clean and sanitize SQL query.
        
        This method is called after extract_sql_from_response, so it should
        handle already-extracted SQL, but also be robust for edge cases.
        """
        if not sql:
            return ""
        
        # Remove markdown formatting
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*', '', sql)
        
        # Find SQL statement - look for SQL keywords
        sql_keywords = r'(SELECT|INSERT|UPDATE|DELETE|WITH|CREATE|DROP|ALTER)'
        sql_match = re.search(
            sql_keywords + r'.*?',
            sql,
            re.IGNORECASE | re.DOTALL
        )
        
        if sql_match:
            start_pos = sql_match.start()
            sql_text = sql[start_pos:]
            
            # Try to find where SQL ends
            end_patterns = [
                r';\s*(?:\n|$)',  # Semicolon followed by newline or end
                r';\s*(?=\n\n)',  # Semicolon followed by double newline
                r';\s*(?=Explanation|Note|This|The query|The SQL)',  # Semicolon before explanation
            ]
            
            sql_cleaned = sql_text
            for pattern in end_patterns:
                match = re.search(pattern, sql_text, re.IGNORECASE)
                if match:
                    sql_cleaned = sql_text[:match.end()].strip()
                    break
            
            # If no semicolon found, extract up to first explanation line
            if not sql_cleaned.strip().endswith(';'):
                lines = sql_cleaned.split('\n')
                sql_lines = []
                explanation_keywords = ['explanation', 'note', 'this query', 'the sql', 'returns', 'finds']
                
                for line in lines:
                    line_lower = line.strip().lower()
                    if any(keyword in line_lower for keyword in explanation_keywords):
                        break
                    if line.strip() and not re.search(r'\b(SELECT|FROM|WHERE|JOIN|GROUP|ORDER|LIMIT|INSERT|UPDATE|DELETE|AND|OR|IN|LIKE|COUNT|SUM|AVG|MAX|MIN)\b', line, re.IGNORECASE):
                        if len(line.strip()) > 50 and not any(char in line for char in ['(', ')', '=', '<', '>']):
                            break
                    sql_lines.append(line)
                
                sql_cleaned = '\n'.join(sql_lines).strip()
            
            sql = sql_cleaned
        else:
            # If no SQL keyword found, return empty
            return ""
        
        # Clean up trailing whitespace
        sql = re.sub(r'[\s\n]*$', '', sql)
        
        # Remove any remaining markdown or formatting
        sql = re.sub(r'^[`\s]*', '', sql)
        sql = re.sub(r'[`\s]*$', '', sql)
        
        # Add semicolon if missing (only for valid SQL statements)
        if sql and not sql.endswith(';'):
            if re.search(r'\b(SELECT|INSERT|UPDATE|DELETE)\b', sql, re.IGNORECASE):
                sql += ';'
        
        return sql
    
    def validate_sql_syntax(self, sql: str, db_connection) -> Dict[str, Any]:
        """Validate SQL syntax against the database."""
        try:
            
            cursor = db_connection.cursor()
            cursor.execute(f"EXPLAIN {sql}")
            return {
                'valid': True,
                'error': None,
                'message': 'SQL syntax is valid'
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'message': f'SQL syntax error: {str(e)}'
            }
    
    def is_safe_sql(self, sql: str) -> Dict[str, Any]:
        """Check if SQL is safe to execute."""
        if not sql:
            return {'safe': False, 'reason': 'Empty SQL'}
        
        sql_upper = sql.upper()
        
        # Dangerous patterns to avoid
        dangerous_patterns = [
            r'DROP\s+TABLE',
            r'DROP\s+DATABASE',
            r'TRUNCATE',
            r'DELETE\s+FROM\s+\w+$',  # DELETE without WHERE
            r'UPDATE\s+\w+\s+SET',    # UPDATE without WHERE is dangerous
            r'INSERT\s+INTO\s+\w+\s+VALUES',  # Could be dangerous
            r'ALTER\s+TABLE',
            r'CREATE\s+TABLE',
            r'EXECUTE',
            r'EXEC',
            r'SP_',
            r'XP_',
            r';\s*DROP',
            r';\s*TRUNCATE',
            r';\s*ALTER',
            r';\s*CREATE'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql_upper):
                return {
                    'safe': False, 
                    'reason': f'Dangerous SQL pattern detected: {pattern}'
                }
        
        # Check for safe keywords
        sql_words = re.findall(r'\b\w+\b', sql_upper)
        safe_count = sum(1 for word in sql_words if word in self.safe_keywords)
        total_words = len(sql_words)
        
        safety_ratio = safe_count / total_words if total_words > 0 else 0
        
        if safety_ratio < 0.3:  # Less than 30% safe keywords
            return {
                'safe': False,
                'reason': f'Low safety ratio: {safety_ratio:.2%} safe keywords'
            }
        
        return {
            'safe': True,
            'reason': 'SQL appears safe',
            'safety_ratio': safety_ratio
        }
    
    def validate_and_clean(self, sql: str, db_connection) -> Dict[str, Any]:
        """Validate, clean, and check safety of SQL."""
        result = {
            'original_sql': sql,
            'cleaned_sql': None,
            'is_valid': False,
            'is_safe': False,
            'syntax_error': None,
            'safety_issues': None
        }
        
        # Clean SQL first
        cleaned_sql = self.clean_sql(sql)
        result['cleaned_sql'] = cleaned_sql
        
        if not cleaned_sql:
            result['syntax_error'] = 'No valid SQL found'
            return result
        
        # Check safety
        safety_check = self.is_safe_sql(cleaned_sql)
        result['is_safe'] = safety_check['safe']
        if not safety_check['safe']:
            result['safety_issues'] = safety_check['reason']
            return result
        
        # Validate syntax
        syntax_check = self.validate_sql_syntax(cleaned_sql, db_connection)
        result['is_valid'] = syntax_check['valid']
        if not syntax_check['valid']:
            result['syntax_error'] = syntax_check['error']
        
        return result