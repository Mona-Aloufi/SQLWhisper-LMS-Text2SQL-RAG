"""
Developer utilities for inspecting and debugging database content.
Run with: python -m src.utils.debug_tools
"""
import pandas as pd
from connection import get_connection

def show_feedback():
    """Display all SQL feedback entries for debugging."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM sql_feedback ORDER BY created_at DESC", conn)
    print(df)
    conn.close()
