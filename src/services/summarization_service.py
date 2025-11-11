# src/services/summarization_service.py
import logging
import re
from typing import Dict, List, Any, Optional
import torch

logger = logging.getLogger(__name__)


class ResultSummarizationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing FLAN-T5 Summarization Service")
        self._summary_pipe = None

    @property
    def summary_pipe(self):
        """Lazy-load the summarization pipeline on first use."""
        if self._summary_pipe is None:
            self.logger.info("Loading FLAN-T5 summarization model...")
            try:
                from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
                model_name = "google/flan-t5-base"
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                device = 0 if torch.cuda.is_available() else -1
                self._summary_pipe = pipeline(
                    "text2text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    device=device,
                    max_new_tokens=60,
                    do_sample=False,
                    temperature=0.0,
                )
                self.logger.info("✅ FLAN-T5 model loaded successfully")
            except Exception as e:
                self.logger.error(f"Failed to load FLAN-T5: {e}")
                self._summary_pipe = None
        return self._summary_pipe

    def generate_summary(self, question: str, results: List[Dict], sql_query: str) -> Dict[str, Any]:
        """
        Generate natural language summary using FLAN-T5.
        """
        if not results:
            return {
                "summary": "No data was found matching your criteria.",
                "success": True,
                "row_count": 0
            }

        try:
            # Extract columns from first row
            cols = list(results[0].keys())
            rows = [list(row.values()) for row in results]

            # Reconstruct selected columns from SQL (best effort)
            selected_cols = self._extract_selected_columns(sql_query, cols)

            # Build table text
            header = " | ".join(selected_cols)
            data_lines = []
            for row in rows[:10]:  # limit to 10 rows
                filtered_row = [str(row[cols.index(c)]) for c in selected_cols if c in cols]
                data_lines.append(" | ".join(filtered_row))
            table_text = "\n".join(data_lines) if data_lines else "No results found."

            # Build prompt
            prompt = (
                f"User asked: {question}\n\n"
                f"Table columns shown: {header}\n"
                f"Data:\n{table_text}\n\n"
                f"Write one short factual summary of this data in plain English. "
                f"Do not repeat the SQL query, and only mention information visible above."
            )

            # Generate summary
            if self.summary_pipe:
                summary = self.summary_pipe(prompt)[0]["generated_text"].strip()
            else:
                # Fallback to simple summary
                summary = f"The query returned {len(results)} records."

            return {
                "summary": summary,
                "success": True,
                "row_count": len(results)
            }

        except Exception as e:
            self.logger.error(f"Error in FLAN-T5 summarization: {e}")
            # Fallback to basic summary
            return {
                "summary": f"Query returned {len(results)} records.",
                "success": True,
                "row_count": len(results)
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
                    inner = re.search(r"$$(.*?)$$", base_col)
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
        """Generate exactly one natural language insight using FLAN-T5."""
        if not results:
            return ["No records were found matching your criteria."]
        
        try:
            # Reuse generate_summary logic but return as a list
            summary_result = self.generate_summary(
            question=question,
            results=results,
            sql_query="" )
            return [summary_result["summary"]] if summary_result["success"] else ["Unable to generate insight."]

        except Exception as e:
            self.logger.error(f"Quick insights error: {e}")
            return ["An error occurred while generating the summary."]