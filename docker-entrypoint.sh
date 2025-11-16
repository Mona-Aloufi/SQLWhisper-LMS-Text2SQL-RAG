#!/bin/bash
# Docker entrypoint script for SQLWhisper

set -e

echo "🚀 Starting SQLWhisper..."

# Wait for backend to be ready (if running in separate containers)
if [ -n "$WAIT_FOR_BACKEND" ]; then
    echo "⏳ Waiting for backend to be ready..."
    until curl -f http://${BACKEND_HOST:-backend}:${BACKEND_PORT:-8000}/health > /dev/null 2>&1; do
        echo "   Backend not ready, waiting..."
        sleep 2
    done
    echo "✅ Backend is ready!"
fi

# Initialize feedback table if needed
python -c "
import sqlite3
import os
os.makedirs('data', exist_ok=True)
conn = sqlite3.connect('data/my_database.sqlite')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sql_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        generated_sql TEXT,
        verdict TEXT,
        comment TEXT,
        user_correction TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
conn.close()
print('✅ Feedback table initialized')
" || echo "⚠️  Could not initialize feedback table (may already exist)"

# Execute the main command
exec "$@"

