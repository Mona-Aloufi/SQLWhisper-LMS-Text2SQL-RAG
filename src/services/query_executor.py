# src/services/query_executor.py
import logging
from typing import Dict, Any, List, Tuple

class QueryExecutor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def execute_query(self, db_connection, sql: str) -> Dict[str, Any]:
        """Execute SQL query and return results."""
        try:
            cursor = db_connection.cursor()
            cursor.execute(sql)
            
            # Check if it's a SELECT query (returns results)
            if sql.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # Limit results to prevent memory issues
                max_rows = 1000
                if len(rows) > max_rows:
                    rows = rows[:max_rows]
                    self.logger.warning(f"Results limited to {max_rows} rows for performance")
                
                result = {
                    'success': True,
                    'query_type': 'SELECT',
                    'columns': columns,
                    'rows': rows,
                    'row_count': len(rows),
                    'message': f'Query executed successfully, {len(rows)} rows returned'
                }
            else:
                # For INSERT, UPDATE, DELETE
                affected_rows = cursor.rowcount
                db_connection.commit()
                
                result = {
                    'success': True,
                    'query_type': 'MODIFICATION',
                    'affected_rows': affected_rows,
                    'message': f'Modification query executed successfully, {affected_rows} rows affected'
                }
        
        except Exception as e:
            self.logger.error(f"SQL Execution Error: {e}")
            result = {
                'success': False,
                'error': str(e),
                'message': f'Query execution failed: {str(e)}'
            }
        
        return result
    
    def get_table_info(self, db_connection, table_name: str) -> Dict[str, Any]:
        """Get information about a specific table."""
        try:
            cursor = db_connection.cursor()
            
            # Get column info
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
            row_count = cursor.fetchone()[0]
            
            column_info = []
            for col in columns:
                column_info.append({
                    'name': col[1],
                    'type': col[2],
                    'not_null': bool(col[3]),
                    'default': col[4],
                    'primary_key': bool(col[5])
                })
            
            return {
                'success': True,
                'table_name': table_name,
                'columns': column_info,
                'row_count': row_count
            }
            
        except Exception as e:
            self.logger.error(f"Error getting table info: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_connection(self, db_connection) -> bool:
        """Test if database connection is working."""
        try:
            cursor = db_connection.cursor()
            cursor.execute("SELECT 1")
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False