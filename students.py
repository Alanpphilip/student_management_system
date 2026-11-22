"""
=============================================================================
Student Management System - students.py
Student registration, viewing, updating, searching, and safe deletion.
=============================================================================
"""

import sqlite3
import re
from datetime import datetime
from typing import Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# Validation & ID Generation Helpers
# ---------------------------------------------------------------------------

def validate_date(date_string: str) -> bool:
    """Validate if a string matches the YYYY-MM-DD date format."""
    try:
        datetime.strptime(date_string.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_email(email: str) -> bool:
    """Validate email format using standard regular expression."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email.strip()))


def validate_phone(phone: str) -> bool:
    """Validate that phone number contains 10 to 15 digits or valid characters."""
    cleaned = re.sub(r"[\s\-\(\)\+]", "", phone)
    return cleaned.isdigit() and (7 <= len(cleaned) <= 15)


def generate_student_id(conn: sqlite3.Connection) -> str:
    """
    Generate a new unique Student ID in sequence (e.g., STU1001, STU1002).
    Finds the maximum existing numeric suffix in the database and increments it.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT student_id FROM students WHERE student_id LIKE 'STU%'")
    rows = cursor.fetchall()

    max_num = 1000
    for row in rows:
        sid = row["student_id"]
        digits = sid[3:]
        if digits.isdigit():
            val = int(digits)
            if val > max_num:
                max_num = val

    return f"STU{max_num + 1}"


# ---------------------------------------------------------------------------
# Database Operations
# ---------------------------------------------------------------------------

def add_student(
    conn: sqlite3.Connection,
    student_id: str,
    name: str,
    dob: str,
    gender: str,
    email: str,
    phone: str,
    address: str,
    department: str,
    admission_date: str
) -> tuple[bool, str]:
    """
    Insert a new student record into the database.
    Returns (success_status, message).
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO students (
                student_id, name, dob, gender, email, phone, address, department, admission_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (student_id.strip(), name.strip(), dob.strip(), gender.strip(),
             email.strip().lower(), phone.strip(), address.strip(),
             department.strip(), admission_date.strip())
        )
        conn.commit()
        return True, f"Student {name} registered successfully with ID {student_id}."
    except sqlite3.IntegrityError as e:
        error_msg = str(e)
        if "UNIQUE constraint failed: students.email" in error_msg:
            return False, f"Error: A student with email '{email}' already exists."
        elif "UNIQUE constraint failed: students.student_id" in error_msg:
            return False, f"Error: Student ID '{student_id}' already exists."
        return False, f"Database Integrity Error: {error_msg}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def get_all_students(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    """Retrieve all student records ordered by Student ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students ORDER BY student_id ASC")
    return cursor.fetchall()


def get_student_by_id(conn: sqlite3.Connection, student_id: str) -> Optional[sqlite3.Row]:
    """Retrieve a single student record by Student ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id.strip(),))
    return cursor.fetchone()


def search_students(conn: sqlite3.Connection, query: str, search_by: str = "all") -> List[sqlite3.Row]:
    """
    Search students based on ID, Name, Department, or across all three fields.
    Uses parameterized LIKE queries.
    """
    cursor = conn.cursor()
    term = f"%{query.strip()}%"

    if search_by.lower() == "id":
        cursor.execute("SELECT * FROM students WHERE student_id LIKE ? ORDER BY student_id", (term,))
    elif search_by.lower() == "name":
        cursor.execute("SELECT * FROM students WHERE name LIKE ? ORDER BY name", (term,))
    elif search_by.lower() == "department":
        cursor.execute("SELECT * FROM students WHERE department LIKE ? ORDER BY department", (term,))
    else:
        cursor.execute(
            """
            SELECT * FROM students 
            WHERE student_id LIKE ? OR name LIKE ? OR department LIKE ?
            ORDER BY student_id
            """,
            (term, term, term)
        )
    return cursor.fetchall()


def update_student(
    conn: sqlite3.Connection,
    student_id: str,
    name: Optional[str] = None,
    dob: Optional[str] = None,
    gender: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    department: Optional[str] = None,
    admission_date: Optional[str] = None
) -> tuple[bool, str]:
    """
    Update student information for the specified Student ID.
    Only updates fields that are provided (not None).
    """
    existing = get_student_by_id(conn, student_id)
    if not existing:
        return False, f"Student with ID '{student_id}' does not exist."

    # Use existing values if new values are not provided
    updated_name = name.strip() if name is not None and name.strip() else existing["name"]
    updated_dob = dob.strip() if dob is not None and dob.strip() else existing["dob"]
    updated_gender = gender.strip() if gender is not None and gender.strip() else existing["gender"]
    updated_email = email.strip().lower() if email is not None and email.strip() else existing["email"]
    updated_phone = phone.strip() if phone is not None and phone.strip() else existing["phone"]
    updated_address = address.strip() if address is not None and address.strip() else existing["address"]
    updated_dept = department.strip() if department is not None and department.strip() else existing["department"]
    updated_adm_date = admission_date.strip() if admission_date is not None and admission_date.strip() else existing["admission_date"]

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE students SET
                name = ?, dob = ?, gender = ?, email = ?, phone = ?,
                address = ?, department = ?, admission_date = ?
            WHERE student_id = ?
            """,
            (updated_name, updated_dob, updated_gender, updated_email,
             updated_phone, updated_address, updated_dept, updated_adm_date, student_id.strip())
        )
        conn.commit()
        return True, f"Student record for ID '{student_id}' updated successfully."
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed: students.email" in str(e):
            return False, f"Error: The email '{updated_email}' is already in use by another student."
        return False, f"Database error: {str(e)}"


def delete_student(conn: sqlite3.Connection, student_id: str) -> tuple[bool, str]:
    """
    Safely delete a student record by ID.
    Foreign key ON DELETE CASCADE will clean up enrollments, attendance, and marks.
    """
    cursor = conn.cursor()
    student = get_student_by_id(conn, student_id)
    if not student:
        return False, f"Student with ID '{student_id}' not found."

    try:
        cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id.strip(),))
        conn.commit()
        return True, f"Student '{student['name']}' ({student_id}) and all associated records deleted successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Failed to delete student: {str(e)}"


# ---------------------------------------------------------------------------
# CLI Formatting and Menu Handlers
# ---------------------------------------------------------------------------

def display_students_table(students: List[sqlite3.Row]) -> None:
    """Format and print a list of student records in a structured table."""
    if not students:
        print("\n[!] No student records found.")
        return

    print("\n" + "=" * 115)
    print(f"{'ID':<10} | {'Name':<22} | {'Gender':<8} | {'Department':<20} | {'Phone':<14} | {'Email':<28}")
    print("-" * 115)
    for s in students:
        print(f"{s['student_id']:<10} | {s['name']:<22} | {s['gender']:<8} | {s['department']:<20} | {s['phone']:<14} | {s['email']:<28}")
    print("=" * 115)
    print(f"Total Records: {len(students)}\n")


def add_student_cli(conn: sqlite3.Connection) -> None:
    """CLI prompt for registering a new student."""
    print("\n" + "=" * 50)
    print("           REGISTER NEW STUDENT")
    print("=" * 50)

    auto_id = generate_student_id(conn)
    print(f"Auto-generated Student ID: {auto_id}")
    custom_choice = input(f"Press Enter to use [{auto_id}] or type a custom ID: ").strip()
    student_id = custom_choice if custom_choice else auto_id

    # Check if ID exists
    if get_student_by_id(conn, student_id):
        print(f"[x] Error: Student ID '{student_id}' is already registered.")
        return

    # Name
    while True:
        name = input("Enter Full Name: ").strip()
        if name:
            break
        print("[!] Student name cannot be empty.")

    # Date of Birth
    while True:
        dob = input("Enter Date of Birth (YYYY-MM-DD): ").strip()
        if validate_date(dob):
            break
        print("[!] Invalid date format. Please use YYYY-MM-DD (e.g., 2004-05-15).")

    # Gender
    while True:
        gender_input = input("Enter Gender (Male/Female/Other): ").strip()
        gender = gender_input.capitalize()
        if gender in ["Male", "Female", "Other"]:
            break
        print("[!] Please enter 'Male', 'Female', or 'Other'.")

    # Email
    while True:
        email = input("Enter Email Address: ").strip()
        if validate_email(email):
            break
        print("[!] Invalid email format (e.g., student@example.com).")

    # Phone
    while True:
        phone = input("Enter Phone Number: ").strip()
        if validate_phone(phone):
            break
        print("[!] Invalid phone number (must be 7-15 digits).")

    # Address
    while True:
        address = input("Enter Residential Address: ").strip()
        if address:
            break
        print("[!] Address cannot be empty.")

    # Department
    while True:
        department = input("Enter Department (e.g., Computer Science): ").strip()
        if department:
            break
        print("[!] Department cannot be empty.")

    # Admission Date
    today_str = datetime.now().strftime("%Y-%m-%d")
    adm_input = input(f"Enter Admission Date (YYYY-MM-DD) [Default: {today_str}]: ").strip()
    admission_date = adm_input if adm_input else today_str
    if not validate_date(admission_date):
        print("[!] Invalid admission date format. Using today's date instead.")
        admission_date = today_str

    success, msg = add_student(
        conn, student_id, name, dob, gender, email, phone, address, department, admission_date
    )
    if success:
        print(f"\n[+] {msg}")
    else:
        print(f"\n[x] {msg}")


def view_all_students_cli(conn: sqlite3.Connection) -> None:
    """CLI handler to display all students."""
    print("\n" + "=" * 50)
    print("             ALL REGISTERED STUDENTS")
    print("=" * 50)
    students = get_all_students(conn)
    display_students_table(students)


def search_student_cli(conn: sqlite3.Connection) -> None:
    """CLI handler to search students by ID, Name, or Department."""
    print("\n" + "=" * 50)
    print("               SEARCH STUDENTS")
    print("=" * 50)
    print("1. Search by Student ID")
    print("2. Search by Name")
    print("3. Search by Department")
    print("4. Search Across All Fields")
    print("-" * 50)

    choice = input("Enter your search option (1-4): ").strip()
    field_map = {"1": "id", "2": "name", "3": "department", "4": "all"}

    if choice not in field_map:
        print("[!] Invalid choice. Returning to main menu.")
        return

    query = input("Enter search keyword: ").strip()
    if not query:
        print("[!] Search query cannot be empty.")
        return

    results = search_students(conn, query, field_map[choice])
    print(f"\nSearch results for '{query}':")
    display_students_table(results)


def update_student_cli(conn: sqlite3.Connection) -> None:
    """CLI handler for updating an existing student's information."""
    print("\n" + "=" * 50)
    print("            UPDATE STUDENT DETAILS")
    print("=" * 50)

    student_id = input("Enter Student ID to update (e.g., STU1001): ").strip()
    student = get_student_by_id(conn, student_id)

    if not student:
        print(f"[x] Error: No student found with ID '{student_id}'.")
        return

    print("\nCurrent Information:")
    print(f"  Name           : {student['name']}")
    print(f"  Date of Birth  : {student['dob']}")
    print(f"  Gender         : {student['gender']}")
    print(f"  Email          : {student['email']}")
    print(f"  Phone          : {student['phone']}")
    print(f"  Address        : {student['address']}")
    print(f"  Department     : {student['department']}")
    print(f"  Admission Date : {student['admission_date']}")
    print("\nInstructions: Enter new value, or press Enter to keep existing value.\n")

    name = input(f"New Name [{student['name']}]: ").strip() or None

    while True:
        dob_in = input(f"New DOB [{student['dob']}]: ").strip()
        if not dob_in:
            dob = None
            break
        if validate_date(dob_in):
            dob = dob_in
            break
        print("[!] Invalid date format (YYYY-MM-DD).")

    while True:
        gender_in = input(f"New Gender [{student['gender']}]: ").strip()
        if not gender_in:
            gender = None
            break
        if gender_in.capitalize() in ["Male", "Female", "Other"]:
            gender = gender_in.capitalize()
            break
        print("[!] Enter 'Male', 'Female', or 'Other'.")

    while True:
        email_in = input(f"New Email [{student['email']}]: ").strip()
        if not email_in:
            email = None
            break
        if validate_email(email_in):
            email = email_in
            break
        print("[!] Invalid email format.")

    while True:
        phone_in = input(f"New Phone [{student['phone']}]: ").strip()
        if not phone_in:
            phone = None
            break
        if validate_phone(phone_in):
            phone = phone_in
            break
        print("[!] Invalid phone format (7-15 digits).")

    address = input(f"New Address [{student['address']}]: ").strip() or None
    department = input(f"New Department [{student['department']}]: ").strip() or None

    while True:
        adm_in = input(f"New Admission Date [{student['admission_date']}]: ").strip()
        if not adm_in:
            admission_date = None
            break
        if validate_date(adm_in):
            admission_date = adm_in
            break
        print("[!] Invalid date format (YYYY-MM-DD).")

    success, msg = update_student(
        conn, student_id, name, dob, gender, email, phone, address, department, admission_date
    )
    if success:
        print(f"\n[+] {msg}")
    else:
        print(f"\n[x] {msg}")


def delete_student_cli(conn: sqlite3.Connection) -> None:
    """CLI handler for safely deleting a student record."""
    print("\n" + "=" * 50)
    print("             DELETE STUDENT RECORD")
    print("=" * 50)

    student_id = input("Enter Student ID to delete (e.g., STU1001): ").strip()
    student = get_student_by_id(conn, student_id)

    if not student:
        print(f"[x] Error: No student found with ID '{student_id}'.")
        return

    print("\nRecord to be deleted:")
    print(f"  ID         : {student['student_id']}")
    print(f"  Name       : {student['name']}")
    print(f"  Department : {student['department']}")
    print(f"  Email      : {student['email']}")
    print("\n[!] WARNING: Deleting this student will also remove all their enrollments, attendance, and marks records!")
    confirm = input("Are you absolutely sure you want to delete this student? (yes/no): ").strip().lower()

    if confirm in ["yes", "y"]:
        success, msg = delete_student(conn, student_id)
        if success:
            print(f"\n[+] {msg}")
        else:
            print(f"\n[x] {msg}")
    else:
        print("\n[*] Deletion cancelled by user.")
