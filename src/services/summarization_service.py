# src/services/summarization_service.py
import logging
import re
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv
from .model_handler import ModelHandler

load_dotenv()

logger = logging.getLogger(__name__)


class ResultSummarizationService:
    def __init__(self, model_name=None, device=None):
        """
        Enhanced summarization service using LLM for natural language generation.
        Uses the same ModelHandler pattern as text2sql_service for consistency.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Enhanced Summarization Service")
        
        # Use a model optimized for text generation/summarization
        # Default to a model that's good at natural language generation
        self.summary_model_name = model_name or os.getenv(
            "SUMMARY_MODEL_NAME", 
            "google/flan-t5-base"  # Can use same model or a different one
        )
        
        # Initialize model handler for summarization
        self.model_handler = ModelHandler(
            model_name=self.summary_model_name,
            device=device
        )
        
        self.logger.info("✅ ResultSummarizationService initialized")
    
    def generate_summary(
        self, 
        question: str, 
        results: List[Dict], 
        sql_query: str,
        max_rows: int = 20
    ) -> Dict[str, Any]:
        """
        Generate natural language summary using LLM.
        
        Args:
            question: Original user question
            results: Query results as list of dictionaries
            sql_query: The SQL query that generated the results
            max_rows: Maximum number of rows to include in summary (default: 20)
        
        Returns:
            Dict with summary, success status, and metadata
        """
        # Validate and normalize results format
        if not results:
            return {
                "summary": "No data was found matching your criteria.",
                "success": True,
                "row_count": 0,
                "summary_type": "empty_result"
            }
        
        # Ensure results are dictionaries
        normalized_results = []
        for i, result in enumerate(results):
            if isinstance(result, dict):
                normalized_results.append(result)
            elif isinstance(result, (list, tuple)):
                # Convert tuple/list to dict (shouldn't happen but handle it)
                self.logger.warning(f"Result {i} is not a dict, converting from tuple/list")
                normalized_results.append({f"col_{j}": val for j, val in enumerate(result)})
            else:
                self.logger.warning(f"Result {i} has unexpected type {type(result)}, skipping")
        
        if not normalized_results:
            return {
                "summary": "No valid data was found to summarize.",
                "success": False,
                "row_count": 0,
                "summary_type": "invalid_format"
            }
        
        results = normalized_results
        self.logger.info(f"Generating summary for {len(results)} results, question: {question[:50]}...")
        
        try:
            # Format data for LLM
            formatted_data = self._format_results_for_llm(results, max_rows)
            
            # Build enhanced prompt for natural language generation
            prompt = self._build_summary_prompt(question, formatted_data, sql_query, len(results))
            
            # Generate summary using LLM
            generation_result = self.model_handler.generate_with_confidence(
                prompt, 
                max_new_tokens=200  # Allow longer summaries
            )
            
            if generation_result.get('error'):
                # Fallback to simple summary
                return self._generate_fallback_summary(results, question)
            
            # Extract and clean the summary
            raw_summary = generation_result.get('generated_text', '').strip()
            
            # Log raw output for debugging
            self.logger.info(f"Raw summary output (length: {len(raw_summary)}): {raw_summary[:200]}...")
            
            if not raw_summary:
                self.logger.warning("Model returned empty summary, using fallback")
                return self._generate_fallback_summary(results, question)
            
            summary = self._extract_summary_from_response(raw_summary)
            
            # If extraction failed or summary is too short, use the raw output
            if not summary or len(summary.strip()) < 10:
                self.logger.info("Extraction returned short/empty summary, using raw output")
                summary = raw_summary.strip()
                # Try to clean it
                summary = self._clean_summary(summary)
                
                # If still empty after cleaning, use fallback
                if not summary or len(summary.strip()) < 10:
                    self.logger.warning("Cleaned summary still empty, using fallback")
                    return self._generate_fallback_summary(results, question)
            
            return {
                "summary": summary,
                "success": True,
                "row_count": len(results),
                "summary_type": "llm_generated",
                "confidence": generation_result.get('confidence', 0.0),
                "raw_output": raw_summary
            }
            
        except Exception as e:
            self.logger.error(f"Error in LLM summarization: {e}")
            # Fallback to basic summary
            return self._generate_fallback_summary(results, question)
    
    def _format_results_for_llm(self, results: List[Dict], max_rows: int) -> str:
        """
        Format query results in a way that's easy for LLM to understand.
        """
        if not results:
            return "No data available."
        
        # Limit rows for prompt size
        rows_to_show = results[:max_rows]
        
        # Get column names
        columns = list(results[0].keys())
        
        # Build formatted table
        lines = []
        
        # Header
        header = " | ".join(columns)
        lines.append(f"Columns: {header}")
        lines.append("")
        lines.append("Data:")
        
        # Data rows
        for i, row in enumerate(rows_to_show, 1):
            values = [str(row.get(col, "")) for col in columns]
            row_text = " | ".join(values)
            lines.append(f"Row {i}: {row_text}")
        
        # Add summary if more rows exist
        if len(results) > max_rows:
            lines.append("")
            lines.append(f"... and {len(results) - max_rows} more rows (total: {len(results)} rows)")
        
        return "\n".join(lines)
    
    def _build_summary_prompt(
        self, 
        question: str, 
        formatted_data: str, 
        sql_query: str,
        total_rows: int
    ) -> str:
        """
        Build a prompt that guides the LLM to generate natural language summary.
        Optimized for FLAN-T5 and other instruction-following models.
        """
        # Check if using FLAN-T5 (better prompt format for instruction models)
        is_flan = 'flan' in self.summary_model_name.lower() or 't5' in self.summary_model_name.lower()
        
        if is_flan:
            # FLAN-T5 works better with direct instruction format
            return f"""Summarize the following database query results in natural language.

Question: {question}

Results ({total_rows} rows):
{formatted_data}

Summary:"""
        else:
            # For other models, use more detailed instructions
            return f"""Convert the following SQL query results into a clear, natural language summary.

Original Question: {question}

SQL Query Used: {sql_query}

Query Results ({total_rows} rows):
{formatted_data}

Instructions:
- Write a natural, conversational summary in plain English
- Focus on the key findings and insights from the data
- Use numbers and specific values from the results
- Keep it concise but informative (2-4 sentences)
- Write as if explaining to a colleague
- Do NOT repeat the SQL query or technical details
- Do NOT use phrases like "The query returned" or "The data shows"
- Start directly with the findings

Natural Language Summary:"""
    
    def _extract_summary_from_response(self, response: str) -> str:
        """
        Extract the summary from LLM response, removing any extra text.
        """
        if not response:
            return ""
        
        # Remove the prompt if it was echoed
        # Look for common patterns that indicate start of summary
        summary_markers = [
            r'Natural Language Summary:\s*(.*)',
            r'Summary:\s*(.*)',
            r'Answer:\s*(.*)',
        ]
        
        for pattern in summary_markers:
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                summary = match.group(1).strip()
                # Remove any trailing instruction text
                summary = re.sub(r'\n.*?(Instructions|SQL|Query).*$', '', summary, flags=re.IGNORECASE | re.DOTALL)
                return summary
        
        # If no marker found, use the response directly but clean it
        summary = response.strip()
        
        # Remove prompt-like text that might be at the start
        # Remove lines that look like data rows (Row 1:, Row 2:, etc.)
        lines = summary.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                continue
            
            # Skip instruction-like lines
            if any(keyword in line_stripped.lower() for keyword in [
                'instructions:', 'sql query', 'original question', 
                'query results', 'columns:', 'data:'
            ]):
                continue
            
            # Skip lines that look like data rows (Row X: pattern)
            if re.match(r'^Row\s+\d+:', line_stripped, re.IGNORECASE):
                continue
            
            # Skip lines that are just row numbers or data patterns
            if re.match(r'^\d+:\s*\d+', line_stripped):  # Pattern like "1: 2" or "Row 1: 2"
                continue
            
            cleaned_lines.append(line)
        
        summary = '\n'.join(cleaned_lines).strip()
        
        # Clean up
        summary = self._clean_summary(summary)
        
        return summary
    
    def _clean_summary(self, summary: str) -> str:
        """
        Clean and format the summary text.
        """
        if not summary:
            return ""
        
        # Remove markdown formatting
        summary = re.sub(r'```.*?```', '', summary, flags=re.DOTALL)
        summary = re.sub(r'`', '', summary)
        
        # Remove row number patterns that might have leaked through
        # Pattern: "Row 1:", "Row 2:", etc.
        summary = re.sub(r'Row\s+\d+:\s*', '', summary, flags=re.IGNORECASE)
        
        # Remove patterns like "1: value" or "2: value"
        summary = re.sub(r'^\d+:\s*', '', summary, flags=re.MULTILINE)
        
        # Remove extra whitespace but preserve sentence structure
        summary = re.sub(r'\s+', ' ', summary)
        summary = summary.strip()
        
        # Remove any remaining data-like patterns
        # Remove lines that are just numbers or product names repeated
        lines = summary.split('.')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip lines that are mostly numbers or look like data
            if line and not re.match(r'^[\d\s,]+$', line):  # Not just numbers and commas
                # Skip if it's a repetitive pattern
                words = line.split()
                if len(set(words)) < len(words) * 0.3:  # Too repetitive
                    continue
                cleaned_lines.append(line)
        
        summary = '. '.join(cleaned_lines).strip()
        
        # Ensure it ends with proper punctuation
        if summary and not summary[-1] in '.!?':
            summary += '.'
        
        # Capitalize first letter
        if summary:
            summary = summary[0].upper() + summary[1:] if len(summary) > 1 else summary.upper()
        
        return summary
    
    def _generate_fallback_summary(self, results: List[Dict], question: str) -> Dict[str, Any]:
        """
        Generate a simple fallback summary when LLM fails.
        """
        row_count = len(results)
        
        if row_count == 0:
            summary = "No data was found matching your criteria."
        elif row_count == 1:
            summary = f"Found 1 result matching your query."
        else:
            # Try to extract some key information
            columns = list(results[0].keys()) if results else []
            if columns:
                summary = f"Found {row_count} results with {len(columns)} columns: {', '.join(columns[:3])}"
                if len(columns) > 3:
                    summary += f" and {len(columns) - 3} more."
            else:
                summary = f"Found {row_count} results."
        
        return {
            "summary": summary,
            "success": True,
            "row_count": row_count,
            "summary_type": "fallback"
        }
    
    def _extract_selected_columns(self, sql: str, all_columns: List[str]) -> List[str]:
        """Extract selected columns from SQL SELECT clause."""
        try:
            select_match = re.search(r"SELECT\s+(.*?)\s+FROM", sql, re.IGNORECASE | re.DOTALL)
            if not select_match:
                return all_columns

            select_part = select_match.group(1).strip()
            if select_part == "*" or "all" in select_part.lower():
                return all_columns

            # Split and clean column names
            cols = []
            for col in re.split(r",\s*", select_part):
                # Remove aliases (e.g., "name AS customer_name" → "name")
                base_col = col.split()[0].strip()
                # Remove function wrappers (e.g., "COUNT(*)", "AVG(price)")
                if "(" in base_col:
                    # Try to extract inner column if exists
                    inner = re.search(r'\((.*?)\)', base_col)
                    if inner and inner.group(1) and inner.group(1) != "*":
                        candidate = inner.group(1).strip()
                        if candidate in all_columns:
                            cols.append(candidate)
                    else:
                        cols.append(base_col)
                else:
                    if base_col in all_columns:
                        cols.append(base_col)
                    else:
                        cols.append(base_col)
            return cols if cols else all_columns

        except Exception as e:
            self.logger.warning(f"Column extraction failed: {e}")
            return all_columns

    def quick_insights(self, results: List[Dict], question: str) -> List[str]:
        """
        Generate quick insights from results.
        Returns a list of insight strings.
        """
        if not results:
            return ["No records were found matching your criteria."]
        
        try:
            # Generate summary
            summary_result = self.generate_summary(
                question=question,
                results=results,
                sql_query="",  # Not needed for quick insights
                max_rows=10
            )
            
            if summary_result.get("success"):
                # Return as list
                summary = summary_result.get("summary", "")
                # Split into multiple insights if it's long
                if len(summary) > 200:
                    # Try to split by sentences
                    sentences = re.split(r'[.!?]+', summary)
                    insights = [s.strip() + '.' for s in sentences if s.strip()]
                    return insights[:3]  # Max 3 insights
                else:
                    return [summary]
            else:
                return ["Unable to generate insights."]
                
        except Exception as e:
            self.logger.error(f"Quick insights error: {e}")
            return ["An error occurred while generating insights."]
    
    def generate_detailed_analysis(
        self,
        question: str,
        results: List[Dict],
        sql_query: str
    ) -> Dict[str, Any]:
        """
        Generate a more detailed analysis with insights and patterns.
        """
        if not results:
            return {
                "analysis": "No data available for analysis.",
                "insights": [],
                "success": False
            }
        
        try:
            # Generate basic summary
            summary_result = self.generate_summary(question, results, sql_query, max_rows=50)
            
            # Generate additional insights
            insights = self._generate_insights(results, question)
            
            return {
                "summary": summary_result.get("summary", ""),
                "insights": insights,
                "row_count": len(results),
                "success": True,
                "analysis_type": "detailed"
            }
            
        except Exception as e:
            self.logger.error(f"Detailed analysis error: {e}")
            return {
                "analysis": f"Error generating analysis: {str(e)}",
                "insights": [],
                "success": False
            }
    
    def _generate_insights(self, results: List[Dict], question: str) -> List[str]:
        """
        Generate specific insights from the data.
        """
        insights = []
        
        if not results:
            return insights
        
        row_count = len(results)
        columns = list(results[0].keys()) if results else []
        
        # Basic insights
        if row_count > 0:
            insights.append(f"Found {row_count} result{'s' if row_count != 1 else ''}.")
        
        # Try to identify patterns
        # This is a simple heuristic - could be enhanced with LLM
        if row_count > 10:
            insights.append(f"Large result set with {row_count} records.")
        
        # Check for numeric columns that might have interesting stats
        numeric_columns = []
        for col in columns:
            if results:
                sample_value = results[0].get(col)
                if isinstance(sample_value, (int, float)):
                    numeric_columns.append(col)
        
        if numeric_columns:
            insights.append(f"Data includes numeric fields: {', '.join(numeric_columns[:3])}.")
        
        return insights
