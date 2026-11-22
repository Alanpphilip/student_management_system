"""
=============================================================================
Student Management System - test_system.py
Automated test suite verifying core functional and database requirements.
Uses a dedicated temporary database to protect production/sample data.
Run using: python test_system.py
=============================================================================
"""

import os
import sqlite3
import unittest
from datetime import datetime

# Import modules to be tested
from database import get_connection, create_tables, insert_sample_data, initialize_database
from authentication import hash_password, verify_password, validate_user, register_user
from students import (
    generate_student_id,
    add_student,
    get_all_students,
    get_student_by_id,
    search_students,
    update_student,
    delete_student,
    validate_email,
    validate_date,
    validate_phone
)
from courses import (
    add_course,
    get_all_courses,
    get_course_by_id,
    get_course_by_code,
    update_course,
    delete_course,
    enroll_student,
    is_student_enrolled,
    get_student_courses
)
from attendance import (
    record_attendance,
    get_student_attendance_summary,
    get_course_attendance_report
)
from marks import (
    calculate_grade,
    enter_or_update_marks,
    get_student_marks,
    calculate_academic_summary
)


TEST_DB = "test_system_temp.db"


class TestStudentManagementSystem(unittest.TestCase):
    """
    Comprehensive automated test cases for the Student Management System.
    """

    @classmethod
    def setUpClass(cls):
        """Set up an isolated test database for running the tests."""
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except OSError:
                pass

        # Initialize the fresh test database
        initialize_database(TEST_DB)
        cls.conn = get_connection(TEST_DB)

    @classmethod
    def tearDownClass(cls):
        """Clean up and delete the isolated test database file."""
        cls.conn.close()
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except OSError:
                pass

    # -----------------------------------------------------------------------
    # 1. Database & Table Creation Tests
    # -----------------------------------------------------------------------
    def test_01_database_and_tables_creation(self):
        """Verify that all six required tables exist in the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row["name"] for row in cursor.fetchall()]

        required_tables = ["users", "students", "courses", "enrollments", "attendance", "marks"]
        for table in required_tables:
            self.assertIn(
                table,
                tables,
                f"Required database table '{table}' was not created."
            )

    # -----------------------------------------------------------------------
    # 2. Authentication & Password Hashing Tests
    # -----------------------------------------------------------------------
    def test_02_password_hashing(self):
        """Verify SHA-256 password hashing and salt uniqueness."""
        pwd = "SecretPassword123"
        hash1, salt1 = hash_password(pwd)
        hash2, salt2 = hash_password(pwd)

        # Hashes should be 64 characters (hex sha256)
        self.assertEqual(len(hash1), 64)
        self.assertEqual(len(hash2), 64)

        # Different salts must yield different hashes
        self.assertNotEqual(salt1, salt2)
        self.assertNotEqual(hash1, hash2)

        # Verification with correct salt should return True
        self.assertTrue(verify_password(pwd, hash1, salt1))
        # Verification with wrong password should return False
        self.assertFalse(verify_password("WrongPassword", hash1, salt1))

    def test_03_admin_login(self):
        """Verify admin login validation with default credentials and bad credentials."""
        # Valid login
        user = validate_user(self.conn, "admin", "Admin@123")
        self.assertIsNotNone(user, "Default admin login failed.")
        self.assertEqual(user["username"], "admin")
        self.assertEqual(user["role"], "admin")

        # Invalid password
        bad_pass = validate_user(self.conn, "admin", "WrongPass@999")
        self.assertIsNone(bad_pass, "Invalid password was improperly accepted.")

        # Non-existent user
        no_user = validate_user(self.conn, "non_existent_admin", "Admin@123")
        self.assertIsNone(no_user, "Non-existent user was improperly validated.")

    # -----------------------------------------------------------------------
    # 3. Student Registration, Search, and Update Tests
    # -----------------------------------------------------------------------
    def test_04_student_registration(self):
        """Verify student registration with auto-generated ID and validation."""
        new_id = generate_student_id(self.conn)
        self.assertTrue(new_id.startswith("STU"))

        success, msg = add_student(
            self.conn,
            student_id=new_id,
            name="Daniel Brown",
            dob="2004-03-22",
            gender="Male",
            email="daniel.brown@test.com",
            phone="9123456780",
            address="101 Pine Needle Rd",
            department="Computer Science",
            admission_date="2024-08-01"
        )
        self.assertTrue(success, f"Failed to register student: {msg}")

        # Check retrieval
        student = get_student_by_id(self.conn, new_id)
        self.assertIsNotNone(student)
        self.assertEqual(student["name"], "Daniel Brown")
        self.assertEqual(student["email"], "daniel.brown@test.com")

        # Duplicate email prevention
        dup_success, dup_msg = add_student(
            self.conn,
            student_id="STU9999",
            name="Daniel Clone",
            dob="2004-03-22",
            gender="Male",
            email="daniel.brown@test.com",  # Duplicate email
            phone="9123456781",
            address="102 Pine Needle Rd",
            department="Computer Science",
            admission_date="2024-08-01"
        )
        self.assertFalse(dup_success, "Duplicate email registration was not blocked.")

    def test_05_student_searching_and_updating(self):
        """Verify searching students by ID, Name, Department and updating info."""
        # Search by Name
        results = search_students(self.conn, "Daniel", search_by="name")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Daniel Brown")

        # Search by Department
        dept_results = search_students(self.conn, "Computer Science", search_by="department")
        self.assertGreaterEqual(len(dept_results), 1)

        # Update student details
        sid = results[0]["student_id"]
        update_success, update_msg = update_student(
            self.conn,
            student_id=sid,
            phone="9988776655",
            department="Data Science"
        )
        self.assertTrue(update_success, f"Failed to update student: {update_msg}")

        # Verify updated values
        updated = get_student_by_id(self.conn, sid)
        self.assertEqual(updated["phone"], "9988776655")
        self.assertEqual(updated["department"], "Data Science")
        # Ensure name remained intact
        self.assertEqual(updated["name"], "Daniel Brown")

    # -----------------------------------------------------------------------
    # 4. Course Management Tests
    # -----------------------------------------------------------------------
    def test_06_course_creation_and_update(self):
        """Verify course creation and updating course details."""
        code = "CS105"
        name = "Operating Systems"
        success, msg = add_course(self.conn, code, name, credits=4, department="Computer Science")
        self.assertTrue(success, f"Failed to add course: {msg}")

        course = get_course_by_code(self.conn, code)
        self.assertIsNotNone(course)
        self.assertEqual(course["course_name"], name)

        # Update course
        up_success, up_msg = update_course(
            self.conn,
            course_id=course["course_id"],
            course_name="Advanced Operating Systems",
            credits=4
        )
        self.assertTrue(up_success, f"Failed to update course: {up_msg}")

        updated_course = get_course_by_id(self.conn, course["course_id"])
        self.assertEqual(updated_course["course_name"], "Advanced Operating Systems")

    # -----------------------------------------------------------------------
    # 5. Enrollment & Duplicate Prevention Tests
    # -----------------------------------------------------------------------
    def test_07_student_enrollment_and_duplicate_prevention(self):
        """Verify student course enrollment and prevention of duplicate enrollment."""
        # Find Daniel Brown and CS105
        student = search_students(self.conn, "Daniel Brown", search_by="name")[0]
        course = get_course_by_code(self.conn, "CS105")

        sid = student["student_id"]
        cid = course["course_id"]

        # First enrollment - should succeed
        success, msg = enroll_student(self.conn, sid, cid, "2024-08-10")
        self.assertTrue(success, f"Initial enrollment failed: {msg}")
        self.assertTrue(is_student_enrolled(self.conn, sid, cid))

        # Duplicate enrollment - should be prevented
        dup_success, dup_msg = enroll_student(self.conn, sid, cid, "2024-08-10")
        self.assertFalse(dup_success, "Duplicate course enrollment was allowed!")
        self.assertIn("Duplicate Enrollment", dup_msg)

    # -----------------------------------------------------------------------
    # 6. Attendance Recording & Calculation Tests
    # -----------------------------------------------------------------------
    def test_08_attendance_recording_and_calculation(self):
        """Verify attendance marking, status updating, and percentage calculation."""
        student = search_students(self.conn, "Daniel Brown", search_by="name")[0]
        course = get_course_by_code(self.conn, "CS105")
        sid = student["student_id"]
        cid = course["course_id"]

        # Mark 4 sessions: 3 Present, 1 Absent (75%)
        dates_and_status = [
            ("2024-09-01", "Present"),
            ("2024-09-02", "Present"),
            ("2024-09-03", "Absent"),
            ("2024-09-04", "Present"),
        ]

        for dt, st in dates_and_status:
            rec_ok, rec_msg = record_attendance(self.conn, sid, cid, dt, st)
            self.assertTrue(rec_ok, f"Failed to record attendance: {rec_msg}")

        summary = get_student_attendance_summary(self.conn, sid, course_id=cid)
        self.assertEqual(summary["total_classes"], 4)
        self.assertEqual(summary["present_count"], 3)
        self.assertEqual(summary["absent_count"], 1)
        self.assertEqual(summary["percentage"], 75.0)

        # Update attendance for 2024-09-03 from Absent to Present
        up_ok, up_msg = record_attendance(self.conn, sid, cid, "2024-09-03", "Present")
        self.assertTrue(up_ok)
        new_summary = get_student_attendance_summary(self.conn, sid, course_id=cid)
        self.assertEqual(new_summary["present_count"], 4)
        self.assertEqual(new_summary["percentage"], 100.0)

    # -----------------------------------------------------------------------
    # 7. Marks Entry, Validation, and Grade Calculation Tests
    # -----------------------------------------------------------------------
    def test_09_marks_entry_and_grading(self):
        """Verify marks recording, score bounds validation, and letter grade assignment."""
        student = search_students(self.conn, "Daniel Brown", search_by="name")[0]
        course = get_course_by_code(self.conn, "CS105")
        sid = student["student_id"]
        cid = course["course_id"]

        # Test bounds validation: obtained_marks > max_marks must fail
        fail_ok, fail_msg = enter_or_update_marks(
            self.conn, sid, cid, "Midterm Exam", max_marks=100.0, obtained_marks=105.0
        )
        self.assertFalse(fail_ok, "Obtained marks exceeding maximum marks was not prevented.")

        # Test valid entry: 92/100 -> A+
        ok, msg = enter_or_update_marks(
            self.conn, sid, cid, "Midterm Exam", max_marks=100.0, obtained_marks=92.0
        )
        self.assertTrue(ok, f"Failed to enter valid marks: {msg}")

        marks_list = get_student_marks(self.conn, sid)
        self.assertGreaterEqual(len(marks_list), 1)
        entered_mark = marks_list[0]
        self.assertEqual(entered_mark["obtained_marks"], 92.0)
        self.assertEqual(entered_mark["grade"], "A+")

        # Test Grade calculation scale boundaries
        self.assertEqual(calculate_grade(95.0)[0], "A+")
        self.assertEqual(calculate_grade(85.0)[0], "A")
        self.assertEqual(calculate_grade(75.0)[0], "B")
        self.assertEqual(calculate_grade(65.0)[0], "C")
        self.assertEqual(calculate_grade(55.0)[0], "D")
        self.assertEqual(calculate_grade(45.0)[0], "F")

        # Academic summary calculation
        summary = calculate_academic_summary(marks_list)
        self.assertEqual(summary["overall_percentage"], 92.0)
        self.assertEqual(summary["overall_grade"], "A+")

    # -----------------------------------------------------------------------
    # 8. Database Relationship Integrity & Safe Deletion Tests
    # -----------------------------------------------------------------------
    def test_10_database_relationship_integrity_and_deletion(self):
        """
        Verify foreign key cascading deletion and integrity:
        Deleting a student should safely cascade to remove their enrollments,
        attendance records, and marks.
        """
        student = search_students(self.conn, "Daniel Brown", search_by="name")[0]
        sid = student["student_id"]

        # Ensure related records exist before deletion
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) AS c FROM enrollments WHERE student_id = ?", (sid,))
        self.assertGreater(cursor.fetchone()["c"], 0)

        cursor.execute("SELECT COUNT(*) AS c FROM attendance WHERE student_id = ?", (sid,))
        self.assertGreater(cursor.fetchone()["c"], 0)

        cursor.execute("SELECT COUNT(*) AS c FROM marks WHERE student_id = ?", (sid,))
        self.assertGreater(cursor.fetchone()["c"], 0)

        # Delete student record safely
        del_ok, del_msg = delete_student(self.conn, sid)
        self.assertTrue(del_ok, f"Safe deletion failed: {del_msg}")

        # Verify student is gone
        self.assertIsNone(get_student_by_id(self.conn, sid))

        # Verify cascading deletion cleaned up child tables
        cursor.execute("SELECT COUNT(*) AS c FROM enrollments WHERE student_id = ?", (sid,))
        self.assertEqual(cursor.fetchone()["c"], 0, "Enrollments were not cascade deleted.")

        cursor.execute("SELECT COUNT(*) AS c FROM attendance WHERE student_id = ?", (sid,))
        self.assertEqual(cursor.fetchone()["c"], 0, "Attendance was not cascade deleted.")

        cursor.execute("SELECT COUNT(*) AS c FROM marks WHERE student_id = ?", (sid,))
        self.assertEqual(cursor.fetchone()["c"], 0, "Marks were not cascade deleted.")


def run_tests():
    """Run all automated unit tests and display a clear summary."""
    print("\n" + "=" * 65)
    print("      STUDENT MANAGEMENT SYSTEM - AUTOMATED TEST SUITE")
    print("=" * 65)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStudentManagementSystem)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 65)
    if result.wasSuccessful():
        print(" [PASS] ALL TESTS COMPLETED SUCCESSFULLY!")
    else:
        print(f" [FAIL] {len(result.failures)} test(s) failed, {len(result.errors)} error(s) encountered.")
    print("=" * 65 + "\n")
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    import sys
    sys.exit(0 if success else 1)
