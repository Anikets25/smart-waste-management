"""
create_admin.py
───────────────
Run this script ONCE to create the first admin account.

Usage:
    python create_admin.py

It will ask you to choose a username and password interactively.
The password is hashed with Werkzeug (pbkdf2:sha256) before storage.
No plain-text passwords are ever written anywhere.

You can run this multiple times to add more admin accounts.
"""

import getpass
import sys

from werkzeug.security import generate_password_hash

# Import config and helpers (makes sure .env is loaded)
from config import Config
from utils.helpers import get_db_connection


def main():
    print("=" * 50)
    print("  Smart Waste Management — Create Admin Account")
    print("=" * 50)
    print()

    # ── Get username ──────────────────────────────────────────────────
    username = input("Enter admin username: ").strip()
    if not username:
        print("Error: Username cannot be empty.")
        sys.exit(1)

    if len(username) > 80:
        print("Error: Username must be 80 characters or fewer.")
        sys.exit(1)

    # ── Get password (hidden input, confirmed) ────────────────────────
    while True:
        password = getpass.getpass("Enter password (input is hidden): ")
        if len(password) < 8:
            print("Password must be at least 8 characters. Try again.")
            continue

        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match. Try again.")
            continue

        break

    # ── Hash the password ─────────────────────────────────────────────
    password_hash = generate_password_hash(password)

    # ── Insert into database ──────────────────────────────────────────
    try:
        conn   = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
            (username, password_hash),
        )
        conn.commit()
        cursor.close()
        conn.close()

        print()
        print(f"✅  Admin account '{username}' created successfully.")
        print("    You can now log in at http://127.0.0.1:5000/admin/login")

    except Exception as e:
        # MySQL duplicate key error code is 1062
        if "1062" in str(e) or "Duplicate entry" in str(e):
            print(f"Error: Username '{username}' is already taken. Choose a different one.")
        else:
            print(f"Error: Could not create admin account.\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
