Student Management System (SMS)

A beginner-friendly command-line Student Management System developed using Python 3.x and SQLite3 as a Python Core Course Project.

This application helps educational institutions manage student records, courses, enrollments, attendance, examination marks, and academic performance reports.

1. Project Overview

The Student Management System provides a simple way to manage academic information through a command-line interface.

Main Features

- Admin login and authentication
- Student registration and management
- Search, update, and delete student records
- Course creation and management
- Student course enrollment
- Attendance marking and tracking
- Examination marks management
- Automatic percentage and grade calculation
- Student academic reports
- Automated testing

2. Technologies Used

Technology| Purpose
Python 3.x| Application development
SQLite3| Database management
SQL| Database operations
VS Code| Code editor
Git and GitHub| Version control and project hosting

The project uses Python's standard library and does not require external packages.

3. Project Structure

Student-Management-System/
│
├── main.py
├── database.py
├── authentication.py
├── students.py
├── courses.py
├── attendance.py
├── marks.py
├── reports.py
├── test_system.py
├── README.md
└── .gitignore

File Descriptions

File| Description
"main.py"| Main application and admin menu
"database.py"| Database connection and table creation
"authentication.py"| Admin login and password handling
"students.py"| Student registration and management
"courses.py"| Course management and enrollment
"attendance.py"| Attendance recording and reports
"marks.py"| Marks entry and grade calculation
"reports.py"| Academic performance reports
"test_system.py"| Automated project tests

4. Database Details

The application uses SQLite3 and includes six relational database tables:

1. "users" – Stores administrator login information.
2. "students" – Stores student personal and academic details.
3. "courses" – Stores course information.
4. "enrollments" – Stores student course enrollment details.
5. "attendance" – Stores attendance records.
6. "marks" – Stores examination marks and grades.

The database uses primary keys, foreign keys, unique constraints, and validation rules to maintain data integrity.

The database file "student_management.db" is generated when the application initializes.

5. Default Admin Login

Field| Default Value
Username| "admin"
Password| "Admin@123"
Role| Administrator

These are demonstration credentials. Change the default password before using the system with real information.

6. Grading System

The application uses the following grading scale:

Percentage| Grade| Performance
90–100%| A+| Outstanding
80–89.99%| A| Excellent
70–79.99%| B| Very Good
60–69.99%| C| Good
50–59.99%| D| Pass
Below 50%| F| Fail

Attendance Eligibility

- 75% or above: Eligible for examinations.
- Below 75%: Low attendance warning.

7. Admin Menu

The application provides the following menu options:

========================================
             ADMIN MENU
========================================
1. Add Student
2. View All Students
3. Search Student
4. Update Student
5. Delete Student
6. Manage Courses
7. Enroll Student
8. Mark Attendance
9. View Attendance Report
10. Enter Student Marks
11. View Student Report
12. Logout
13. Exit
========================================

8. How to Run the Project

Requirements

- Python 3.x
- Visual Studio Code
- Git (optional)

Step 1: Clone the Repository

git clone https://github.com/USERNAME/Student-Management-System.git

Replace "USERNAME" with the GitHub account username that owns the repository.

Step 2: Open the Project Folder

Open the downloaded project folder in Visual Studio Code.

Step 3: Run the Application

Open the VS Code terminal and execute:

python main.py

Step 4: Login

Use the default administrator credentials:

Username: admin
Password: Admin@123

9. Running Automated Tests

To execute the automated test suite, run:

python test_system.py

The tests are intended to verify important application functions, including:

- Database and table creation
- Password hashing and verification
- Admin authentication
- Student registration and management
- Course management
- Student enrollment
- Attendance calculations
- Marks and grade calculations
- Database relationships and constraints

The actual test coverage depends on the implementation in "test_system.py".

10. Learning Outcomes

This project demonstrates practical use of:

- Python functions and modules
- Conditional statements and loops
- Lists, dictionaries, and tuples
- Exception handling
- SQLite database operations
- SQL queries and relationships
- CRUD operations
- Input validation
- Basic authentication
- Automated testing

11. Future Enhancements

- Graphical user interface
- Student login portal
- Export academic reports to PDF
- Advanced performance analytics
- Database backup and restore
- Email notifications

12. Conclusion

The Student Management System is a Python-based academic project designed to simplify student information management. It demonstrates the practical application of Python programming and SQLite database concepts in a modular command-line application.

---

Project: Student Management System
Language: Python 3.x
Database: SQLite3
Project Type: Python Core Course Project
