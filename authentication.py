"""
=============================================================================
Student Management System - authentication.py
Admin login, password hashing, verification, and user session management.
=============================================================================
"""

import sqlite3
import hashlib
import secrets
from typing import Optional, Dict, Any


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    Hash a plaintext password using SHA-256 with a cryptographic salt.
    If no salt is provided, a new random hex salt is generated.
    Returns:
        tuple[str, str]: (password_hash, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    combined = salt + password
    hashed = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return hashed, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """
    Verify whether the provided password matches the stored SHA-256 hash
    when combined with the stored salt.
    """
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == stored_hash


def validate_user(conn: sqlite3.Connection, username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Validate a user's login credentials against the 'users' table.
    Returns user details as a dictionary if credentials are valid, else None.
    Uses parameterized query to prevent SQL injection.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, username, password_hash, salt, role FROM users WHERE username = ?",
        (username.strip(),)
    )
    user_row = cursor.fetchone()

    if user_row is None:
        return None

    if verify_password(password, user_row["password_hash"], user_row["salt"]):
        return {
            "user_id": user_row["user_id"],
            "username": user_row["username"],
            "role": user_row["role"]
        }
    return None


def register_user(conn: sqlite3.Connection, username: str, password: str, role: str = "admin") -> bool:
    """
    Register a new user in the database with securely hashed password.
    Returns True upon success, False if username already exists.
    """
    cursor = conn.cursor()
    pwd_hash, salt = hash_password(password)
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)",
            (username.strip(), pwd_hash, salt, role)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def login_prompt(conn: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    """
    Display the CLI login prompt for the administrator.
    Allows up to 3 login attempts before returning None.
    Provides clear feedback for invalid credentials or empty inputs.
    """
    print("\n" + "=" * 50)
    print("           ADMINISTRATOR LOGIN")
    print("=" * 50)
    print("Default Credentials: Username: admin | Password: Admin@123")
    print("Type 'exit' as username to quit the program.")
    print("-" * 50)

    max_attempts = 3
    attempts = 0

    while attempts < max_attempts:
        try:
            username = input("\nEnter Username: ").strip()
            if not username:
                print("[!] Username cannot be empty. Please try again.")
                continue

            if username.lower() == "exit":
                print("[*] Login cancelled by user.")
                return None

            password = input("Enter Password: ").strip()
            if not password:
                print("[!] Password cannot be empty. Please try again.")
                continue

            user = validate_user(conn, username, password)
            if user:
                print("\n[+] Login successful! Welcome, Administrator.")
                return user
            else:
                attempts += 1
                remaining = max_attempts - attempts
                print(f"[x] Invalid username or password! ({remaining} attempt(s) remaining)")

        except (KeyboardInterrupt, EOFError):
            print("\n\n[*] Login process interrupted.")
            return None

    print("\n[!] Maximum login attempts exceeded. Returning to start screen.")
    return None


if __name__ == "__main__":
    from database import get_connection, initialize_database
    initialize_database()
    conn = get_connection()
    try:
        user = login_prompt(conn)
        if user:
            print(f"Logged in user info: {user}")
    finally:
        conn.close()
