"""Teacher routes - GVQL (Giáo Viên Quản Lý)"""

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from functools import wraps
import csv
import io

from app import db
from app.models import (
    ExamResult,
    User,
    Teacher,
    Student,
    School,
    ExamSession,
    StudentSubjectRegistration,
    MakeupRegistration,
    Subject,
    District,
    Province,
)
from app.utils.validators import validate_cccd, validate_password
from . import teacher_bp


def validate_date(date_str, pattern=r"^\d{4}-\d{2}-\d{2}$"):
    """Validate date string with regex pattern (default YYYY-MM-DD)"""
    import re

    if not re.match(pattern, date_str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def teacher_required(f):
    """Decorator to check if user is teacher or admin"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        # Cho phép cả teacher và admin
        if not user or user.role not in ["teacher", "admin"]:
            return jsonify({"error": "Teacher access required"}), 403

        if user.is_first_login:
            return jsonify({"error": "Password change required"}), 403

        # Nếu là teacher thì kiểm tra thêm trạng thái duyệt
        if user.role == "teacher":
            teacher = Teacher.query.filter_by(user_id=user_id).first()
            if not teacher or teacher.approval_status != "approved":
                return jsonify({"error": "Teacher not approved"}), 403

        return f(*args, **kwargs)

    return decorated_function


def get_school_id_for_user(user):
    """Lấy School ID an toàn cho cả Admin và Teacher"""
    if user.role == "admin":
        # Admin tạm thời lấy trường đầu tiên để quản lý
        school = School.query.first()
        return school.school_id if school else None
    else:
        teacher = Teacher.query.filter_by(user_id=user.user_id).first()
        return teacher.school_id if teacher else None


@teacher_bp.route("/school-id/<int:teacher_id>", methods=["GET"])
@jwt_required()
@teacher_required
def get_school_id(teacher_id):
    """Endpoint để frontend lấy school_id của giáo viên hiện tại"""
    try:
        user = User.query.get(teacher_id)
        school_id = get_school_id_for_user(user)
        if not school_id:
            return jsonify({"error": "School not found for user"}), 404
        return jsonify({"school_id": school_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@teacher_bp.route("/school-results/<int:school_id>", methods=["GET"])
@jwt_required()
@teacher_required
def get_school_results(school_id):
    """Endpoint để giáo viên xem kết quả của trường mình"""
    try:
        results = []
        sessions = ExamSession.query.filter_by(is_published=True).all()
        for session in sessions:
            session_results = (
                db.session.query(
                    Student.full_name,
                    Student.class_name,
                    Student.cccd,
                    Subject.subject_name,
                    ExamResult.score,
                    ExamResult.status,
                )
                .join(
                    StudentSubjectRegistration,
                    Student.student_id == StudentSubjectRegistration.student_id,
                )
                .join(
                    Subject, StudentSubjectRegistration.subject_id == Subject.subject_id
                )
                .join(
                    ExamResult,
                    (ExamResult.student_id == Student.student_id)
                    & (ExamResult.subject_id == Subject.subject_id),
                )
                .filter(
                    Student.school_id == school_id,
                    StudentSubjectRegistration.exam_session_id
                    == session.exam_session_id,
                )
                .all()
            )

            for (
                full_name,
                class_name,
                cccd,
                subject_name,
                score,
                status,
            ) in session_results:
                results.append(
                    {
                        "student_name": full_name,
                        "class_name": class_name,
                        "student_cccd": cccd,
                        "subject_name": subject_name,
                        "score": score,
                        "session_name": session.session_name,
                        "status": status,
                    }
                )

        return jsonify({"results": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@teacher_bp.route("/profile", methods=["GET"])
@jwt_required()
@teacher_required
def get_profile():
    """Get teacher profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if user.role == "admin":
            return (
                jsonify(
                    {
                        "username": user.username,
                        "full_name": user.full_name,
                        "role": "admin",
                    }
                ),
                200,
            )

        teacher = Teacher.query.filter_by(user_id=user_id).first()
        school = School.query.get(teacher.school_id)

        return (
            jsonify(
                {
                    "teacher_id": teacher.teacher_id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone": user.phone,
                    "school_id": teacher.school_id,
                    "school_name": school.school_name if school else None,
                    "subject_specialty": teacher.subject_specialty,
                    "created_at": (
                        teacher.created_at.isoformat() if teacher.created_at else None
                    ),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@teacher_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@teacher_required
def get_dashboard():
    """Teacher home: Tailored for GVQL or GRADER"""
    try:
        user_id = get_jwt_identity()
        teacher = Teacher.query.filter_by(user_id=user_id).first()

        # DÀNH CHO GIÁO VIÊN CHẤM THI NGỮ VĂN
        if teacher.subject_specialty == "NGU_VAN_GRADER":
            from app.models import EssayGrade

            total_assigned = EssayGrade.query.filter_by(grader_id=user_id).count()
            graded = EssayGrade.query.filter_by(
                grader_id=user_id, final_status="completed"
            ).count()
            return (
                jsonify(
                    {
                        "role_type": "grader",
                        "stats": {
                            "total_assigned": total_assigned,
                            "graded": graded,
                            "pending": total_assigned - graded,
                        },
                    }
                ),
                200,
            )

        # DÀNH CHO GIÁO VIÊN QUẢN LÝ TRƯỜNG (GVQL)
        else:
            school_id = teacher.school_id
            student_ids = [
                s.student_id for s in Student.query.filter_by(school_id=school_id).all()
            ]
            pending_makeups = (
                MakeupRegistration.query.filter(
                    MakeupRegistration.student_id.in_(student_ids),
                    MakeupRegistration.approval_status == "pending",
                ).count()
                if student_ids
                else 0
            )

            # Sửa "Đề thi của tôi" thành "Kỳ thi đang diễn ra"
            active_sessions = ExamSession.query.filter_by(
                is_published=True, is_locked=False
            ).count()

            return (
                jsonify(
                    {
                        "role_type": "gvql",
                        "stats": {
                            "total_students": len(student_ids),
                            "pending_makeups": pending_makeups,
                            "active_sessions": active_sessions,
                        },
                    }
                ),
                200,
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# STUDENT MANAGEMENT
# ============================================================


@teacher_bp.route("/students", methods=["GET"])
@jwt_required()
@teacher_required
def get_students():
    """Get students of the school"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        school_id = get_school_id_for_user(user)

        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        search = request.args.get("search", type=str)

        query = Student.query.filter_by(school_id=school_id)

        if search:
            query = query.filter(
                (Student.full_name.ilike(f"%{search}%"))
                | (Student.cccd.ilike(f"%{search}%"))
                | (Student.student_code.ilike(f"%{search}%"))
            )

        total = query.count()
        students = query.paginate(page=page, per_page=limit, error_out=False)

        latest_session = ExamSession.query.order_by(
            ExamSession.created_at.desc()
        ).first()
        session_id = latest_session.exam_session_id if latest_session else None

        data = []
        for student in students.items:
            user = User.query.get(student.user_id)

            elective_1 = None
            elective_2 = None
            if session_id:
                regs = StudentSubjectRegistration.query.filter_by(
                    student_id=student.student_id, exam_session_id=session_id
                ).all()
                subject_ids = [r.subject_id for r in regs]
                if subject_ids:
                    subjects = Subject.query.filter(
                        Subject.subject_id.in_(subject_ids)
                    ).all()
                    electives = [
                        s.subject_code
                        for s in subjects
                        if s.subject_code not in ["TOAN", "NVVAN"]
                    ]
                    if len(electives) > 0:
                        elective_1 = electives[0]
                    if len(electives) > 1:
                        elective_2 = electives[1]

            data.append(
                {
                    "student_id": student.student_id,
                    "student_code": student.student_code,
                    "cccd": student.cccd,
                    "full_name": student.full_name,
                    "gender": student.gender,
                    "date_of_birth": (
                        student.date_of_birth.isoformat()
                        if student.date_of_birth
                        else None
                    ),
                    "address": student.address,
                    "phone": student.phone,
                    "class_name": student.class_name,
                    "has_profile_photo": bool(student.profile_photo),
                    "username": user.username if user else None,
                    "is_active": user.is_active if user else False,
                    "elective_subject_1": elective_1,
                    "elective_subject_2": elective_2,
                }
            )

        return (
            jsonify(
                {
                    "total": total,
                    "page": page,
                    "pages": (total + limit - 1) // limit,
                    "data": data,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@teacher_bp.route("/students/<int:student_id>", methods=["PUT"])
@jwt_required()
@teacher_required
def update_student(student_id):
    """Update a student in the teacher's school."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        school_id = get_school_id_for_user(user)

        student = Student.query.get(student_id)
        if not student or student.school_id != school_id:
            return jsonify({"error": "Student not found"}), 404

        data = request.get_json() or {}
        for field in [
            "full_name",
            "gender",
            "address",
            "permanent_address",
            "phone",
            "class_name",
            "student_code",
        ]:
            if field in data:
                setattr(student, field, data[field])
        if data.get("date_of_birth"):
            student.date_of_birth = datetime.strptime(
                data["date_of_birth"], "%Y-%m-%d"
            ).date()

        user_acc = User.query.get(student.user_id)
        if user_acc:
            user_acc.full_name = student.full_name
            user_acc.phone = student.phone
            if "email" in data:
                user_acc.email = data.get("email")

        if "elective_subject_1" in data or "elective_subject_2" in data:
            latest_session = ExamSession.query.order_by(
                ExamSession.created_at.desc()
            ).first()
            if latest_session:
                session_id = latest_session.exam_session_id

                for code in ["TOAN", "NVVAN"]:
                    subj = Subject.query.filter_by(subject_code=code).first()
                    if subj:
                        existing_reg = StudentSubjectRegistration.query.filter_by(
                            student_id=student_id,
                            subject_id=subj.subject_id,
                            exam_session_id=session_id,
                        ).first()
                        if not existing_reg:
                            db.session.add(
                                StudentSubjectRegistration(
                                    student_id=student_id,
                                    subject_id=subj.subject_id,
                                    exam_session_id=session_id,
                                    registered_by=user_id,
                                )
                            )

                regs = StudentSubjectRegistration.query.filter_by(
                    student_id=student_id, exam_session_id=session_id
                ).all()
                for reg in regs:
                    subj = Subject.query.get(reg.subject_id)
                    if subj and subj.subject_code not in ["TOAN", "NVVAN"]:
                        db.session.delete(reg)

                new_codes = []
                if data.get("elective_subject_1"):
                    new_codes.append(data["elective_subject_1"])
                if data.get("elective_subject_2"):
                    new_codes.append(data["elective_subject_2"])

                for code in new_codes:
                    subj = Subject.query.filter_by(subject_code=code).first()
                    if subj:
                        db.session.add(
                            StudentSubjectRegistration(
                                student_id=student_id,
                                subject_id=subj.subject_id,
                                exam_session_id=session_id,
                                registered_by=user_id,
                            )
                        )

        db.session.commit()
        return jsonify({"message": "Student updated"}), 200
    except ValueError as e:
        return jsonify({"error": f"Invalid date format: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@teacher_bp.route("/students/<int:student_id>", methods=["DELETE"])
@jwt_required()
@teacher_required
def delete_student(student_id):
    """Deactivate a student account without removing exam history."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        school_id = get_school_id_for_user(user)

        student = Student.query.get(student_id)
        if not student or student.school_id != school_id:
            return jsonify({"error": "Student not found"}), 404

        user_acc = User.query.get(student.user_id)
        if user_acc:
            user_acc.is_active = False
        db.session.commit()
        return jsonify({"message": "Student deactivated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@teacher_bp.route("/students/import", methods=["POST"])
@jwt_required()
@teacher_required
def import_students():
    """Import students from CSV and register subjects automatically"""
    import csv
    import io
    from datetime import datetime

    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        school_id = get_school_id_for_user(user)

        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "" or not file.filename.endswith(".csv"):
            return jsonify({"error": "Only CSV files are supported"}), 400

        exam_session_id = request.form.get("exam_session_id")
        if not exam_session_id:
            latest_session = ExamSession.query.order_by(
                ExamSession.created_at.desc()
            ).first()
            if not latest_session:
                return (
                    jsonify({"error": "Chưa có kỳ thi nào được tạo trên hệ thống"}),
                    400,
                )
            exam_session_id = latest_session.exam_session_id

        # Đọc nội dung file
        content = file.stream.read().decode("utf-8-sig")
        stream = io.StringIO(content, newline=None)

        # Tự động nhận diện dấu phân cách (dấu phẩy hoặc dấu chấm phẩy)
        try:
            dialect = csv.Sniffer().sniff(content[:1024], delimiters=",;")
            csv_data = csv.DictReader(stream, dialect=dialect)
        except csv.Error:
            stream.seek(0)
            csv_data = csv.DictReader(stream, delimiter=";")

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
            "tuchon1",
            "tuchon2",
        ]

        for row_num, row in enumerate(csv_data, start=2):
            try:
                clean_row = {}
                for key, value in row.items():
                    if key:
                        clean_key = key.strip()
                        clean_val = value.strip().strip("'") if value else ""
                        clean_row[clean_key] = clean_val

                row = clean_row

                for field in required_fields:
                    if not row.get(field):
                        raise ValueError(f"Missing {field}")

                # Tạm thời hủy xác minh CCCD vì vẫn có trường hợp sử dụng mã định danh có định dạng khác
                # if not validate_cccd(row['cccd']):
                #     raise ValueError('Số CCCD không hợp lệ.')

                existing = Student.query.filter_by(cccd=row["cccd"]).first()
                if existing:
                    raise ValueError("Mã định danh/CCCD đã tồn tại trong hệ thống.")

                gender = None
                if row.get("gender"):
                    if row["gender"].lower() not in [
                        "male",
                        "female",
                        "nam",
                        "nu",
                        "nữ",
                    ]:
                        raise ValueError("Giới tính phải là Male, Female hoặc Nam, Nữ.")
                    gender = (
                        "male" if row["gender"].lower() in ["male", "nam"] else "female"
                    )
                else:
                    raise ValueError("Giới tính không được để trống.")

                if not row.get("tuchon1"):
                    raise ValueError("Môn tự chọn 1 không được để trống.")
                if row.get("tuchon1") and not row.get("tuchon2"):
                    raise ValueError(
                        "Môn tự chọn 2 không được để trống. Nếu thí sinh chỉ đăng ký 1 môn tự chọn, hãy để môn tự chọn 2 là MT."
                    )

                if row.get("tuchon1") and row["tuchon1"].upper() not in [
                    "VAT_LI",
                    "HOA_HO",
                    "SINH_H",
                    "DIA_LI",
                    "LICH_S",
                    "GDKTVL",
                    "TIN_HO",
                    "CNNG",
                    "CNNN",
                    "TIENG_ANH",
                    "TIENG_RU",
                    "TIENG_PH",
                    "TIENG_TR",
                    "TIENG_DU",
                    "TIENG_NH",
                    "TIENG_HAN",
                    "MT",
                ]:
                    raise ValueError("Môn tự chọn 1 không hợp lệ.")
                if row.get("tuchon2") and row["tuchon2"].upper() not in [
                    "VAT_LI",
                    "HOA_HO",
                    "SINH_H",
                    "DIA_LI",
                    "LICH_S",
                    "GDKTVL",
                    "TIN_HO",
                    "CNNG",
                    "CNNN",
                    "TIENG_ANH",
                    "TIENG_RU",
                    "TIENG_PH",
                    "TIENG_TR",
                    "TIENG_DU",
                    "TIENG_NH",
                    "TIENG_HAN",
                    "MT",
                ]:
                    raise ValueError("Môn tự chọn 2 không hợp lệ.")

                if (
                    row.get("tuchon1") == "MT"
                    and row.get("tuchon2")
                    and row["tuchon2"] != "MT"
                ):
                    raise ValueError(
                        "Nếu môn tự chọn 1 là MT thì môn tự chọn 2 phải là MT. Hoặc nếu thí sinh chỉ đăng ký 1 môn tự chọn, phải để tuchon1 là mã môn tự chọn và tuchon2 là MT."
                    )

                if row.get("date_of_birth") and not validate_date(
                    row["date_of_birth"], pattern=r"^\d{4}-\d{2}-\d{2}$"
                ):
                    raise ValueError("Ngày sinh phải có định dạng YYYY-MM-DD.")
                if row.get("date_of_birth"):
                    date_of_birth = datetime.strptime(
                        row["date_of_birth"], "%Y-%m-%d"
                    ).date()

                temp_password = f"{row['full_name'][:4].upper()}@{row['cccd'][-6:]}"

                new_user = User(
                    username=row["cccd"],
                    email=None,
                    phone=row["phone"],
                    full_name=row["full_name"].upper(),
                    role="student",
                    school_id=school_id,
                    is_active=True,
                    is_first_login=True,
                )
                new_user.set_password(temp_password)
                db.session.add(new_user)
                db.session.flush()

                student_code = row.get("student_code")
                if not student_code:
                    student_code = row["cccd"]

                student = Student(
                    user_id=new_user.user_id,
                    school_id=school_id,
                    student_code=student_code,
                    cccd=row["cccd"],
                    full_name=row["full_name"].upper(),
                    gender=gender,
                    date_of_birth=date_of_birth,
                    address=row["address"],
                    phone=row["phone"],
                    class_name=row["class_name"].upper(),
                    permanent_address=row.get("permanent_address", row["address"]),
                )

                db.session.add(student)
                db.session.flush()

                subject_codes = ["TOAN", "NVVAN"]
                if row.get("tuchon1"):
                    subject_codes.append(row["tuchon1"])
                if row.get("tuchon2"):
                    subject_codes.append(row["tuchon2"])

                for code in subject_codes:
                    subj = Subject.query.filter_by(subject_code=code).first()
                    if subj:
                        existing_reg = StudentSubjectRegistration.query.filter_by(
                            student_id=student.student_id,
                            subject_id=subj.subject_id,
                            exam_session_id=exam_session_id,
                        ).first()
                        if not existing_reg:
                            db.session.add(
                                StudentSubjectRegistration(
                                    student_id=student.student_id,
                                    subject_id=subj.subject_id,
                                    exam_session_id=exam_session_id,
                                    registered_by=user_id,
                                )
                            )

                db.session.commit()
                imported += 1

            except Exception as e:
                db.session.rollback()
                failed += 1
                errors.append(
                    {
                        "row": row_num,
                        "error": "Gặp lỗi khi xử lý dòng này. Xem chi tiết lỗi bên cạnh hoặc liên hệ Quản trị viên nếu bạn nghĩ đây là lỗi hệ thống.",
                        "details": str(e),
                    }
                )

        return (
            jsonify(
                {
                    "imported": imported,
                    "failed": failed,
                    "errors": errors,
                    "total": imported + failed,
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@teacher_bp.route("/students/<int:student_id>/reset-password", methods=["POST"])
@jwt_required()
@teacher_required
def reset_student_password(student_id):
    """Reset student password to temporary"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        school_id = get_school_id_for_user(user)

        student = Student.query.get(student_id)
        if not student or student.school_id != school_id:
            return jsonify({"error": "Student not found"}), 404

        temp_password = f"{student.full_name[:4].upper()}@{student.cccd[-6:]}"

        student_user = User.query.get(student.user_id)
        student_user.set_password(temp_password)
        student_user.is_first_login = True

        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Password reset successfully",
                    "temporary_password": temp_password,
                    "note": "Student must change this password on first login",
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@teacher_bp.route("/students/<int:student_id>/photo", methods=["POST"])
@jwt_required()
@teacher_required
def upload_student_photo(student_id):
    """Upload or replace student exam photo."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        school_id = get_school_id_for_user(user)

        student = Student.query.get(student_id)
        if not student or student.school_id != school_id:
            return jsonify({"error": "Student not found"}), 404

        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": "No file selected"}), 400

        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in {"jpg", "jpeg", "png"}:
            return jsonify({"error": "Only jpg, jpeg, png files are supported"}), 400

        student.profile_photo = file.read()
        student.profile_photo_filename = file.filename
        db.session.commit()

        return jsonify({"message": "Student photo uploaded"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ============================================================
# EXAM REGISTRATION
# ============================================================


@teacher_bp.route("/student-registrations", methods=["POST"])
@jwt_required()
@teacher_required
def register_students_for_exam():
    """Register students for exam session and subjects"""
    try:
        data = request.get_json()

        if (
            not data.get("exam_session_id")
            or not data.get("student_ids")
            or not data.get("subject_ids")
        ):
            return jsonify({"error": "Missing required fields"}), 400

        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        school_id = get_school_id_for_user(user)

        exam_session_id = data["exam_session_id"]
        student_ids = data["student_ids"]
        subject_ids = data["subject_ids"]

        session = ExamSession.query.get(exam_session_id)
        if not session:
            return jsonify({"error": "Exam session not found"}), 404

        registered = 0
        errors = []

        for student_id in student_ids:
            student = Student.query.get(student_id)
            if not student:
                errors.append({"student_id": student_id, "error": "Student not found"})
                continue

            if student.school_id != school_id:
                errors.append(
                    {"student_id": student_id, "error": "Student not in your school"}
                )
                continue

            for subject_id in subject_ids:
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
                        registered_by=user_id,
                    )
                    db.session.add(registration)

            registered += 1

        db.session.commit()

        return (
            jsonify(
                {
                    "registered": registered,
                    "errors": errors,
                    "message": "Students registered successfully",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ============================================================
# MAKEUP EXAM REGISTRATION
# ============================================================


@teacher_bp.route("/makeup-registrations", methods=["POST"])
@jwt_required()
@teacher_required
def create_makeup_request():
    """Request makeup exam for students"""
    try:
        data = request.get_json()

        if (
            not data.get("exam_session_id")
            or not data.get("student_ids")
            or not data.get("subject_id")
        ):
            return jsonify({"error": "Missing required fields"}), 400

        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        school_id = get_school_id_for_user(user)

        exam_session_id = data["exam_session_id"]
        student_ids = data["student_ids"]
        subject_id = data["subject_id"]

        session = ExamSession.query.get(exam_session_id)
        if not session:
            return jsonify({"error": "Exam session not found"}), 404

        registered = 0
        errors = []

        for student_id in student_ids:
            student = Student.query.get(student_id)
            if not student:
                errors.append({"student_id": student_id, "error": "Student not found"})
                continue

            if student.school_id != school_id:
                errors.append(
                    {"student_id": student_id, "error": "Student not in your school"}
                )
                continue

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
                    requested_by=user_id,
                    request_date=datetime.utcnow(),
                )
                db.session.add(registration)

            registered += 1

        db.session.commit()

        return (
            jsonify(
                {
                    "registered": registered,
                    "errors": errors,
                    "message": "Makeup requests submitted",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@teacher_bp.route("/makeup-registrations/<int:session_id>", methods=["GET"])
@jwt_required()
@teacher_required
def get_makeup_registrations(session_id):
    """Get makeup registrations for school"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        school_id = get_school_id_for_user(user)

        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        status = request.args.get("status", type=str)

        query = MakeupRegistration.query.filter_by(exam_session_id=session_id)

        student_ids = [
            s.student_id for s in Student.query.filter_by(school_id=school_id).all()
        ]
        query = query.filter(MakeupRegistration.student_id.in_(student_ids))

        if status:
            query = query.filter_by(approval_status=status)

        total = query.count()
        registrations = query.paginate(page=page, per_page=limit, error_out=False)

        data = []
        for reg in registrations.items:
            student = Student.query.get(reg.student_id)
            subject = Subject.query.get(reg.subject_id)
            data.append(
                {
                    "registration_id": reg.registration_id,
                    "student_name": student.full_name if student else None,
                    "subject_name": subject.subject_name if subject else None,
                    "request_date": (
                        reg.request_date.isoformat() if reg.request_date else None
                    ),
                    "approval_status": reg.approval_status,
                }
            )

        return (
            jsonify(
                {
                    "total": total,
                    "page": page,
                    "pages": (total + limit - 1) // limit,
                    "data": data,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
