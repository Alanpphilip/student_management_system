"""
=============================================================================
Student Management System - courses.py
Course management (Add, View, Update, Delete) and Student Enrollment.
=============================================================================
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# Database Operations - Course Management
# ---------------------------------------------------------------------------

def add_course(
    conn: sqlite3.Connection,
    course_code: str,
    course_name: str,
    credits: int,
    department: str
) -> tuple[bool, str]:
    """
    Add a new course to the courses table.
    Enforces uniqueness of course_code and positive credits.
    """
    code = course_code.strip().upper()
    name = course_name.strip()
    dept = department.strip()

    if not code or not name or not dept:
        return False, "Course code, course name, and department cannot be empty."

    if credits <= 0:
        return False, "Course credits must be a positive integer."

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO courses (course_code, course_name, credits, department)
            VALUES (?, ?, ?, ?)
            """,
            (code, name, credits, dept)
        )
        conn.commit()
        return True, f"Course '{code} - {name}' added successfully."
    except sqlite3.IntegrityError:
        return False, f"Error: Course code '{code}' already exists in the system."
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def get_all_courses(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    """Retrieve all courses ordered by course code."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses ORDER BY course_code ASC")
    return cursor.fetchall()


def get_course_by_id(conn: sqlite3.Connection, course_id: int) -> Optional[sqlite3.Row]:
    """Retrieve course details by its primary key ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    return cursor.fetchone()


def get_course_by_code(conn: sqlite3.Connection, course_code: str) -> Optional[sqlite3.Row]:
    """Retrieve course details by course code (e.g. CS101)."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE UPPER(course_code) = ?", (course_code.strip().upper(),))
    return cursor.fetchone()


def update_course(
    conn: sqlite3.Connection,
    course_id: int,
    course_code: Optional[str] = None,
    course_name: Optional[str] = None,
    credits: Optional[int] = None,
    department: Optional[str] = None
) -> tuple[bool, str]:
    """
    Update details of an existing course.
    Only updates provided non-empty fields.
    """
    existing = get_course_by_id(conn, course_id)
    if not existing:
        return False, f"Course with ID {course_id} does not exist."

    new_code = course_code.strip().upper() if course_code is not None and course_code.strip() else existing["course_code"]
    new_name = course_name.strip() if course_name is not None and course_name.strip() else existing["course_name"]
    new_credits = credits if credits is not None and credits > 0 else existing["credits"]
    new_dept = department.strip() if department is not None and department.strip() else existing["department"]

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE courses SET
                course_code = ?, course_name = ?, credits = ?, department = ?
            WHERE course_id = ?
            """,
            (new_code, new_name, new_credits, new_dept, course_id)
        )
        conn.commit()
        return True, f"Course ID {course_id} updated successfully."
    except sqlite3.IntegrityError:
        return False, f"Error: Course code '{new_code}' is already used by another course."
    except Exception as e:
        return False, f"Database error: {str(e)}"


def delete_course(conn: sqlite3.Connection, course_id: int) -> tuple[bool, str]:
    """
    Safely delete a course by ID.
    Cascades to delete related enrollments, attendance, and marks.
    """
    course = get_course_by_id(conn, course_id)
    if not course:
        return False, f"Course with ID {course_id} not found."

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM courses WHERE course_id = ?", (course_id,))
        conn.commit()
        return True, f"Course '{course['course_code']} - {course['course_name']}' deleted successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Failed to delete course: {str(e)}"


# ---------------------------------------------------------------------------
# Database Operations - Enrollment Management
# ---------------------------------------------------------------------------

def enroll_student(
    conn: sqlite3.Connection,
    student_id: str,
    course_id: int,
    enrollment_date: Optional[str] = None
) -> tuple[bool, str]:
    """
    Enroll a student into a specific course.
    Prevents duplicate enrollment using UNIQUE constraint.
    """
    if enrollment_date is None or not enrollment_date.strip():
        enrollment_date = datetime.now().strftime("%Y-%m-%d")

    cursor = conn.cursor()

    # Validate student existence
    cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id.strip(),))
    student_row = cursor.fetchone()
    if not student_row:
        return False, f"Student with ID '{student_id}' does not exist."

    # Validate course existence
    cursor.execute("SELECT course_code, course_name FROM courses WHERE course_id = ?", (course_id,))
    course_row = cursor.fetchone()
    if not course_row:
        return False, f"Course with ID {course_id} does not exist."

    try:
        cursor.execute(
            """
            INSERT INTO enrollments (student_id, course_id, enrollment_date)
            VALUES (?, ?, ?)
            """,
            (student_id.strip(), course_id, enrollment_date.strip())
        )
        conn.commit()
        return True, (
            f"Successfully enrolled {student_row['name']} ({student_id}) "
            f"in {course_row['course_code']} - {course_row['course_name']}."
        )
    except sqlite3.IntegrityError:
        return False, (
            f"Duplicate Enrollment: Student '{student_id}' is already enrolled "
            f"in course '{course_row['course_code']}'."
        )
    except Exception as e:
        return False, f"Enrollment failed: {str(e)}"


def get_student_courses(conn: sqlite3.Connection, student_id: str) -> List[sqlite3.Row]:
    """Retrieve all courses in which a student is currently enrolled."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT c.course_id, c.course_code, c.course_name, c.credits, c.department, e.enrollment_date
        FROM courses c
        JOIN enrollments e ON c.course_id = e.course_id
        WHERE e.student_id = ?
        ORDER BY c.course_code ASC
        """,
        (student_id.strip(),)
    )
    return cursor.fetchall()


def is_student_enrolled(conn: sqlite3.Connection, student_id: str, course_id: int) -> bool:
    """Check if a student is already enrolled in a specific course."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM enrollments WHERE student_id = ? AND course_id = ?",
        (student_id.strip(), course_id)
    )
    return cursor.fetchone() is not None


# ---------------------------------------------------------------------------
# CLI Formatting and Handlers
# ---------------------------------------------------------------------------

def display_courses_table(courses: List[sqlite3.Row]) -> None:
    """Format and print courses in a clean ASCII table."""
    if not courses:
        print("\n[!] No courses found in the database.")
        return

    print("\n" + "=" * 85)
    print(f"{'ID':<6} | {'Code':<10} | {'Course Name':<35} | {'Credits':<8} | {'Department':<20}")
    print("-" * 85)
    for c in courses:
        print(f"{c['course_id']:<6} | {c['course_code']:<10} | {c['course_name']:<35} | {c['credits']:<8} | {c['department']:<20}")
    print("=" * 85)
    print(f"Total Courses: {len(courses)}\n")


def add_course_cli(conn: sqlite3.Connection) -> None:
    """CLI prompt to add a new course."""
    print("\n" + "=" * 50)
    print("               ADD NEW COURSE")
    print("=" * 50)

    while True:
        code = input("Enter Course Code (e.g., CS103): ").strip().upper()
        if code:
            if get_course_by_code(conn, code):
                print(f"[x] Error: Course code '{code}' already exists.")
                continue
            break
        print("[!] Course code cannot be empty.")

    while True:
        name = input("Enter Course Name (e.g., Database Systems): ").strip()
        if name:
            break
        print("[!] Course name cannot be empty.")

    while True:
        credits_str = input("Enter Credits (1-6): ").strip()
        if credits_str.isdigit() and int(credits_str) > 0:
            credits = int(credits_str)
            break
        print("[!] Please enter a valid positive integer for credits.")

    while True:
        dept = input("Enter Department: ").strip()
        if dept:
            break
        print("[!] Department cannot be empty.")

    success, msg = add_course(conn, code, name, credits, dept)
    if success:
        print(f"\n[+] {msg}")
    else:
        print(f"\n[x] {msg}")


def view_all_courses_cli(conn: sqlite3.Connection) -> None:
    """CLI display of all courses."""
    print("\n" + "=" * 50)
    print("               ALL COURSES")
    print("=" * 50)
    courses = get_all_courses(conn)
    display_courses_table(courses)


def update_course_cli(conn: sqlite3.Connection) -> None:
    """CLI prompt to update an existing course."""
    print("\n" + "=" * 50)
    print("             UPDATE COURSE DETAILS")
    print("=" * 50)

    code_or_id = input("Enter Course ID or Course Code to update: ").strip()
    course = None
    if code_or_id.isdigit():
        course = get_course_by_id(conn, int(code_or_id))
    if not course:
        course = get_course_by_code(conn, code_or_id)

    if not course:
        print(f"[x] Error: Course '{code_or_id}' not found.")
        return

    print("\nCurrent Course Details:")
    print(f"  Course ID   : {course['course_id']}")
    print(f"  Code        : {course['course_code']}")
    print(f"  Name        : {course['course_name']}")
    print(f"  Credits     : {course['credits']}")
    print(f"  Department  : {course['department']}")
    print("\nPress Enter to retain existing values.\n")

    new_code = input(f"New Course Code [{course['course_code']}]: ").strip() or None
    new_name = input(f"New Course Name [{course['course_name']}]: ").strip() or None

    new_credits = None
    while True:
        c_in = input(f"New Credits [{course['credits']}]: ").strip()
        if not c_in:
            break
        if c_in.isdigit() and int(c_in) > 0:
            new_credits = int(c_in)
            break
        print("[!] Credits must be a positive integer.")

    new_dept = input(f"New Department [{course['department']}]: ").strip() or None

    success, msg = update_course(
        conn, course["course_id"], new_code, new_name, new_credits, new_dept
    )
    if success:
        print(f"\n[+] {msg}")
    else:
        print(f"\n[x] {msg}")


def delete_course_cli(conn: sqlite3.Connection) -> None:
    """CLI prompt to safely delete a course."""
    print("\n" + "=" * 50)
    print("              DELETE A COURSE")
    print("=" * 50)

    code_or_id = input("Enter Course ID or Course Code to delete: ").strip()
    course = None
    if code_or_id.isdigit():
        course = get_course_by_id(conn, int(code_or_id))
    if not course:
        course = get_course_by_code(conn, code_or_id)

    if not course:
        print(f"[x] Error: Course '{code_or_id}' not found.")
        return

    print("\nCourse to be deleted:")
    print(f"  ID   : {course['course_id']}")
    print(f"  Code : {course['course_code']}")
    print(f"  Name : {course['course_name']}")
    print("\n[!] WARNING: Deleting this course will also delete all student enrollments, attendance, and marks for it.")
    confirm = input("Are you sure you want to delete this course? (yes/no): ").strip().lower()

    if confirm in ["yes", "y"]:
        success, msg = delete_course(conn, course["course_id"])
        if success:
            print(f"\n[+] {msg}")
        else:
            print(f"\n[x] {msg}")
    else:
        print("\n[*] Course deletion cancelled.")


def manage_courses_menu(conn: sqlite3.Connection) -> None:
    """Sub-menu for Course Management."""
    while True:
        print("\n" + "=" * 50)
        print("           COURSE MANAGEMENT MENU")
        print("=" * 50)
        print("1. Add New Course")
        print("2. View All Courses")
        print("3. Update Course Details")
        print("4. Delete Course")
        print("5. Return to Main Menu")
        print("-" * 50)

        choice = input("Enter your choice (1-5): ").strip()
        if choice == "1":
            add_course_cli(conn)
        elif choice == "2":
            view_all_courses_cli(conn)
        elif choice == "3":
            update_course_cli(conn)
        elif choice == "4":
            delete_course_cli(conn)
        elif choice == "5":
            break
        else:
            print("[!] Invalid option. Please select 1 through 5.")


def enroll_student_cli(conn: sqlite3.Connection) -> None:
    """CLI handler for enrolling a student into a course."""
    print("\n" + "=" * 50)
    print("             ENROLL STUDENT IN COURSE")
    print("=" * 50)

    student_id = input("Enter Student ID (e.g., STU1001): ").strip()
    cursor = conn.cursor()
    cursor.execute("SELECT name, department FROM students WHERE student_id = ?", (student_id,))
    student = cursor.fetchone()

    if not student:
        print(f"[x] Error: No student found with ID '{student_id}'.")
        return

    print(f"Selected Student: {student['name']} ({student_id}) - Department: {student['department']}")

    # Show available courses
    courses = get_all_courses(conn)
    if not courses:
        print("[!] No courses available. Please add courses first.")
        return

    display_courses_table(courses)
    course_input = input("Enter Course ID or Course Code to enroll in: ").strip()

    course = None
    if course_input.isdigit():
        course = get_course_by_id(conn, int(course_input))
    if not course:
        course = get_course_by_code(conn, course_input)

    if not course:
        print(f"[x] Error: Course '{course_input}' not found.")
        return

    # Check duplicate enrollment before inserting
    if is_student_enrolled(conn, student_id, course["course_id"]):
        print(f"[x] Error: Student '{student_id}' is ALREADY enrolled in '{course['course_code']} - {course['course_name']}'.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    enroll_date = input(f"Enter Enrollment Date (YYYY-MM-DD) [Default: {today_str}]: ").strip()
    if not enroll_date:
        enroll_date = today_str

    success, msg = enroll_student(conn, student_id, course["course_id"], enroll_date)
    if success:
        print(f"\n[+] {msg}")
    else:
        print(f"\n[x] {msg}")
