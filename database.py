"""
=============================================================================
Student Management System - database.py
Database connection, table creation, and sample data population.
=============================================================================
"""

import sqlite3
import hashlib
import secrets
from typing import Optional

# Default database filename
DEFAULT_DB_NAME = "student_management.db"


def get_connection(db_name: str = DEFAULT_DB_NAME) -> sqlite3.Connection:
    """
    Establish and return a connection to the SQLite database.
    Enforces foreign key constraint checks for every active connection.
    Sets row_factory to sqlite3.Row for convenient column-name access.
    """
    conn = sqlite3.connect(db_name)
    # Enable foreign key support in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    # Allow column access by name as well as index
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """
    Create the necessary SQLite tables if they do not already exist:
    - users: Admin credentials and authentication
    - students: Student personal and academic information
    - courses: Course details and credits
    - enrollments: Linking students to courses
    - attendance: Daily student attendance per course
    - marks: Student examination scores and grades
    """
    cursor = conn.cursor()

    # 1. Users Table (Admin authentication)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'admin',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Students Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        dob TEXT NOT NULL,
        gender TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        address TEXT NOT NULL,
        department TEXT NOT NULL,
        admission_date TEXT NOT NULL
    );
    """)

    # 3. Courses Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT UNIQUE NOT NULL,
        course_name TEXT NOT NULL,
        credits INTEGER NOT NULL CHECK(credits > 0),
        department TEXT NOT NULL
    );
    """)

    # 4. Enrollments Table (Many-to-Many relationship between Students & Courses)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        course_id INTEGER NOT NULL,
        enrollment_date TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
        UNIQUE (student_id, course_id)
    );
    """)

    # 5. Attendance Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        course_id INTEGER NOT NULL,
        attendance_date TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
        UNIQUE (student_id, course_id, attendance_date)
    );
    """)

    # 6. Marks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marks (
        mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        course_id INTEGER NOT NULL,
        exam_name TEXT NOT NULL,
        max_marks REAL NOT NULL CHECK(max_marks > 0),
        obtained_marks REAL NOT NULL CHECK(obtained_marks >= 0 AND obtained_marks <= max_marks),
        grade TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
        UNIQUE (student_id, course_id, exam_name)
    );
    """)

    conn.commit()


def hash_password_helper(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    Helper to hash a password using SHA-256 with a random salt.
    Returns (password_hash, salt).
    """
    if salt is None:
        salt = secrets.token_hex(16)
    combined = salt + password
    pwd_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return pwd_hash, salt


def insert_sample_data(conn: sqlite3.Connection) -> None:
    """
    Populate the database with default administrator account and sample
    data (students, courses, enrollments, attendance, and marks) if empty.
    """
    cursor = conn.cursor()

    # 1. Default Admin Account (Username: admin, Password: Admin@123)
    cursor.execute("SELECT COUNT(*) AS count FROM users WHERE username = 'admin'")
    if cursor.fetchone()["count"] == 0:
        pwd_hash, salt = hash_password_helper("Admin@123")
        cursor.execute(
            "INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)",
            ("admin", pwd_hash, salt, "admin")
        )

    # 2. Sample Courses
    cursor.execute("SELECT COUNT(*) AS count FROM courses")
    if cursor.fetchone()["count"] == 0:
        sample_courses = [
            ("CS101", "Introduction to Python Programming", 4, "Computer Science"),
            ("CS102", "Data Structures and Algorithms", 4, "Computer Science"),
            ("MA101", "Applied Discrete Mathematics", 3, "Mathematics"),
            ("EC101", "Digital Logic and Circuits", 3, "Electronics"),
            ("ENG101", "Professional Communication", 2, "Humanities")
        ]
        cursor.executemany(
            "INSERT INTO courses (course_code, course_name, credits, department) VALUES (?, ?, ?, ?)",
            sample_courses
        )

    # 3. Sample Students
    cursor.execute("SELECT COUNT(*) AS count FROM students")
    if cursor.fetchone()["count"] == 0:
        sample_students = [
            ("STU1001", "Alice Johnson", "2004-05-15", "Female", "alice.johnson@example.com", "9876543210", "123 Maple Street, Springfield", "Computer Science", "2024-08-01"),
            ("STU1002", "Bob Smith", "2003-11-20", "Male", "bob.smith@example.com", "9876543211", "456 Oak Avenue, Metropolis", "Computer Science", "2024-08-01"),
            ("STU1003", "Catherine Davis", "2004-02-10", "Female", "catherine.davis@example.com", "9876543212", "789 Pine Road, Gotham", "Electronics", "2024-08-01")
        ]
        cursor.executemany(
            "INSERT INTO students (student_id, name, dob, gender, email, phone, address, department, admission_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            sample_students
        )

    # 4. Sample Enrollments
    cursor.execute("SELECT COUNT(*) AS count FROM enrollments")
    if cursor.fetchone()["count"] == 0:
        # Fetch course IDs based on codes
        cursor.execute("SELECT course_id, course_code FROM courses")
        course_map = {row["course_code"]: row["course_id"] for row in cursor.fetchall()}

        sample_enrollments = [
            # Alice enrolled in CS101, CS102, MA101
            ("STU1001", course_map["CS101"], "2024-08-05"),
            ("STU1001", course_map["CS102"], "2024-08-05"),
            ("STU1001", course_map["MA101"], "2024-08-05"),
            # Bob enrolled in CS101, MA101
            ("STU1002", course_map["CS101"], "2024-08-05"),
            ("STU1002", course_map["MA101"], "2024-08-05"),
            # Catherine enrolled in EC101, MA101, ENG101
            ("STU1003", course_map["EC101"], "2024-08-05"),
            ("STU1003", course_map["MA101"], "2024-08-05"),
            ("STU1003", course_map["ENG101"], "2024-08-05")
        ]
        cursor.executemany(
            "INSERT INTO enrollments (student_id, course_id, enrollment_date) VALUES (?, ?, ?)",
            sample_enrollments
        )

    # 5. Sample Attendance
    cursor.execute("SELECT COUNT(*) AS count FROM attendance")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("SELECT course_id, course_code FROM courses")
        course_map = {row["course_code"]: row["course_id"] for row in cursor.fetchall()}

        sample_attendance = [
            # Alice CS101 attendance
            ("STU1001", course_map["CS101"], "2024-09-01", "Present"),
            ("STU1001", course_map["CS101"], "2024-09-02", "Present"),
            ("STU1001", course_map["CS101"], "2024-09-03", "Present"),
            ("STU1001", course_map["CS101"], "2024-09-04", "Absent"),
            ("STU1001", course_map["CS101"], "2024-09-05", "Present"),
            # Bob CS101 attendance
            ("STU1002", course_map["CS101"], "2024-09-01", "Present"),
            ("STU1002", course_map["CS101"], "2024-09-02", "Absent"),
            ("STU1002", course_map["CS101"], "2024-09-03", "Present"),
            ("STU1002", course_map["CS101"], "2024-09-04", "Absent"),
            ("STU1002", course_map["CS101"], "2024-09-05", "Present"),
            # Catherine EC101 attendance
            ("STU1003", course_map["EC101"], "2024-09-01", "Present"),
            ("STU1003", course_map["EC101"], "2024-09-02", "Present"),
            ("STU1003", course_map["EC101"], "2024-09-03", "Present"),
            ("STU1003", course_map["EC101"], "2024-09-04", "Present"),
            ("STU1003", course_map["EC101"], "2024-09-05", "Present")
        ]
        cursor.executemany(
            "INSERT INTO attendance (student_id, course_id, attendance_date, status) VALUES (?, ?, ?, ?)",
            sample_attendance
        )

    # 6. Sample Marks
    cursor.execute("SELECT COUNT(*) AS count FROM marks")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("SELECT course_id, course_code FROM courses")
        course_map = {row["course_code"]: row["course_id"] for row in cursor.fetchall()}

        sample_marks = [
            # Alice marks
            ("STU1001", course_map["CS101"], "Midterm Exam", 100.0, 92.0, "A+"),
            ("STU1001", course_map["CS102"], "Midterm Exam", 100.0, 85.0, "A"),
            ("STU1001", course_map["MA101"], "Midterm Exam", 100.0, 78.0, "B"),
            # Bob marks
            ("STU1002", course_map["CS101"], "Midterm Exam", 100.0, 68.0, "C"),
            ("STU1002", course_map["MA101"], "Midterm Exam", 100.0, 74.0, "B"),
            # Catherine marks
            ("STU1003", course_map["EC101"], "Midterm Exam", 100.0, 89.0, "A"),
            ("STU1003", course_map["MA101"], "Midterm Exam", 100.0, 94.0, "A+"),
            ("STU1003", course_map["ENG101"], "Midterm Exam", 50.0, 45.0, "A+")
        ]
        cursor.executemany(
            "INSERT INTO marks (student_id, course_id, exam_name, max_marks, obtained_marks, grade) VALUES (?, ?, ?, ?, ?, ?)",
            sample_marks
        )

    conn.commit()


def initialize_database(db_name: str = DEFAULT_DB_NAME) -> None:
    """
    Connect to the database, build all required tables,
    and seed initial sample data.
    """
    conn = get_connection(db_name)
    try:
        create_tables(conn)
        insert_sample_data(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    print(f"Initializing database '{DEFAULT_DB_NAME}'...")
    initialize_database()
    print("Database initialization and sample data insertion completed successfully!")
