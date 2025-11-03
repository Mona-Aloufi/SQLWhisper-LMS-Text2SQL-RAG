import sqlite3

# Connect or create the database
conn = sqlite3.connect("streamlit_app/my_database.sqlite")
cur = conn.cursor()

# ------------------------
# Students Table
# ------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    name TEXT,
    score INTEGER
)
""")
cur.executemany("INSERT INTO students (name, score) VALUES (?, ?)", [
    ("Alice", 95),
    ("Bob", 88),
    ("Charlie", 92),
    ("Dina", 75),
    ("Ethan", 68),
    ("Fatima", 99)
])

# ------------------------
# Professors Table
# ------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS professors (
    id INTEGER PRIMARY KEY,
    name TEXT,
    department TEXT
)
""")
cur.executemany("INSERT INTO professors (name, department) VALUES (?, ?)", [
    ("Dr. Smith", "Mathematics"),
    ("Dr. Lee", "Physics"),
    ("Dr. Khan", "Chemistry"),
    ("Dr. Sara", "Biology"),
    ("Dr. Omar", "Computer Science")
])

# ------------------------
# Courses Table
# ------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY,
    name TEXT,
    professor_id INTEGER,
    FOREIGN KEY (professor_id) REFERENCES professors(id)
)
""")
cur.executemany("INSERT INTO courses (name, professor_id) VALUES (?, ?)", [
    ("Math", 1),
    ("Physics", 2),
    ("Chemistry", 3),
    ("Biology", 4),
    ("Computer Science", 5)
])

# ------------------------
# Enrollments Table
# ------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY,
    student_id INTEGER,
    course_id INTEGER,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
)
""")
cur.executemany("INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)", [
    (1, 1),
    (1, 5),
    (2, 2),
    (3, 3),
    (3, 1),
    (4, 4),
    (5, 2),
    (6, 5),
    (6, 3)
])

# ------------------------
# Grades Table
# ------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY,
    student_id INTEGER,
    course_id INTEGER,
    grade INTEGER,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
)
""")
cur.executemany("INSERT INTO grades (student_id, course_id, grade) VALUES (?, ?, ?)", [
    (1, 1, 98),
    (1, 5, 91),
    (2, 2, 85),
    (3, 3, 89),
    (3, 1, 90),
    (4, 4, 70),
    (5, 2, 76),
    (6, 5, 95),
    (6, 3, 93)
])

conn.commit()
conn.close()
print("✅ Demo database created successfully with 5 tables!")
