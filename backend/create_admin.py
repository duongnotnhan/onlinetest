"""
Admin account creation script
Creates a new admin user with 2FA setup required on first login
"""
import sys
import traceback
from os import getenv

import pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load environment variables
load_dotenv()


def create_admin_account():
    """Create a new admin account in the database"""

    # Get database configuration
    db_host = getenv('DB_HOST', 'localhost')
    db_port = int(getenv('DB_PORT', 3306))
    db_user = getenv('DB_USER', 'root')
    db_password = getenv('DB_PASSWORD', 'root')
    db_name = getenv('DB_NAME', 'exam_system')

    print("=" * 60)
    print("ADMIN ACCOUNT CREATION")
    print("=" * 60)

    # Prompt for admin details
    username = input("\nEnter admin username: ").strip()
    if not username:
        print("✗ Username cannot be empty")
        return False

    email = input("Enter admin email: ").strip()
    if not email or '@' not in email:
        print("✗ Invalid email format")
        return False

    password = input("Enter admin password (min 8 chars): ").strip()
    if len(password) < 8:
        print("✗ Password must be at least 8 characters")
        return False

    full_name = input("Enter full name: ").strip()
    phone = input("Enter phone number (optional): ").strip() or None

    try:
        # Connect to database
        print("\nConnecting to database...")
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )

        cursor = connection.cursor()

        # Check if user already exists
        cursor.execute(
            "SELECT user_id FROM users WHERE username = %s OR email = %s",
            (username,
             email))
        if cursor.fetchone():
            print("✗ User with this username or email already exists")
            cursor.close()
            connection.close()
            return False

        # Hash password
        password_hash = generate_password_hash(
            password, method='pbkdf2:sha256')

        # Insert admin user
        print("Creating admin account...")
        cursor.execute("""
            INSERT INTO users (
                username, email, password_hash, full_name, phone, role,
                is_active, is_first_login, two_fa_enabled
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            username, email, password_hash, full_name, phone, 'admin',
            True, True, False  # First login required, 2FA not enabled yet
        ))

        connection.commit()

        user_id = cursor.lastrowid

        # Create admin profile
        cursor.execute("""
            INSERT INTO admins (user_id)
            VALUES (%s)
        """, (user_id,))

        connection.commit()

        print("\n" + "=" * 60)
        print("✓ ADMIN ACCOUNT CREATED SUCCESSFULLY")
        print("=" * 60)
        print(f"\nAdmin ID: {user_id}")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Full Name: {full_name}")
        print(f"\n⚠ First Login Setup Required:")
        print("  - Change password on first login")
        print("  - Setup 2FA (Two-Factor Authentication)")
        print("=" * 60)

        cursor.close()
        connection.close()
        return True

    except pymysql.Error as e:
        print(f"\n✗ Database Error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        traceback.print_exc()
        return False


if __name__ == '__main__':
    sys.exit(0 if create_admin_account() else 1)
