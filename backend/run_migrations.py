#!/usr/bin/env python
"""Run database migrations"""
import pymysql
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def get_db_connection():
    """Get database connection"""
    connection = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'exam_system'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection


def run_migrations():
    """Run all SQL migrations in order"""
    migrations_dir = Path(__file__).parent / 'migrations'
    sql_files = sorted([f for f in migrations_dir.glob('*.sql')])

    if not sql_files:
        print("No migrations found")
        return

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            for sql_file in sql_files:
                print(f"Running migration: {sql_file.name}")
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                    # Split by semicolon but handle comments
                    for statement in sql_content.split(';'):
                        statement = statement.strip()
                        if statement and not statement.startswith('--'):
                            try:
                                cursor.execute(statement)
                                print(f"  ✓ {statement[:60]}...")
                            except Exception as e:
                                print(f"  ✗ Error: {e}")
        connection.commit()
        print("\n✅ All migrations completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        connection.rollback()
    finally:
        connection.close()


if __name__ == '__main__':
    run_migrations()
