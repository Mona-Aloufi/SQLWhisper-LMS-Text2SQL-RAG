# src/services/text2sql_service.py
import logging
from typing import Dict, Any
from .model_handler import ModelHandler
from .prompt_builder import PromptBuilder
from .sql_validator import SQLValidator
from .query_executor import QueryExecutor
from .confidence_analyzer import ConfidenceAnalyzer

class EnhancedText2SQLService:
    def __init__(self, model_name=None, device=None):
        """
        Enhanced Text2SQL service with modular architecture.
        Integrates with the database system we built.
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize all components
        self.model_handler = ModelHandler(model_name, device)
        self.prompt_builder = PromptBuilder()
        self.sql_validator = SQLValidator()
        self.query_executor = QueryExecutor()
        self.confidence_analyzer = ConfidenceAnalyzer()
        
        self.logger.info("✅ EnhancedText2SQLService initialized with all components")
    
    def generate_sql(self, question: str, db_connection, max_retries: int = 2) -> Dict[str, Any]:
        """Generate SQL from natural language question."""
        try:
            # Extract schema from database connection
            schema_info = self._extract_schema_from_connection(db_connection)
            
            # Build schema context
            schema_context = self.prompt_builder.build_schema_context(schema_info, question)
            
            # Build enhanced prompt
            prompt = self.prompt_builder.build_enhanced_prompt(question, schema_context)
            
            # Generate SQL with model
            generation_result = self.model_handler.generate_with_confidence(prompt)
            
            if generation_result.get('error'):
                return {
                    'sql': '',
                    'valid': False,
                    'error': generation_result['error'],
                    'confidence': 0.0,
                    'confidence_label': 'Error'
                }
            
            # Extract SQL from response
            raw_sql = generation_result['generated_text']
            extracted_sql = self.prompt_builder.extract_sql_from_response(raw_sql)
            
            # Validate and clean SQL
            validation_result = self.sql_validator.validate_and_clean(extracted_sql, db_connection)
            
            # Analyze confidence
            confidence_data = self.confidence_analyzer.calculate_token_confidence(
                generation_result.get('confidences', [])
            )
            
            # Analyze generation quality
            quality_analysis = self.confidence_analyzer.analyze_generation_quality(
                raw_sql, 
                confidence_data['avg_confidence']
            )
            
            return {
                'sql': validation_result['cleaned_sql'],
                'valid': validation_result['is_valid'],
                'is_safe': validation_result['is_safe'],
                'raw_output': raw_sql,
                'schema_used': schema_context,
                'confidence': confidence_data['avg_confidence'],
                'confidence_label': confidence_data['confidence_label'],
                'confidence_details': confidence_data,
                'quality_analysis': quality_analysis,
                'validation_result': validation_result,
                'model_info': self.model_handler.get_model_info()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating SQL: {e}")
            return {
                'sql': '',
                'valid': False,
                'error': str(e),
                'raw_output': '',
                'confidence': 0.0,
                'confidence_label': 'Error'
            }
    
    def execute_sql(self, db_connection, sql: str) -> Dict[str, Any]:
        """Execute SQL query using the query executor."""
        return self.query_executor.execute_query(db_connection, sql)
    
    def _extract_schema_from_connection(self, db_connection) -> Dict[str, Any]:
        """Extract schema information from database connection."""
        try:
            cursor = db_connection.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            schema_info = {}
            
            for table in tables:
                table_name = table[0]
                try:
                    # Get table columns
                    cursor.execute(f'PRAGMA table_info("{table_name}")')
                    columns = cursor.fetchall()
                    
                    schema_info[table_name] = {
                        'columns': [
                            {
                                'name': col[1],
                                'type': col[2],
                                'nullable': not col[3],
                                'primary_key': bool(col[5])
                            }
                            for col in columns
                        ]
                    }
                    
                    # Get foreign keys
                    cursor.execute(f'PRAGMA foreign_key_list("{table_name}")')
                    foreign_keys = cursor.fetchall()
                    
                    schema_info[table_name]['foreign_keys'] = [
                        f"{fk[3]} -> {fk[2]}.{fk[4]}"  # from_col -> to_table.to_col
                        for fk in foreign_keys
                    ]
                    
                except Exception as e:
                    self.logger.warning(f"Skipping table {table_name}: {e}")
                    continue
            
            return schema_info
            
        except Exception as e:
            self.logger.error(f"Error extracting schema: {e}")
            return {}
    
    def get_table_info(self, db_connection, table_name: str) -> Dict[str, Any]:
        """Get information about a specific table."""
        return self.query_executor.get_table_info(db_connection, table_name)
    
    def test_connection(self, db_connection) -> bool:
        """Test database connection."""
        return self.query_executor.test_connection(db_connection)
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information."""
        return {
            'model_info': self.model_handler.get_model_info(),
            'service_status': 'active',
            'components': {
                'model_handler': True,
                'prompt_builder': True,
                'sql_validator': True,
                'query_executor': True,
                'confidence_analyzer': True
            }
        }