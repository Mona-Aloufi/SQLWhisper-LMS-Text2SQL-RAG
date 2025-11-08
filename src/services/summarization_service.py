# src/services/summarization_service.py
import logging
from typing import Dict, List, Any
import pandas as pd
import numpy as np

class ResultSummarizationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Generic Summarization Service")

    def generate_summary(self, question: str, results: List[Dict], sql_query: str) -> Dict[str, Any]:
        """
        Generate generic plain English summary for any database.
        """
        if not results:
            return {
                "summary": "No data was found matching your criteria.",
                "success": True,
                "row_count": 0
            }

        try:
            df = pd.DataFrame(results)
            summary = self._generate_generic_summary(question, df, sql_query)
            
            return {
                "summary": summary,
                "success": True,
                "row_count": len(df)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return {
                "summary": "Unable to generate summary due to a processing error.",
                "success": False,
                "error": str(e)
            }

    def _generate_generic_summary(self, question: str, df: pd.DataFrame, sql_query: str) -> str:
        """Generate generic summary based on data patterns and question intent."""
        
        question_lower = question.lower()
        sql_lower = sql_query.lower()
        row_count = len(df)
        
        # Get data characteristics
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        text_cols = df.select_dtypes(include=[object]).columns.tolist()
        
        # Handle different query types based on patterns
        if self._is_count_query(question_lower, sql_lower):
            count_value = self._extract_count_value(df)
            return f"The query returned {count_value} records in total."
        
        elif self._is_average_query(question_lower, sql_lower) and numeric_cols:
            avg_value = df[numeric_cols[0]].mean()
            field_name = self._clean_field_name(numeric_cols[0])
            return f"The average {field_name} is {avg_value:.1f} across {row_count} records."
        
        elif self._is_max_query(question_lower, sql_lower) and numeric_cols:
            max_value = df[numeric_cols[0]].max()
            field_name = self._clean_field_name(numeric_cols[0])
            return f"The maximum {field_name} is {max_value:.1f} among {row_count} records."
        
        elif self._is_min_query(question_lower, sql_lower) and numeric_cols:
            min_value = df[numeric_cols[0]].min()
            field_name = self._clean_field_name(numeric_cols[0])
            return f"The minimum {field_name} is {min_value:.1f} among {row_count} records."
        
        elif row_count == 1 and numeric_cols:
            # Single record with numeric data
            value = df[numeric_cols[0]].iloc[0]
            field_name = self._clean_field_name(numeric_cols[0])
            return f"The data shows a {field_name} of {value:.1f} for this record."
        
        elif row_count <= 5 and text_cols:
            # Small result set with text data
            sample_items = [str(row[text_cols[0]]) for _, row in df.head(3).iterrows()]
            if len(sample_items) == 1:
                return f"Found 1 record: {sample_items[0]}"
            else:
                items_text = ", ".join(sample_items)
                return f"Found {row_count} records including: {items_text}"
        
        else:
            # Generic summary
            if numeric_cols:
                field_name = self._clean_field_name(numeric_cols[0])
                avg_value = df[numeric_cols[0]].mean()
                return f"Analysis of {row_count} records shows an average {field_name} of {avg_value:.1f}."
            else:
                return f"The query returned {row_count} records matching the specified criteria."

    def _is_count_query(self, question_lower: str, sql_lower: str) -> bool:
        """Check if this is a count query."""
        return any(word in question_lower for word in ['count', 'total', 'how many', 'number of']) or 'count(' in sql_lower

    def _is_average_query(self, question_lower: str, sql_lower: str) -> bool:
        """Check if this is an average query."""
        return any(word in question_lower for word in ['average', 'avg', 'mean']) or 'avg(' in sql_lower

    def _is_max_query(self, question_lower: str, sql_lower: str) -> bool:
        """Check if this is a maximum query."""
        return any(word in question_lower for word in ['max', 'maximum', 'highest', 'top']) or 'max(' in sql_lower

    def _is_min_query(self, question_lower: str, sql_lower: str) -> bool:
        """Check if this is a minimum query."""
        return any(word in question_lower for word in ['min', 'minimum', 'lowest', 'bottom']) or 'min(' in sql_lower

    def _extract_count_value(self, df: pd.DataFrame) -> int:
        """Extract count value from dataframe."""
        for col in df.columns:
            if 'count' in col.lower() and len(df) == 1:
                try:
                    return int(df[col].iloc[0])
                except:
                    continue
        return len(df)

    def _clean_field_name(self, field_name: str) -> str:
        """Clean SQL field names for natural language."""
        # Remove SQL functions and underscores
        clean_name = field_name.lower()
        clean_name = clean_name.replace('avg(', '').replace('count(', '').replace('max(', '').replace('min(', '')
        clean_name = clean_name.replace(')', '').replace('_', ' ')
        clean_name = clean_name.strip()
        
        # Common field name improvements
        field_map = {
            'id': 'ID',
            'name': 'name', 
            'date': 'date',
            'time': 'time',
            'price': 'price',
            'amount': 'amount',
            'total': 'total',
            'score': 'score',
            'grade': 'grade',
            'age': 'age',
            'salary': 'salary',
            'quantity': 'quantity'
        }
        
        return field_map.get(clean_name, clean_name)

    def quick_insights(self, results: List[Dict], question: str) -> List[str]:
        """Generate generic insights for any database."""
        if not results:
            return ["No records were found matching your criteria."]

        try:
            summary_data = self.generate_summary(question, results, "")
            if summary_data["success"]:
                return [summary_data["summary"]]
            else:
                return ["Unable to generate insights for this data."]
                
        except Exception as e:
            self.logger.error(f"Error in quick_insights: {e}")
            return ["An error occurred while processing the data."]