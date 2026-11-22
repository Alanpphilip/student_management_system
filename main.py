"""
=============================================================================
Student Management System - main.py
Main entry point, application loop, and menu navigation.
=============================================================================
"""

import sys
import sqlite3
from database import initialize_database, get_connection
from authentication import login_prompt
from students import (
    add_student_cli,
    view_all_students_cli,
    search_student_cli,
    update_student_cli,
    delete_student_cli
)
from courses import (
    manage_courses_menu,
    enroll_student_cli
)
from attendance import (
    mark_attendance_cli,
    view_attendance_report_cli
)
from marks import enter_marks_cli
from reports import view_student_report_cli


def print_banner() -> None:
    """Print the main system header banner."""
    print("\n" + "=" * 65)
    print("      STUDENT MANAGEMENT SYSTEM - ACADEMIC PORTAL (CLI)")
    print("           Python Core Course Project with SQLite3")
    print("=" * 65)


def display_admin_menu() -> None:
    """Display the 13-option administrator main menu."""
    print("\n" + "=" * 50)
    print("                  ADMIN MENU")
    print("=" * 50)
    print("  1.  Add Student")
    print("  2.  View All Students")
    print("  3.  Search Student")
    print("  4.  Update Student")
    print("  5.  Delete Student")
    print("  6.  Manage Courses")
    print("  7.  Enroll Student")
    print("  8.  Mark Attendance")
    print("  9.  View Attendance Report")
    print("  10. Enter Student Marks")
    print("  11. View Student Report")
    print("  12. Logout")
    print("  13. Exit")
    print("=" * 50)


def admin_dashboard(conn: sqlite3.Connection, current_user: dict) -> bool:
    """
    Run the administrator interaction loop.
    Returns:
        True: user logged out, return to login screen.
        False: user chose to exit the application completely.
    """
    print(f"\n[+] Active Session: {current_user['username']} (Role: {current_user['role'].capitalize()})")

    while True:
        display_admin_menu()
        choice = input("Enter your option (1-13): ").strip()

        try:
            if choice == "1":
                add_student_cli(conn)
            elif choice == "2":
                view_all_students_cli(conn)
            elif choice == "3":
                search_student_cli(conn)
            elif choice == "4":
                update_student_cli(conn)
            elif choice == "5":
                delete_student_cli(conn)
            elif choice == "6":
                manage_courses_menu(conn)
            elif choice == "7":
                enroll_student_cli(conn)
            elif choice == "8":
                mark_attendance_cli(conn)
            elif choice == "9":
                view_attendance_report_cli(conn)
            elif choice == "10":
                enter_marks_cli(conn)
            elif choice == "11":
                view_student_report_cli(conn)
            elif choice == "12":
                print(f"\n[*] Administrator '{current_user['username']}' logged out successfully.")
                return True
            elif choice == "13":
                return False
            else:
                print("[!] Invalid option. Please enter a number between 1 and 13.")
        except (KeyboardInterrupt, EOFError):
            print("\n\n[*] Operation cancelled by user.")
        except Exception as e:
            print(f"\n[x] An unexpected error occurred: {str(e)}")

        input("\nPress Enter to return to Admin Menu...")


def main() -> None:
    """
    Application main function.
    Initializes the database, handles login cycles, and controls program termination.
    """
    print_banner()

    # Initialize the database and ensure default tables and sample data exist
    try:
        initialize_database()
    except Exception as e:
        print(f"[x] Fatal error during database initialization: {str(e)}")
        sys.exit(1)

    conn = get_connection()

    try:
        while True:
            # Step 1: Prompt for Admin Login
            user = login_prompt(conn)
            if not user:
                print("\n[*] Exiting Student Management System. Goodbye!")
                break

            # Step 2: Enter Admin Dashboard
            should_continue = admin_dashboard(conn, user)
            if not should_continue:
                print("\n" + "=" * 65)
                print(" Thank you for using the Student Management System. Goodbye!")
                print("=" * 65 + "\n")
                break

    except (KeyboardInterrupt, EOFError):
        print("\n\n[*] Application terminated by user. Goodbye!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
