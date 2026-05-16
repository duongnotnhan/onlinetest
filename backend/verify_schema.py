#!/usr/bin/env python
"""Verify database schema"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

import pymysql

def verify_schema():
    """Verify that reading_material column exists"""
    connection = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'exam_system'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with connection.cursor() as cursor:
            # Check if reading_material column exists
            cursor.execute("""
                SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'exam_papers' AND COLUMN_NAME = 'reading_material'
            """)
            result = cursor.fetchone()
            if result:
                print("✅ Column 'reading_material' verified successfully!")
                print(f"   Name: {result['COLUMN_NAME']}")
                print(f"   Type: {result['COLUMN_TYPE']}")
                print(f"   Nullable: {result['IS_NULLABLE']}")
                print(f"   Comment: {result['COLUMN_COMMENT']}")
            else:
                print("❌ Column 'reading_material' NOT found in exam_papers table")
                
            # List all columns in exam_papers
            cursor.execute("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'exam_papers'
                ORDER BY ORDINAL_POSITION
            """)
            columns = cursor.fetchall()
            print("\nAll columns in exam_papers table:")
            for col in columns:
                print(f"  - {col['COLUMN_NAME']}")
    finally:
        connection.close()

if __name__ == '__main__':
    verify_schema()
