"""Authentication routes - THPT QG System"""

from flask import request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from functools import wraps
import os
import io
import qrcode
import pyotp
from datetime import datetime, timedelta

from app import db
from app.models import User, Teacher, Student, Admin, AuditLog
from app.utils.validators import validate_password
from . import auth_bp


def audit_log(
    action, target_table=None, target_id=None, old_values=None, new_values=None
):
    """Decorator to log actions"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            result = f(*args, **kwargs)
            try:
                user_id = get_jwt_identity() if get_jwt_identity() else None
                log = AuditLog(
                    user_id=user_id,
                    action=action,
                    target_table=target_table,
                    target_id=target_id,
                    old_values=old_values,
                    new_values=new_values,
                )
                db.session.add(log)
                db.session.commit()
            except Exception as e:
                print(f"Error creating audit log: {e}")
            return result

        return decorated_function

    return decorator


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register new user account"""
    data = request.get_json()

    # Validate required fields
    if not data.get("username") or not data.get("password") or not data.get("role"):
        return jsonify({"error": "Missing required fields"}), 400

    # Validate role
    if data["role"] not in ["student", "teacher", "admin"]:
        return jsonify({"error": "Invalid role"}), 400

    if data["role"] == "admin" and User.query.filter_by(role="admin").first():
        return (
            jsonify(
                {"error": "Admin accounts must be created by an existing administrator"}
            ),
            403,
        )

    # Check if user exists
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already exists"}), 400

    # Validate password
    is_valid, message = validate_password(data["password"])
    if not is_valid:
        return jsonify({"error": message}), 400

    try:
        # Create user
        user = User(
            username=data["username"],
            email=data.get("email"),
            phone=data.get("phone"),
            full_name=data.get("full_name"),
            role=data["role"],
            is_first_login=True,
            is_active=False if data["role"] == "teacher" else True,
        )
        user.set_password(data["password"])

        db.session.add(user)
        db.session.flush()

        # If teacher or admin, require approval
        if data["role"] == "teacher":
            teacher = Teacher(
                user_id=user.user_id,
                school_id=data.get("school_id"),
                approval_status="pending",
            )
            db.session.add(teacher)
        elif data["role"] == "admin":
            from app.models import Admin

            admin = Admin(user_id=user.user_id)
            db.session.add(admin)

        db.session.commit()

        return (
            jsonify(
                {
                    "user_id": user.user_id,
                    "username": user.username,
                    "role": user.role,
                    "message": "Registration successful",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    User login for students, teachers (GVQL), and admins (QTV)
    Students: cccd + password
    Teachers/Admins: username + password + optional 2FA code
    """
    data = request.get_json()

    # Validate required fields
    if not data.get("cccd") or not data.get("password") or not data.get("role"):
        return jsonify({"error": "Missing required fields (cccd, password, role)"}), 400

    # Validate role
    if data["role"] not in ["student", "teacher", "admin"]:
        return jsonify({"error": "Invalid role"}), 400

    try:
        # Find user
        if data["role"] == "student":
            # Student login by CCCD
            student = Student.query.filter_by(cccd=data["cccd"]).first()
            if not student:
                return jsonify({"error": "Số CCCD/CMND/ĐDCN không tồn tại"}), 401
            user = student.user
        else:
            # Teacher/Admin login by username
            user = User.query.filter_by(username=data["cccd"]).first()
            if not user:
                return jsonify({"error": "Tên đăng nhập hoặc mật khẩu không đúng"}), 401

        # Verify password
        if not user or not user.check_password(data["password"]):
            return jsonify({"error": "Số CCCD/CMND/ĐDCN hoặc mật khẩu không đúng"}), 401

        # Check account active status
        if not user.is_active:
            return jsonify({"error": "Tài khoản chưa được kích hoạt"}), 401

        # For first login (teachers/admins only), require password change
        if user.is_first_login and data["role"] != "student":
            access_token = create_access_token(identity=str(user.user_id))
            return (
                jsonify(
                    {
                        "requires_password_change": True,
                        "access_token": access_token,
                        "user": {
                            "user_id": user.user_id,
                            "username": user.username,
                            "role": user.role,
                            "full_name": user.full_name,
                            "is_first_login": True,
                            "two_fa_enabled": False,
                        },
                    }
                ),
                200,
            )

        # For teachers/admins without 2FA setup, require setup
        if data["role"] != "student" and not user.two_fa_enabled:
            access_token = create_access_token(identity=str(user.user_id))
            return (
                jsonify(
                    {
                        "requires_2fa_setup": True,
                        "access_token": access_token,
                        "user": {
                            "user_id": user.user_id,
                            "username": user.username,
                            "role": user.role,
                            "full_name": user.full_name,
                            "is_first_login": False,
                            "two_fa_enabled": False,
                        },
                    }
                ),
                200,
            )

        # For teachers/admins with 2FA enabled, require 2FA code
        if data["role"] != "student" and user.two_fa_enabled:
            if not data.get("two_fa_code"):
                return (
                    jsonify(
                        {"requires_2fa": True, "message": "Vui lòng cung cấp mã 2FA"}
                    ),
                    202,
                )

            # Verify 2FA code
            totp = pyotp.TOTP(user.two_fa_secret)
            if not totp.verify(data["two_fa_code"]):
                return jsonify({"error": "Mã 2FA không đúng"}), 401

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Create tokens
        access_token = create_access_token(identity=str(user.user_id))
        refresh_token = create_refresh_token(identity=str(user.user_id))

        # THÊM LOGIC PHÂN LOẠI GIÁO VIÊN Ở ĐÂY
        user_data = {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
            "phone": user.phone,
            "is_active": user.is_active,
            "is_first_login": user.is_first_login,
            "two_fa_enabled": user.two_fa_enabled,
        }

        if user.role == "teacher":
            teacher_rec = Teacher.query.filter_by(user_id=user.user_id).first()
            user_data["teacher_type"] = (
                teacher_rec.subject_specialty if teacher_rec else "GVQL"
            )

        return (
            jsonify(
                {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": user_data,
                }
            ),
            200,
        )

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)

    return jsonify({"access_token": access_token}), 200


@auth_bp.route("/first-login-change-password", methods=["POST"])
@jwt_required()
def first_login_change_password():
    """Change password on first login"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()

    # Validate old password
    if not user.check_password(data.get("old_password", "")):
        return jsonify({"error": "Invalid old password"}), 401

    # Validate new password
    is_valid, message = validate_password(data.get("new_password", ""))
    if not is_valid:
        return jsonify({"error": message}), 400

    try:
        user.set_password(data["new_password"])
        user.is_first_login = False
        db.session.commit()

        response = {"message": "Password changed successfully"}
        if user.role in ["teacher", "admin"] and not user.two_fa_enabled:
            response["requires_2fa_setup"] = True
        return jsonify(response), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/setup-2fa", methods=["POST"])
@jwt_required()
def setup_2fa():
    """Setup Two-Factor Authentication for teacher/admin"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role == "student":
        return jsonify({"error": "Only teachers and admins can setup 2FA"}), 403

    try:
        # Generate secret
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)

        # Generate QR code
        provisioning_uri = totp.provisioning_uri(
            name=user.email or user.username, issuer_name="THPT QG Exam System"
        )

        qr = qrcode.QRCode()
        qr.add_data(provisioning_uri)
        qr.make()

        img_io = io.BytesIO()
        qr.make_image().save(img_io, format="PNG")
        img_io.seek(0)

        import base64

        qr_str = base64.b64encode(img_io.getvalue()).decode()

        return (
            jsonify(
                {
                    "secret": secret,
                    "qr_code": f"data:image/png;base64,{qr_str}",
                    "provisioning_uri": provisioning_uri,
                    "message": "Quét mã QR để thiết lập 2FA trên ứng dụng Authenticator của bạn",
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/verify-2fa", methods=["POST"])
@jwt_required()
def verify_2fa():
    """Verify and enable 2FA"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()

    if not user or user.role == "student":
        return jsonify({"error": "Only teachers and admins can verify 2FA"}), 403

    if not data.get("secret") or not data.get("otp"):
        return jsonify({"error": "Missing secret or OTP"}), 400

    try:
        # Verify OTP
        totp = pyotp.TOTP(data["secret"])
        if not totp.verify(data["otp"]):
            return jsonify({"error": "Invalid OTP code"}), 401

        # Save secret and enable 2FA
        user.two_fa_secret = data["secret"]
        user.two_fa_enabled = True
        user.is_first_login = False  # Mark first login as done
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "2FA enabled successfully",
                    "user": {
                        "user_id": user.user_id,
                        "two_fa_enabled": True,
                        "is_first_login": False,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """User logout"""
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    """Change user password"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not data.get("old_password") or not data.get("new_password"):
        return jsonify({"error": "Missing old or new password"}), 400

    try:
        # Verify old password
        if not user.check_password(data["old_password"]):
            return jsonify({"error": "Invalid old password"}), 401

        # Validate new password
        is_valid, message = validate_password(data["new_password"])
        if not is_valid:
            return jsonify({"error": message}), 400

        # Update password
        user.set_password(data["new_password"])
        user.is_first_login = False
        db.session.commit()

        return jsonify({"message": "Password changed successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_token():
    """Refresh access token"""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)

    return jsonify({"access_token": access_token}), 200


@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Get current user profile"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    profile_data = {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name,
        "phone": user.phone,
        "is_active": user.is_active,
        "is_first_login": user.is_first_login,
        "two_fa_enabled": user.two_fa_enabled,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }

    # Add student-specific data
    if user.role == "student":
        student = user.student
        if student:
            profile_data["student"] = {
                "student_id": student.student_id,
                "cccd": student.cccd,
                "class": student.class_name,
                "school_id": student.school_id,
            }

    # Add teacher-specific data
    if user.role == "teacher":
        teacher = user.teacher
        if teacher:
            profile_data["teacher"] = {
                "teacher_id": teacher.teacher_id,
                "school_id": teacher.school_id,
                "approval_status": teacher.approval_status,
            }

    return jsonify(profile_data), 200
