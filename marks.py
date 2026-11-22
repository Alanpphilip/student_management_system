"""
=============================================================================
Student Management System - marks.py
Entering marks, validating scores, calculating percentages, and grading.
=============================================================================
"""

import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from courses import get_course_by_id, get_course_by_code, is_student_enrolled, get_student_courses
from students import get_student_by_id


# ---------------------------------------------------------------------------
# Grading Scale & Logic
# ---------------------------------------------------------------------------

def calculate_grade(percentage: float) -> Tuple[str, str]:
    """
    Determine the letter grade and performance description based on percentage.
    Grading Scale:
        90% - 100% : A+ (Outstanding)
        80% - 89.9%: A  (Excellent)
        70% - 79.9%: B  (Very Good)
        60% - 69.9%: C  (Good)
        50% - 59.9%: D  (Pass)
        Below 50%  : F  (Fail)
    """
    if percentage >= 90.0:
        return "A+", "Outstanding"
    elif percentage >= 80.0:
        return "A", "Excellent"
    elif percentage >= 70.0:
        return "B", "Very Good"
    elif percentage >= 60.0:
        return "C", "Good"
    elif percentage >= 50.0:
        return "D", "Pass"
    else:
        return "F", "Fail"


# ---------------------------------------------------------------------------
# Database Operations
# ---------------------------------------------------------------------------

def enter_or_update_marks(
    conn: sqlite3.Connection,
    student_id: str,
    course_id: int,
    exam_name: str,
    max_marks: float,
    obtained_marks: float
) -> Tuple[bool, str]:
    """
    Enter or update examination marks for a student.
    Validates:
        - Student exists
        - Course exists
        - Student is enrolled in the course
        - max_marks > 0
        - 0 <= obtained_marks <= max_marks
    Automatically calculates grade.
    """
    clean_sid = student_id.strip()
    clean_exam = exam_name.strip()

    if max_marks <= 0:
        return False, "Maximum marks must be greater than zero."

    if obtained_marks < 0 or obtained_marks > max_marks:
        return False, f"Obtained marks ({obtained_marks}) must be between 0 and maximum marks ({max_marks})."

    # Verify student
    student = get_student_by_id(conn, clean_sid)
    if not student:
        return False, f"Student with ID '{clean_sid}' not found."

    # Verify course
    course = get_course_by_id(conn, course_id)
    if not course:
        return False, f"Course with ID {course_id} not found."

    # Verify enrollment
    if not is_student_enrolled(conn, clean_sid, course_id):
        return False, f"Student '{clean_sid}' is not enrolled in '{course['course_code']} - {course['course_name']}'."

    # Calculate percentage & grade
    pct = (obtained_marks / max_marks) * 100.0
    grade, _ = calculate_grade(pct)

    cursor = conn.cursor()
    # Check if a mark entry already exists for this exam
    cursor.execute(
        """
        SELECT mark_id FROM marks
        WHERE student_id = ? AND course_id = ? AND exam_name = ?
        """,
        (clean_sid, course_id, clean_exam)
    )
    existing = cursor.fetchone()

    try:
        if existing:
            cursor.execute(
                """
                UPDATE marks SET
                    max_marks = ?, obtained_marks = ?, grade = ?
                WHERE mark_id = ?
                """,
                (max_marks, obtained_marks, grade, existing["mark_id"])
            )
            conn.commit()
            return True, f"Updated marks for {student['name']} in {course['course_code']} ({clean_exam}): {obtained_marks}/{max_marks} (Grade: {grade})."
        else:
            cursor.execute(
                """
                INSERT INTO marks (student_id, course_id, exam_name, max_marks, obtained_marks, grade)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (clean_sid, course_id, clean_exam, max_marks, obtained_marks, grade)
            )
            conn.commit()
            return True, f"Entered marks for {student['name']} in {course['course_code']} ({clean_exam}): {obtained_marks}/{max_marks} (Grade: {grade})."
    except Exception as e:
        conn.rollback()
        return False, f"Database error while saving marks: {str(e)}"


def get_student_marks(conn: sqlite3.Connection, student_id: str) -> List[sqlite3.Row]:
    """Retrieve all examination marks recorded for a student."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT m.mark_id, m.student_id, m.course_id, m.exam_name,
               m.max_marks, m.obtained_marks, m.grade,
               c.course_code, c.course_name, c.credits
        FROM marks m
        JOIN courses c ON m.course_id = c.course_id
        WHERE m.student_id = ?
        ORDER BY c.course_code ASC, m.exam_name ASC
        """,
        (student_id.strip(),)
    )
    return cursor.fetchall()


def calculate_academic_summary(marks_records: List[sqlite3.Row]) -> Dict[str, Any]:
    """
    Calculate total maximum marks, total obtained marks,
    overall percentage, and overall grade from a list of mark rows.
    """
    if not marks_records:
        return {
            "total_max": 0.0,
            "total_obtained": 0.0,
            "overall_percentage": 0.0,
            "overall_grade": "N/A",
            "remarks": "No examination records available."
        }

    total_max = sum(row["max_marks"] for row in marks_records)
    total_obtained = sum(row["obtained_marks"] for row in marks_records)
    overall_percentage = (total_obtained / total_max * 100.0) if total_max > 0 else 0.0
    grade, remarks = calculate_grade(overall_percentage)

    return {
        "total_max": round(total_max, 2),
        "total_obtained": round(total_obtained, 2),
        "overall_percentage": round(overall_percentage, 2),
        "overall_grade": grade,
        "remarks": remarks
    }


# ---------------------------------------------------------------------------
# CLI Handlers
# ---------------------------------------------------------------------------

def enter_marks_cli(conn: sqlite3.Connection) -> None:
    """CLI handler to input or update student exam marks."""
    print("\n" + "=" * 50)
    print("             ENTER / UPDATE MARKS")
    print("=" * 50)

    student_id = input("Enter Student ID (e.g., STU1001): ").strip()
    student = get_student_by_id(conn, student_id)
    if not student:
        print(f"[x] Error: No student found with ID '{student_id}'.")
        return

    enrolled = get_student_courses(conn, student_id)
    if not enrolled:
        print(f"[!] Student {student['name']} is not enrolled in any courses.")
        return

    print(f"\nStudent: {student['name']} ({student_id})")
    print("Enrolled Courses:")
    for idx, c in enumerate(enrolled, 1):
        print(f"  {idx}. [{c['course_id']}] {c['course_code']} - {c['course_name']}")

    course_input = input("\nEnter Course ID or Code: ").strip()
    course = None
    if course_input.isdigit():
        course = get_course_by_id(conn, int(course_input))
    if not course:
        course = get_course_by_code(conn, course_input)

    if not course or not is_student_enrolled(conn, student_id, course["course_id"]):
        print(f"[x] Error: Student is not enrolled in '{course_input}'.")
        return

    while True:
        exam_name = input("Enter Examination Name (e.g., Midterm Exam, Final Exam, Quiz 1): ").strip()
        if exam_name:
            break
        print("[!] Exam name cannot be empty.")

    while True:
        max_str = input("Enter Maximum Marks (e.g., 100): ").strip()
        try:
            max_marks = float(max_str)
            if max_marks > 0:
                break
            print("[!] Maximum marks must be greater than zero.")
        except ValueError:
            print("[!] Please enter a valid number for maximum marks.")

    while True:
        obt_str = input(f"Enter Marks Obtained (0 to {max_marks}): ").strip()
        try:
            obtained = float(obt_str)
            if 0 <= obtained <= max_marks:
                break
            print(f"[!] Obtained marks must be between 0 and {max_marks}.")
        except ValueError:
            print("[!] Please enter a valid number for obtained marks.")

    success, msg = enter_or_update_marks(
        conn, student_id, course["course_id"], exam_name, max_marks, obtained
    )
    if success:
        print(f"\n[+] {msg}")
    else:
        print(f"\n[x] {msg}")


def display_marks_table(marks_records: List[sqlite3.Row]) -> None:
    """Format and print examination marks in a clean table."""
    if not marks_records:
        print("  No examination marks on record.")
        return

    print("  " + "=" * 82)
    print(f"  {'Course Code':<12} | {'Course Name':<26} | {'Exam Name':<16} | {'Score':<10} | {'Grade':<6}")
    print("  " + "-" * 82)
    for m in marks_records:
        score_str = f"{m['obtained_marks']:.1f}/{m['max_marks']:.1f}"
        print(f"  {m['course_code']:<12} | {m['course_name']:<26} | {m['exam_name']:<16} | {score_str:<10} | {m['grade']:<6}")
    print("  " + "=" * 82)
