"""
=============================================================================
Student Management System - attendance.py
Attendance marking, status tracking, and attendance report generation.
=============================================================================
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from courses import get_all_courses, get_course_by_id, get_course_by_code, is_student_enrolled
from students import get_student_by_id, validate_date


# ---------------------------------------------------------------------------
# Database Operations
# ---------------------------------------------------------------------------

def record_attendance(
    conn: sqlite3.Connection,
    student_id: str,
    course_id: int,
    attendance_date: str,
    status: str
) -> tuple[bool, str]:
    """
    Record or update attendance for a student in a course on a specific date.
    Status must be 'Present' or 'Absent'.
    Student must be enrolled in the course.
    """
    clean_sid = student_id.strip()
    clean_date = attendance_date.strip()
    clean_status = status.strip().capitalize()

    if clean_status not in ["Present", "Absent"]:
        return False, "Attendance status must be either 'Present' or 'Absent'."

    if not validate_date(clean_date):
        return False, "Invalid attendance date format. Please use YYYY-MM-DD."

    # Validate student existence
    student = get_student_by_id(conn, clean_sid)
    if not student:
        return False, f"Student with ID '{clean_sid}' does not exist."

    # Validate course existence
    course = get_course_by_id(conn, course_id)
    if not course:
        return False, f"Course with ID {course_id} does not exist."

    # Verify enrollment
    if not is_student_enrolled(conn, clean_sid, course_id):
        return False, f"Student '{clean_sid}' is not enrolled in '{course['course_code']} - {course['course_name']}'."

    cursor = conn.cursor()
    # Check if attendance already exists for this date and course
    cursor.execute(
        """
        SELECT attendance_id, status FROM attendance
        WHERE student_id = ? AND course_id = ? AND attendance_date = ?
        """,
        (clean_sid, course_id, clean_date)
    )
    existing = cursor.fetchone()

    try:
        if existing:
            cursor.execute(
                """
                UPDATE attendance SET status = ?
                WHERE attendance_id = ?
                """,
                (clean_status, existing["attendance_id"])
            )
            conn.commit()
            return True, f"Attendance for {student['name']} on {clean_date} updated from '{existing['status']}' to '{clean_status}'."
        else:
            cursor.execute(
                """
                INSERT INTO attendance (student_id, course_id, attendance_date, status)
                VALUES (?, ?, ?, ?)
                """,
                (clean_sid, course_id, clean_date, clean_status)
            )
            conn.commit()
            return True, f"Attendance marked '{clean_status}' for {student['name']} on {clean_date} in {course['course_code']}."
    except Exception as e:
        conn.rollback()
        return False, f"Failed to record attendance: {str(e)}"


def get_student_attendance_summary(
    conn: sqlite3.Connection,
    student_id: str,
    course_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate and return the attendance statistics for a given student.
    Can be filtered by course_id or computed across all enrolled courses.
    Returns:
        dict with keys: 'records', 'total_classes', 'present_count', 'absent_count', 'percentage'
    """
    cursor = conn.cursor()
    query = """
        SELECT a.attendance_id, a.student_id, a.course_id, a.attendance_date, a.status,
               c.course_code, c.course_name
        FROM attendance a
        JOIN courses c ON a.course_id = c.course_id
        WHERE a.student_id = ?
    """
    params = [student_id.strip()]

    if course_id is not None:
        query += " AND a.course_id = ?"
        params.append(course_id)

    query += " ORDER BY a.attendance_date DESC, c.course_code ASC"
    cursor.execute(query, tuple(params))
    records = cursor.fetchall()

    total = len(records)
    present = sum(1 for r in records if r["status"] == "Present")
    absent = total - present
    percentage = (present / total * 100.0) if total > 0 else 0.0

    return {
        "records": records,
        "total_classes": total,
        "present_count": present,
        "absent_count": absent,
        "percentage": round(percentage, 2)
    }


def get_course_attendance_report(conn: sqlite3.Connection, course_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve attendance summary for all students enrolled in a specific course.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.student_id, s.name, s.department
        FROM students s
        JOIN enrollments e ON s.student_id = e.student_id
        WHERE e.course_id = ?
        ORDER BY s.student_id ASC
        """,
        (course_id,)
    )
    enrolled_students = cursor.fetchall()

    summary_list = []
    for st in enrolled_students:
        sid = st["student_id"]
        stats = get_student_attendance_summary(conn, sid, course_id=course_id)
        summary_list.append({
            "student_id": sid,
            "name": st["name"],
            "department": st["department"],
            "total_classes": stats["total_classes"],
            "present_count": stats["present_count"],
            "absent_count": stats["absent_count"],
            "percentage": stats["percentage"]
        })
    return summary_list


# ---------------------------------------------------------------------------
# CLI Handlers
# ---------------------------------------------------------------------------

def mark_attendance_cli(conn: sqlite3.Connection) -> None:
    """CLI prompt to record student attendance."""
    print("\n" + "=" * 50)
    print("               MARK ATTENDANCE")
    print("=" * 50)
    print("1. Mark Attendance for a Single Student")
    print("2. Batch Mark Attendance for an Entire Course")
    print("-" * 50)

    mode = input("Select attendance mode (1-2): ").strip()

    if mode == "1":
        # Single Student Attendance
        student_id = input("\nEnter Student ID (e.g., STU1001): ").strip()
        student = get_student_by_id(conn, student_id)
        if not student:
            print(f"[x] Error: Student '{student_id}' does not exist.")
            return

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.course_id, c.course_code, c.course_name
            FROM courses c
            JOIN enrollments e ON c.course_id = e.course_id
            WHERE e.student_id = ?
            ORDER BY c.course_code
            """,
            (student_id,)
        )
        enrolled_courses = cursor.fetchall()

        if not enrolled_courses:
            print(f"[!] Student {student['name']} is not enrolled in any courses.")
            return

        print(f"\nEnrolled courses for {student['name']}:")
        for idx, c in enumerate(enrolled_courses, 1):
            print(f"  {idx}. [{c['course_id']}] {c['course_code']} - {c['course_name']}")

        c_choice = input("\nEnter Course ID or Code: ").strip()
        course = None
        if c_choice.isdigit():
            course = get_course_by_id(conn, int(c_choice))
        if not course:
            course = get_course_by_code(conn, c_choice)

        if not course or not is_student_enrolled(conn, student_id, course["course_id"]):
            print(f"[x] Error: Student is not enrolled in course '{c_choice}'.")
            return

        today_str = datetime.now().strftime("%Y-%m-%d")
        date_input = input(f"Enter Attendance Date (YYYY-MM-DD) [Default: {today_str}]: ").strip()
        att_date = date_input if date_input else today_str
        if not validate_date(att_date):
            print("[!] Invalid date format. Using today's date.")
            att_date = today_str

        status_input = input("Enter Status (P for Present / A for Absent): ").strip().upper()
        if status_input in ["P", "PRESENT"]:
            status = "Present"
        elif status_input in ["A", "ABSENT"]:
            status = "Absent"
        else:
            print("[!] Invalid status. Defaulting to 'Present'.")
            status = "Present"

        success, msg = record_attendance(conn, student_id, course["course_id"], att_date, status)
        if success:
            print(f"\n[+] {msg}")
        else:
            print(f"\n[x] {msg}")

    elif mode == "2":
        # Batch Attendance for Entire Course
        courses = get_all_courses(conn)
        if not courses:
            print("[!] No courses available.")
            return

        print("\nAvailable Courses:")
        for c in courses:
            print(f"  [{c['course_id']}] {c['course_code']} - {c['course_name']}")

        c_input = input("\nEnter Course ID or Code: ").strip()
        course = None
        if c_input.isdigit():
            course = get_course_by_id(conn, int(c_input))
        if not course:
            course = get_course_by_code(conn, c_input)

        if not course:
            print(f"[x] Error: Course '{c_input}' not found.")
            return

        # Fetch enrolled students
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.student_id, s.name FROM students s
            JOIN enrollments e ON s.student_id = e.student_id
            WHERE e.course_id = ?
            ORDER BY s.student_id ASC
            """,
            (course["course_id"],)
        )
        enrolled_students = cursor.fetchall()

        if not enrolled_students:
            print(f"[!] No students are currently enrolled in '{course['course_code']}'.")
            return

        today_str = datetime.now().strftime("%Y-%m-%d")
        date_input = input(f"Enter Attendance Date (YYYY-MM-DD) [Default: {today_str}]: ").strip()
        att_date = date_input if date_input else today_str
        if not validate_date(att_date):
            print("[!] Invalid date format. Using today's date.")
            att_date = today_str

        print(f"\nMarking Attendance for {course['course_code']} on {att_date}:")
        print("Enter 'P' for Present, 'A' for Absent (Press Enter for Present):")
        print("-" * 50)

        for s in enrolled_students:
            prompt = f"  {s['student_id']} - {s['name']:<20} (P/A) [P]: "
            val = input(prompt).strip().upper()
            status = "Absent" if val in ["A", "ABSENT"] else "Present"
            record_attendance(conn, s["student_id"], course["course_id"], att_date, status)

        print("\n[+] Batch attendance recorded successfully!")

    else:
        print("[!] Invalid option. Returning to menu.")


def view_attendance_report_cli(conn: sqlite3.Connection) -> None:
    """CLI handler to view attendance reports."""
    print("\n" + "=" * 50)
    print("            VIEW ATTENDANCE REPORT")
    print("=" * 50)
    print("1. Individual Student Attendance Report")
    print("2. Course-wide Attendance Summary")
    print("-" * 50)

    choice = input("Select report type (1-2): ").strip()

    if choice == "1":
        student_id = input("Enter Student ID (e.g., STU1001): ").strip()
        student = get_student_by_id(conn, student_id)
        if not student:
            print(f"[x] Error: Student '{student_id}' does not exist.")
            return

        summary = get_student_attendance_summary(conn, student_id)

        print("\n" + "=" * 70)
        print(f"  ATTENDANCE REPORT FOR: {student['name']} ({student_id})")
        print(f"  Department: {student['department']}")
        print("=" * 70)

        records = summary["records"]
        if not records:
            print("  No attendance records found for this student.")
        else:
            print(f"  {'Date':<12} | {'Course Code':<12} | {'Course Name':<28} | {'Status':<8}")
            print("  " + "-" * 66)
            for r in records:
                print(f"  {r['attendance_date']:<12} | {r['course_code']:<12} | {r['course_name']:<28} | {r['status']:<8}")

        print("=" * 70)
        print(f"  Total Classes: {summary['total_classes']} | Present: {summary['present_count']} | Absent: {summary['absent_count']}")
        print(f"  Overall Attendance Percentage: {summary['percentage']:.2f}%")
        if summary["total_classes"] > 0:
            eligibility = "Eligible for Examinations" if summary["percentage"] >= 75.0 else "Warning: Low Attendance (< 75%)"
            print(f"  Eligibility Status: {eligibility}")
        print("=" * 70 + "\n")

    elif choice == "2":
        courses = get_all_courses(conn)
        if not courses:
            print("[!] No courses available.")
            return

        print("\nAvailable Courses:")
        for c in courses:
            print(f"  [{c['course_id']}] {c['course_code']} - {c['course_name']}")

        c_input = input("\nEnter Course ID or Code: ").strip()
        course = None
        if c_input.isdigit():
            course = get_course_by_id(conn, int(c_input))
        if not course:
            course = get_course_by_code(conn, c_input)

        if not course:
            print(f"[x] Error: Course '{c_input}' not found.")
            return

        summary_list = get_course_attendance_report(conn, course["course_id"])

        print("\n" + "=" * 80)
        print(f"  COURSE ATTENDANCE SUMMARY: {course['course_code']} - {course['course_name']}")
        print("=" * 80)

        if not summary_list:
            print("  No students enrolled or no attendance recorded yet.")
        else:
            print(f"  {'Student ID':<12} | {'Student Name':<22} | {'Total':<6} | {'Present':<8} | {'Absent':<8} | {'Percentage':<10}")
            print("  " + "-" * 76)
            for s in summary_list:
                pct_str = f"{s['percentage']:.2f}%"
                print(f"  {s['student_id']:<12} | {s['name']:<22} | {s['total_classes']:<6} | {s['present_count']:<8} | {s['absent_count']:<8} | {pct_str:<10}")

        print("=" * 80 + "\n")

    else:
        print("[!] Invalid option. Returning to menu.")
