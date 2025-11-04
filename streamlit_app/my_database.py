#!/usr/bin/env python3
"""
Idempotent demo DB creator.
Creates data/my_database.sqlite and populates it only if tables are empty.
"""

import sqlite3
from pathlib import Path

# target DB file (inside repo data/)
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "my_database.sqlite"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def ensure_table_and_seed(cur, table_name: str, create_sql: str, seed_rows: list, insert_sql: str):
    # create table if not exists
    cur.execute(create_sql)
    # check if table has rows
    cur.execute(f"SELECT COUNT(1) as cnt FROM {table_name}")
    cnt = cur.fetchone()[0]
    if cnt == 0 and seed_rows:
        cur.executemany(insert_sql, seed_rows)
        print(f"  - seeded table '{table_name}' with {len(seed_rows)} rows")
    else:
        print(f"  - table '{table_name}' already has {cnt} rows (skipping seed)")

def main():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    print(f"Creating or opening DB at: {DB_PATH}")

    # Students
    students_create = """
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        name TEXT,
        score INTEGER
    )
    """
    students_rows = [
        ("Alice", 95),
        ("Bob", 88),
        ("Charlie", 92),
        ("Dina", 75),
        ("Ethan", 68),
        ("Fatima", 99)
    ]
    students_insert = "INSERT INTO students (name, score) VALUES (?, ?)"
    ensure_table_and_seed(cur, "students", students_create, students_rows, students_insert)

    # Professors
    professors_create = """
    CREATE TABLE IF NOT EXISTS professors (
        id INTEGER PRIMARY KEY,
        name TEXT,
        department TEXT
    )
    """
    professors_rows = [
        ("Dr. Smith", "Mathematics"),
        ("Dr. Lee", "Physics"),
        ("Dr. Khan", "Chemistry"),
        ("Dr. Sara", "Biology"),
        ("Dr. Omar", "Computer Science")
    ]
    professors_insert = "INSERT INTO professors (name, department) VALUES (?, ?)"
    ensure_table_and_seed(cur, "professors", professors_create, professors_rows, professors_insert)

    # Courses
    courses_create = """
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY,
        name TEXT,
        professor_id INTEGER,
        FOREIGN KEY (professor_id) REFERENCES professors(id)
    )
    """
    courses_rows = [
        ("Math", 1),
        ("Physics", 2),
        ("Chemistry", 3),
        ("Biology", 4),
        ("Computer Science", 5)
    ]
    courses_insert = "INSERT INTO courses (name, professor_id) VALUES (?, ?)"
    ensure_table_and_seed(cur, "courses", courses_create, courses_rows, courses_insert)

    # Enrollments
    enrollments_create = """
    CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY,
        student_id INTEGER,
        course_id INTEGER,
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (course_id) REFERENCES courses(id)
    )
    """
    enrollments_rows = [
        (1, 1),
        (1, 5),
        (2, 2),
        (3, 3),
        (3, 1),
        (4, 4),
        (5, 2),
        (6, 5),
        (6, 3)
    ]
    enrollments_insert = "INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)"
    ensure_table_and_seed(cur, "enrollments", enrollments_create, enrollments_rows, enrollments_insert)

    # Grades
    grades_create = """
    CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY,
        student_id INTEGER,
        course_id INTEGER,
        grade INTEGER,
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (course_id) REFERENCES courses(id)
    )
    """
    grades_rows = [
        (1, 1, 98),
        (1, 5, 91),
        (2, 2, 85),
        (3, 3, 89),
        (3, 1, 90),
        (4, 4, 70),
        (5, 2, 76),
        (6, 5, 95),
        (6, 3, 93)
    ]
    grades_insert = "INSERT INTO grades (student_id, course_id, grade) VALUES (?, ?, ?)"
    ensure_table_and_seed(cur, "grades", grades_create, grades_rows, grades_insert)
    
    sql_feedback_create = """
    CREATE TABLE IF NOT EXISTS sql_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,              -- User's natural-language question
        generated_sql TEXT NOT NULL,         -- Model-generated SQL
        user_correction TEXT,                -- User's corrected SQL (if any)
        verdict TEXT CHECK(verdict IN ('up', 'down')) NOT NULL,  -- 👍 or 👎
        comment TEXT,                        -- Optional explanation or note
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    cur.execute(sql_feedback_create)
    conn.commit()
    conn.close()
    print("✅ Demo database created/updated successfully at:", DB_PATH)

if __name__ == "__main__":
    main()
