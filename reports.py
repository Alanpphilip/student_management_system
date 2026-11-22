"""
=============================================================================
Student Management System - reports.py
Comprehensive student academic reports, attendance summaries, and performance evaluation.
=============================================================================
"""

import sqlite3
from typing import Optional, Dict, Any
from students import get_student_by_id, get_all_students
from courses import get_student_courses
from attendance import get_student_attendance_summary
from marks import get_student_marks, calculate_academic_summary


def generate_student_report(conn: sqlite3.Connection, student_id: str) -> Optional[Dict[str, Any]]:
    """
    Compile complete student information into a structured dictionary:
    - Personal & contact info
    - Enrolled courses
    - Attendance summary and class records
    - Examination marks and overall academic GPA/Grade
    """
    clean_sid = student_id.strip()
    student = get_student_by_id(conn, clean_sid)
    if not student:
        return None

    courses = get_student_courses(conn, clean_sid)
    attendance = get_student_attendance_summary(conn, clean_sid)
    marks = get_student_marks(conn, clean_sid)
    academic_summary = calculate_academic_summary(marks)

    # Determine examination eligibility based on attendance (minimum 75%)
    is_eligible_for_exams = attendance["percentage"] >= 75.0 if attendance["total_classes"] > 0 else True

    return {
        "student": student,
        "courses": courses,
        "attendance": attendance,
        "marks": marks,
        "academic_summary": academic_summary,
        "exam_eligibility": is_eligible_for_exams
    }


def print_student_report_card(report: Dict[str, Any]) -> None:
    """
    Render a comprehensive, formatted Academic Report Card on the CLI.
    """
    st = report["student"]
    courses = report["courses"]
    att = report["attendance"]
    marks = report["marks"]
    acad = report["academic_summary"]

    width = 86
    print("\n" + "=" * width)
    print("                     OFFICIAL STUDENT ACADEMIC REPORT")
    print("=" * width)

    # 1. Personal & Academic Profile
    print(" 1. STUDENT PROFILE")
    print(" " + "-" * (width - 2))
    print(f"  Student ID     : {st['student_id']:<20} Admission Date : {st['admission_date']}")
    print(f"  Full Name      : {st['name']:<20} Date of Birth  : {st['dob']}")
    print(f"  Gender         : {st['gender']:<20} Department     : {st['department']}")
    print(f"  Email          : {st['email']:<20} Phone          : {st['phone']}")
    print(f"  Address        : {st['address']}")
    print(" " + "-" * (width - 2))

    # 2. Enrolled Courses
    print("\n 2. ENROLLED COURSES")
    print(" " + "-" * (width - 2))
    if not courses:
        print("  No courses currently enrolled.")
    else:
        print(f"  {'Code':<10} | {'Course Title':<34} | {'Credits':<8} | {'Enrolled Date':<14}")
        print("  " + "-" * 72)
        total_credits = sum(c["credits"] for c in courses)
        for c in courses:
            print(f"  {c['course_code']:<10} | {c['course_name']:<34} | {c['credits']:<8} | {c['enrollment_date']:<14}")
        print("  " + "-" * 72)
        print(f"  Total Enrolled Courses: {len(courses)} | Total Registered Credits: {total_credits}")

    # 3. Attendance Overview
    print("\n 3. ATTENDANCE RECORD")
    print(" " + "-" * (width - 2))
    print(f"  Total Classes Conducted : {att['total_classes']}")
    print(f"  Classes Attended (Present): {att['present_count']}")
    print(f"  Classes Missed (Absent)  : {att['absent_count']}")
    print(f"  Attendance Percentage    : {att['percentage']:.2f}%")
    if att["total_classes"] > 0:
        if report["exam_eligibility"]:
            print("  Attendance Status        : [OK] Satisfies Minimum 75% Requirement (Eligible)")
        else:
            print("  Attendance Status        : [WARNING] Below 75% Threshold (Short Attendance)")
    else:
        print("  Attendance Status        : No attendance sessions logged yet.")

    # 4. Examination Marks & Subject Grades
    print("\n 4. EXAMINATION MARKS & GRADES")
    print(" " + "-" * (width - 2))
    if not marks:
        print("  No examination marks recorded.")
    else:
        print(f"  {'Course Code':<12} | {'Course Title':<28} | {'Exam Name':<16} | {'Score':<10} | {'Grade':<6}")
        print("  " + "-" * 80)
        for m in marks:
            score_str = f"{m['obtained_marks']:.1f}/{m['max_marks']:.1f}"
            print(f"  {m['course_code']:<12} | {m['course_name']:<28} | {m['exam_name']:<16} | {score_str:<10} | {m['grade']:<6}")

    # 5. Overall Academic Performance Summary
    print("\n 5. ACADEMIC PERFORMANCE SUMMARY")
    print(" " + "-" * (width - 2))
    if marks:
        print(f"  Total Maximum Marks  : {acad['total_max']}")
        print(f"  Total Marks Obtained : {acad['total_obtained']}")
        print(f"  Overall Percentage   : {acad['overall_percentage']:.2f}%")
        print(f"  Final Grade Awarded  : {acad['overall_grade']} ({acad['remarks']})")
    else:
        print("  Overall Performance  : Pending Examination Records")

    print("=" * width + "\n")


def view_student_report_cli(conn: sqlite3.Connection) -> None:
    """CLI handler to view an individual student report or general summary."""
    print("\n" + "=" * 50)
    print("             STUDENT ACADEMIC REPORT")
    print("=" * 50)

    student_id = input("Enter Student ID (e.g., STU1001) or press Enter to search: ").strip()

    if not student_id:
        name_query = input("Enter Student Name to search: ").strip()
        if not name_query:
            print("[!] No search input provided. Returning to menu.")
            return

        cursor = conn.cursor()
        cursor.execute("SELECT student_id, name, department FROM students WHERE name LIKE ?", (f"%{name_query}%",))
        matches = cursor.fetchall()

        if not matches:
            print(f"[x] No students found matching '{name_query}'.")
            return

        print("\nSelect a student from matches:")
        for idx, m in enumerate(matches, 1):
            print(f"  {idx}. {m['student_id']} - {m['name']} ({m['department']})")

        sel = input("Select number: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(matches):
            student_id = matches[int(sel) - 1]["student_id"]
        else:
            print("[!] Invalid selection.")
            return

    report = generate_student_report(conn, student_id)
    if not report:
        print(f"[x] Error: No student found with ID '{student_id}'.")
        return

    print_student_report_card(report)
