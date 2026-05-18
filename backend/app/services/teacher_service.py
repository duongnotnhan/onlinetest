"""Teacher Service - Business logic for GVQL operations"""

from app import db
from app.models import (
    User,
    Student,
    Teacher,
    StudentSubjectRegistration,
    MakeupRegistration,
    ExamSession,
)
from app.utils.validators import validate_cccd, validate_password
from datetime import datetime


class TeacherService:
    """Service for teacher operations"""

    @staticmethod
    def create_student_account(
        cccd,
        full_name,
        gender,
        date_of_birth,
        address,
        phone,
        class_name,
        school_id,
        teacher_user_id,
        permanent_address=None,
    ):
        """Create student account"""
        try:
            # Validate CCCD not already used
            existing = Student.query.filter_by(cccd=cccd).first()
            if existing:
                return False, "CCCD already registered"

            # Create user account
            username = cccd
            temp_password = f"Temp@{cccd[-6:]}"

            user = User(
                username=username,
                phone=phone,
                full_name=full_name,
                role="student",
                school_id=school_id,
                is_active=True,
                is_first_login=True,
            )
            user.set_password(temp_password)

            db.session.add(user)
            db.session.flush()

            # Create student record
            student = Student(
                user_id=user.user_id,
                school_id=school_id,
                cccd=cccd,
                full_name=full_name,
                gender=gender,
                date_of_birth=date_of_birth,
                address=address,
                phone=phone,
                class_name=class_name,
                permanent_address=permanent_address or address,
            )

            db.session.add(student)
            db.session.commit()

            return True, {
                "student_id": student.student_id,
                "username": username,
                "temporary_password": temp_password,
            }
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def bulk_register_students(
        student_ids, subject_ids, exam_session_id, teacher_user_id
    ):
        """Register students for exam"""
        try:
            teacher = Teacher.query.filter_by(user_id=teacher_user_id).first()

            registered = 0
            errors = []

            for student_id in student_ids:
                student = Student.query.get(student_id)
                if not student or student.school_id != teacher.school_id:
                    errors.append(
                        {"student_id": student_id, "error": "Invalid student"}
                    )
                    continue

                for subject_id in subject_ids:
                    # Check if already registered
                    existing = StudentSubjectRegistration.query.filter_by(
                        student_id=student_id,
                        subject_id=subject_id,
                        exam_session_id=exam_session_id,
                    ).first()

                    if not existing:
                        registration = StudentSubjectRegistration(
                            student_id=student_id,
                            subject_id=subject_id,
                            exam_session_id=exam_session_id,
                            registered_by=teacher_user_id,
                        )
                        db.session.add(registration)

                registered += 1

            db.session.commit()
            return True, {"registered": registered, "errors": errors}
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def submit_makeup_request(
        student_ids, subject_id, exam_session_id, teacher_user_id
    ):
        """Submit makeup exam request"""
        try:
            teacher = Teacher.query.filter_by(user_id=teacher_user_id).first()

            # Verify session exists
            session = ExamSession.query.get(exam_session_id)
            if not session:
                return False, "Session not found"

            registered = 0
            errors = []

            for student_id in student_ids:
                student = Student.query.get(student_id)
                if not student or student.school_id != teacher.school_id:
                    errors.append(
                        {"student_id": student_id, "error": "Invalid student"}
                    )
                    continue

                # Check if already requested
                existing = MakeupRegistration.query.filter_by(
                    student_id=student_id,
                    exam_session_id=exam_session_id,
                    subject_id=subject_id,
                    approval_status="pending",
                ).first()

                if not existing:
                    registration = MakeupRegistration(
                        student_id=student_id,
                        exam_session_id=exam_session_id,
                        subject_id=subject_id,
                        requested_by=teacher_user_id,
                        request_date=datetime.utcnow(),
                    )
                    db.session.add(registration)

                registered += 1

            db.session.commit()
            return True, {"registered": registered, "errors": errors}
        except Exception as e:
            db.session.rollback()
            return False, str(e)


class StudentImportService:
    """Service for importing students from CSV"""

    @staticmethod
    def validate_student_row(row, required_fields):
        """Validate a student import row"""
        errors = []

        # Check required fields
        for field in required_fields:
            if not row.get(field):
                errors.append(f"Missing {field}")

        if errors:
            return False, errors

        # Validate CCCD
        if not validate_cccd(row.get("cccd", "")):
            errors.append("Invalid CCCD format")

        # Check CCCD uniqueness
        existing = Student.query.filter_by(cccd=row["cccd"]).first()
        if existing:
            errors.append("CCCD already registered")

        # Validate date format
        try:
            datetime.strptime(row["date_of_birth"], "%Y-%m-%d")
        except ValueError:
            errors.append("Invalid date format (use YYYY-MM-DD)")

        # Validate gender
        if row.get("gender") not in ["male", "female", "other"]:
            errors.append("Invalid gender (use: male, female, other)")

        if errors:
            return False, errors

        return True, []

    @staticmethod
    def import_students_batch(students_data, school_id, teacher_user_id):
        """Import multiple students"""
        try:
            imported = 0
            failed = 0
            errors = []

            required_fields = [
                "cccd",
                "full_name",
                "gender",
                "date_of_birth",
                "address",
                "phone",
                "class_name",
            ]

            for row_num, row in enumerate(students_data, start=2):
                is_valid, field_errors = StudentImportService.validate_student_row(
                    row, required_fields
                )

                if not is_valid:
                    failed += 1
                    errors.append({"row": row_num, "errors": field_errors})
                    continue

                # Create student
                success, result = TeacherService.create_student_account(
                    cccd=row["cccd"],
                    full_name=row["full_name"],
                    gender=row["gender"],
                    date_of_birth=datetime.strptime(
                        row["date_of_birth"], "%Y-%m-%d"
                    ).date(),
                    address=row["address"],
                    phone=row["phone"],
                    class_name=row["class_name"],
                    school_id=school_id,
                    teacher_user_id=teacher_user_id,
                    permanent_address=row.get("permanent_address", row["address"]),
                )

                if success:
                    imported += 1
                else:
                    failed += 1
                    errors.append({"row": row_num, "errors": [result]})

            return imported, failed, errors
        except Exception as e:
            return 0, len(students_data), [{"error": str(e)}]


class StudentBulkService:
    """Service for bulk student operations"""

    @staticmethod
    def get_students_by_school(school_id, page=1, limit=20, search=None):
        """Get students of a school"""
        query = Student.query.filter_by(school_id=school_id)

        if search:
            query = query.filter(
                (Student.full_name.ilike(f"%{search}%"))
                | (Student.cccd.ilike(f"%{search}%"))
                | (Student.student_code.ilike(f"%{search}%"))
            )

        total = query.count()
        students = query.paginate(page=page, per_page=limit, error_out=False)

        return total, students.items

    @staticmethod
    def reset_student_password(student_id, teacher_user_id):
        """Reset student password"""
        try:
            teacher = Teacher.query.filter_by(user_id=teacher_user_id).first()
            student = Student.query.get(student_id)

            if not student or student.school_id != teacher.school_id:
                return False, "Student not found"

            # Generate temporary password
            temp_password = f"Temp@{student.cccd[-6:]}"

            user = User.query.get(student.user_id)
            user.set_password(temp_password)
            user.is_first_login = True

            db.session.commit()

            return True, temp_password
        except Exception as e:
            db.session.rollback()
            return False, str(e)
