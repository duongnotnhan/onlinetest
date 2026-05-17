"""Admin routes - QTV (Quản Trị Viên)"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from functools import wraps

from app import db
from app.models import (
    User, Teacher, Admin, School, ExamSession, ExamSchedule, 
    Subject, MakeupRegistration, ExamResult, StudentSubjectRegistration,
    Student, ExamAttempt, StudentResponse, Province, District
)
from app.utils.validators import validate_date_format
from app.services.exam_service import ExamScoringService
from . import admin_bp


def admin_required(f):
    """Decorator to check if user is admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        if user.is_first_login:
            return jsonify({'error': 'Password change required'}), 403
        if not user.two_fa_enabled:
            return jsonify({'error': '2FA setup required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@admin_required
def get_dashboard():
    """Admin dashboard statistics"""
    try:
        # Count statistics
        total_teachers = Teacher.query.count()
        pending_teachers = Teacher.query.filter_by(approval_status='pending').count()
        total_schools = School.query.count()
        total_students = Student.query.count()
        active_sessions = ExamSession.query.filter_by(is_published=True, is_locked=False).count()
        
        return jsonify({
            'total_teachers': total_teachers,
            'pending_teachers': pending_teachers,
            'total_schools': total_schools,
            'total_students': total_students,
            'active_sessions': active_sessions
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# TEACHER (GVQL) MANAGEMENT
# ============================================================

@admin_bp.route('/teachers', methods=['GET'])
@jwt_required()
@admin_required
def get_teachers():
    """Get teachers list with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        status = request.args.get('status', type=str)  # pending, approved, rejected
        school_id = request.args.get('school_id', type=int)
        search = request.args.get('search', type=str)
        
        query = Teacher.query
        
        # Filters
        if status:
            query = query.filter_by(approval_status=status)
        if school_id:
            query = query.filter_by(school_id=school_id)
        if search:
            query = query.join(User).filter(
                (User.full_name.ilike(f'%{search}%')) | 
                (User.username.ilike(f'%{search}%'))
            )
        
        total = query.count()
        teachers = query.paginate(page=page, per_page=limit, error_out=False)
        
        data = []
        for teacher in teachers.items:
            user = User.query.get(teacher.user_id)
            school = School.query.get(teacher.school_id)
            data.append({
                'teacher_id': teacher.teacher_id,
                'user_id': teacher.user_id,
                'full_name': user.full_name,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'school_id': teacher.school_id,
                'school_name': _school_display_name(school) if school else None,
                'subject_specialty': teacher.subject_specialty,
                'approval_status': teacher.approval_status,
                'created_at': teacher.created_at.isoformat() if teacher.created_at else None
            })
        
        return jsonify({
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit,
            'data': data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/teachers/<int:teacher_id>/approve', methods=['POST'])
@jwt_required()
@admin_required
def approve_teacher(teacher_id):
    """Approve teacher account"""
    try:
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            return jsonify({'error': 'Teacher not found'}), 404
        
        user_id = get_jwt_identity()
        teacher.approval_status = 'approved'
        teacher.approved_by = user_id
        teacher.approval_date = datetime.utcnow()
        
        # Update user active status
        user = User.query.get(teacher.user_id)
        user.is_active = True
        
        db.session.commit()
        
        return jsonify({
            'message': 'Teacher approved successfully',
            'teacher_id': teacher_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/teachers/<int:teacher_id>/reject', methods=['POST'])
@jwt_required()
@admin_required
def reject_teacher(teacher_id):
    """Reject teacher account"""
    try:
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            return jsonify({'error': 'Teacher not found'}), 404
        
        user_id = get_jwt_identity()
        teacher.approval_status = 'rejected'
        teacher.approved_by = user_id
        teacher.approval_date = datetime.utcnow()
        teacher.rejection_reason = reason
        
        db.session.commit()
        
        return jsonify({
            'message': 'Teacher rejected',
            'teacher_id': teacher_id,
            'reason': reason
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# EXAM SESSION MANAGEMENT
# ============================================================

@admin_bp.route('/exam-sessions', methods=['GET'])
@jwt_required()
@admin_required
def get_exam_sessions():
    """Get exam sessions list"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        query = ExamSession.query.order_by(ExamSession.created_at.desc())
        total = query.count()
        sessions = query.paginate(page=page, per_page=limit, error_out=False)
        
        data = []
        for session in sessions.items:
            data.append({
                'exam_session_id': session.exam_session_id,
                'session_name': session.session_name,
                'session_type': session.session_type,
                'start_date': session.start_date.isoformat() if session.start_date else None,
                'end_date': session.end_date.isoformat() if session.end_date else None,
                'is_published': session.is_published,
                'is_locked': session.is_locked,
                'published_date': session.published_date.isoformat() if session.published_date else None,
                'created_at': session.created_at.isoformat() if session.created_at else None
            })
        
        return jsonify({
            'total': total,
            'page': page,
            'pages': (total + limit - 1) // limit,
            'data': data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/exam-sessions', methods=['POST'])
@jwt_required()
@admin_required
def create_exam_session():
    """Create new exam session"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('session_name') or not data.get('start_date') or not data.get('end_date'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate dates
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        if start_date >= end_date:
            return jsonify({'error': 'start_date must be before end_date'}), 400
        
        user_id = get_jwt_identity()
        session = ExamSession(
            session_name=data['session_name'],
            session_type=data.get('session_type', 'official'),
            start_date=start_date,
            end_date=end_date,
            description=data.get('description'),
            created_by=user_id
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'message': 'Exam session created',
            'exam_session_id': session.exam_session_id,
            'session_name': session.session_name
        }), 201
        
    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/exam-sessions/<int:session_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_exam_session_detail(session_id):
    """Get exam session details with schedules"""
    try:
        session = ExamSession.query.get(session_id)
        if not session:
            return jsonify({'error': 'Exam session not found'}), 404
        
        schedules = ExamSchedule.query.filter_by(exam_session_id=session_id).all()
        
        schedule_data = []
        for schedule in schedules:
            subject = Subject.query.get(schedule.subject_id)
            schedule_data.append({
                'schedule_id': schedule.schedule_id,
                'subject_id': schedule.subject_id,
                'subject_name': subject.subject_name if subject else None,
                'exam_date': schedule.exam_date.isoformat() if schedule.exam_date else None,
                'start_time': str(schedule.start_time) if schedule.start_time else None,
                'end_time': str(schedule.end_time) if schedule.end_time else None,
                'duration_minutes': schedule.duration_minutes
            })
        
        return jsonify({
            'exam_session_id': session.exam_session_id,
            'session_name': session.session_name,
            'session_type': session.session_type,
            'start_date': session.start_date.isoformat() if session.start_date else None,
            'end_date': session.end_date.isoformat() if session.end_date else None,
            'is_published': session.is_published,
            'is_locked': session.is_locked,
            'schedules': schedule_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/exam-sessions/<int:session_id>/publish', methods=['POST'])
@jwt_required()
@admin_required
def publish_exam_session(session_id):
    """Publish exam session"""
    try:
        session = ExamSession.query.get(session_id)
        if not session:
            return jsonify({'error': 'Exam session not found'}), 404
        
        if session.is_published:
            return jsonify({'error': 'Session already published'}), 400
        
        # Verify schedules exist
        schedules_count = ExamSchedule.query.filter_by(exam_session_id=session_id).count()
        if schedules_count == 0:
            return jsonify({'error': 'No schedules defined for this session'}), 400
        
        user_id = get_jwt_identity()
        session.is_published = True
        session.published_by = user_id
        session.published_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Exam session published',
            'exam_session_id': session_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# EXAM SCHEDULE MANAGEMENT
# ============================================================

@admin_bp.route('/exam-schedules', methods=['POST'])
@jwt_required()
@admin_required
def create_exam_schedule():
    """Create exam schedule"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['exam_session_id', 'subject_id', 'exam_date', 'start_time', 'end_time']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Verify session exists
        session = ExamSession.query.get(data['exam_session_id'])
        if not session:
            return jsonify({'error': 'Exam session not found'}), 404
        
        # Verify subject exists
        subject = Subject.query.get(data['subject_id'])
        if not subject:
            return jsonify({'error': 'Subject not found'}), 404
        
        # Parse and validate dates/times
        exam_date = datetime.strptime(data['exam_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        
        # Validate dates are within session range
        if not (session.start_date <= exam_date <= session.end_date):
            return jsonify({'error': 'Exam date must be within session date range'}), 400
        
        # Validate times
        if start_time >= end_time:
            return jsonify({'error': 'start_time must be before end_time'}), 400
        
        # Calculate duration
        from datetime import datetime as dt_class
        dt_start = dt_class.combine(exam_date, start_time)
        dt_end = dt_class.combine(exam_date, end_time)
        duration_minutes = int((dt_end - dt_start).total_seconds() / 60)
        expected_duration = subject.duration_minutes
        if expected_duration and duration_minutes < expected_duration:
            return jsonify({'error': f'Duration must be at least {expected_duration} minutes for {subject.subject_name}'}), 400
        
        schedule = ExamSchedule(
            exam_session_id=data['exam_session_id'],
            subject_id=data['subject_id'],
            exam_date=exam_date,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        return jsonify({
            'message': 'Exam schedule created',
            'schedule_id': schedule.schedule_id,
            'subject_name': subject.subject_name,
            'exam_date': exam_date.isoformat(),
            'duration_minutes': duration_minutes
        }), 201
        
    except ValueError as e:
        return jsonify({'error': f'Invalid format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# MAKEUP EXAM MANAGEMENT
# ============================================================

@admin_bp.route('/makeup-registrations', methods=['GET'])
@jwt_required()
@admin_required
def get_makeup_registrations():
    """Get makeup exam requests"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        status = request.args.get('status', type=str)  # pending, approved, rejected
        session_id = request.args.get('session_id', type=int)
        
        query = MakeupRegistration.query
        
        if status:
            query = query.filter_by(approval_status=status)
        if session_id:
            query = query.filter_by(exam_session_id=session_id)
        
        query = query.order_by(MakeupRegistration.request_date.desc())
        total = query.count()
        registrations = query.paginate(page=page, per_page=limit, error_out=False)
        
        data = []
        for reg in registrations.items:
            student = Student.query.get(reg.student_id)
            subject = Subject.query.get(reg.subject_id)
            data.append({
                'registration_id': reg.registration_id,
                'student_id': reg.student_id,
                'student_name': student.full_name if student else None,
                'student_cccd': student.cccd if student else None,
                'subject_id': reg.subject_id,
                'subject_name': subject.subject_name if subject else None,
                'request_date': reg.request_date.isoformat() if reg.request_date else None,
                'approval_status': reg.approval_status,
                'scheduled_date': reg.scheduled_date.isoformat() if reg.scheduled_date else None
            })
        
        return jsonify({
            'total': total,
            'page': page,
            'pages': (total + limit - 1) // limit,
            'data': data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/makeup-registrations/<int:reg_id>/approve', methods=['POST'])
@jwt_required()
@admin_required
def approve_makeup_registration(reg_id):
    """Approve makeup exam request"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('scheduled_date') or not data.get('scheduled_start_time') or not data.get('scheduled_end_time'):
            return jsonify({'error': 'Missing scheduled date/time'}), 400
        
        registration = MakeupRegistration.query.get(reg_id)
        if not registration:
            return jsonify({'error': 'Registration not found'}), 404
        
        # Parse and validate times
        scheduled_date = datetime.strptime(data['scheduled_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['scheduled_start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['scheduled_end_time'], '%H:%M').time()
        
        if start_time >= end_time:
            return jsonify({'error': 'start_time must be before end_time'}), 400

        session = ExamSession.query.get(registration.exam_session_id)
        subject = Subject.query.get(registration.subject_id)
        if session and scheduled_date <= session.end_date:
            return jsonify({'error': 'Makeup exam must be scheduled after the main exam session'}), 400

        duration_minutes = int((
            datetime.combine(scheduled_date, end_time) -
            datetime.combine(scheduled_date, start_time)
        ).total_seconds() / 60)
        if subject and subject.duration_minutes and duration_minutes != subject.duration_minutes:
            return jsonify({'error': f'Duration must be {subject.duration_minutes} minutes for {subject.subject_name}'}), 400
        
        user_id = get_jwt_identity()
        registration.approval_status = 'approved'
        registration.approved_by = user_id
        registration.approval_date = datetime.utcnow()
        registration.scheduled_date = scheduled_date
        registration.scheduled_start_time = start_time
        registration.scheduled_end_time = end_time
        
        db.session.commit()
        
        return jsonify({
            'message': 'Makeup exam approved',
            'registration_id': reg_id
        }), 200
        
    except ValueError as e:
        return jsonify({'error': f'Invalid format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/makeup-registrations/<int:reg_id>/reject', methods=['POST'])
@jwt_required()
@admin_required
def reject_makeup_registration(reg_id):
    """Reject makeup exam request"""
    try:
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        registration = MakeupRegistration.query.get(reg_id)
        if not registration:
            return jsonify({'error': 'Registration not found'}), 404
        
        user_id = get_jwt_identity()
        registration.approval_status = 'rejected'
        registration.approved_by = user_id
        registration.approval_date = datetime.utcnow()
        registration.rejection_reason = reason
        
        db.session.commit()
        
        return jsonify({
            'message': 'Makeup exam rejected',
            'registration_id': reg_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# RESULT MANAGEMENT
# ============================================================

@admin_bp.route('/exam-sessions/<int:session_id>/publish-results', methods=['POST'])
@jwt_required()
@admin_required
def publish_exam_results(session_id):
    """Publish exam results and lock session"""
    try:
        session = ExamSession.query.get(session_id)
        if not session:
            return jsonify({'error': 'Exam session not found'}), 404
        
        if not session.is_published:
            return jsonify({'error': 'Session must be published first'}), 400
        
        if session.is_locked:
            return jsonify({'error': 'Session already locked'}), 400
        
        # Check if all essays are graded
        incomplete_essays = db.session.query(ExamAttempt).filter(
            ExamAttempt.exam_session_id == session_id,
            ExamAttempt.status != 'graded'
        ).first()
        
        if incomplete_essays:
            return jsonify({'error': 'Not all exams are graded yet'}), 400
        
        attempts = ExamAttempt.query.filter_by(exam_session_id=session_id, status='graded').all()
        for attempt in attempts:
            result = ExamResult.query.filter_by(
                student_id=attempt.student_id,
                exam_session_id=session_id,
                subject_id=attempt.subject_id
            ).first()
            if not result:
                result = ExamResult(
                    student_id=attempt.student_id,
                    exam_session_id=session_id,
                    subject_id=attempt.subject_id
                )
                db.session.add(result)

            score = float(attempt.total_score or 0)
            result.score = score
            result.grade = _grade_from_score(score)
            result.status = 'passed' if score >= 5.0 else 'failed'
            result.published = True
            result.published_date = datetime.utcnow()
        
        # Lock session
        session.is_locked = True

        student_user_ids = db.session.query(Student.user_id).join(
            ExamAttempt, Student.student_id == ExamAttempt.student_id
        ).filter(ExamAttempt.exam_session_id == session_id).distinct().all()
        for (student_user_id,) in student_user_ids:
            user = User.query.get(student_user_id)
            if user:
                user.is_active = False
        
        db.session.commit()
        
        return jsonify({
            'message': 'Results published and session locked',
            'exam_session_id': session_id,
            'published_date': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/exam-schedules', methods=['GET'])
@jwt_required()
@admin_required
def get_exam_schedules():
    """Get schedules, optionally filtered by exam session."""
    try:
        session_id = request.args.get('exam_session_id', type=int)
        query = ExamSchedule.query
        if session_id:
            query = query.filter_by(exam_session_id=session_id)

        schedules = query.order_by(ExamSchedule.exam_date.asc(), ExamSchedule.start_time.asc()).all()
        return jsonify({
            'data': [{
                'schedule_id': schedule.schedule_id,
                'exam_session_id': schedule.exam_session_id,
                'session_name': schedule.exam_session.session_name if schedule.exam_session else None,
                'subject_id': schedule.subject_id,
                'subject_name': schedule.subject.subject_name if schedule.subject else None,
                'exam_date': schedule.exam_date.isoformat() if schedule.exam_date else None,
                'start_time': schedule.start_time.strftime('%H:%M') if schedule.start_time else None,
                'end_time': schedule.end_time.strftime('%H:%M') if schedule.end_time else None,
                'duration_minutes': schedule.duration_minutes
            } for schedule in schedules]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/schools', methods=['GET'])
@jwt_required()
@admin_required
def get_schools():
    """Get schools list for account assignment and filtering."""
    try:
        schools = School.query.order_by(School.school_name.asc()).all()
        return jsonify({
            'data': [{
                'school_id': school.school_id,
                'school_name': school.school_name,
                'display_name': _school_display_name(school),
                'address': school.address,
                'phone': school.phone,
                'email': school.email,
                'district_id': school.district_id,
                'province_id': school.province_id,
                'district_name': school.district.district_name if school.district else None,
                'province_name': school.province.province_name if school.province else None,
            } for school in schools]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/schools', methods=['POST'])
@jwt_required()
@admin_required
def create_school():
    """Create a school."""
    try:
        data = request.get_json() or {}
        if not data.get('school_name') or not data.get('province_id') or not data.get('district_id'):
            return jsonify({'error': 'Missing school_name, province_id, or district_id'}), 400

        province = Province.query.get(data['province_id'])
        district = District.query.get(data['district_id'])
        if not province or not district or district.province_id != province.province_id:
            return jsonify({'error': 'Invalid province or ward/commune'}), 400

        school = School(
            school_name=data['school_name'],
            address=data.get('address'),
            phone=data.get('phone'),
            email=data.get('email'),
            district_id=district.district_id,
            province_id=province.province_id,
        )
        db.session.add(school)
        db.session.commit()

        return jsonify({
            'message': 'School created',
            'school_id': school.school_id,
            'school_name': school.school_name,
            'display_name': _school_display_name(school)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/subjects', methods=['GET'])
@jwt_required()
@admin_required
def get_subjects():
    """Get subject catalog."""
    try:
        subjects = Subject.query.order_by(Subject.group_code.asc(), Subject.subject_name.asc()).all()
        return jsonify({
            'data': [{
                'subject_id': subject.subject_id,
                'subject_code': subject.subject_code,
                'subject_name': subject.subject_name,
                'group_code': subject.group_code,
                'exam_type': subject.exam_type,
                'duration_minutes': subject.duration_minutes
            } for subject in subjects]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/locations/provinces', methods=['GET'])
@jwt_required()
@admin_required
def get_provinces():
    """Get provinces/cities for school creation."""
    try:
        provinces = Province.query.order_by(Province.province_id.asc()).all()
        return jsonify({
            'data': [{
                'province_id': province.province_id,
                'province_name': province.province_name,
                'province_code': province.province_code,
                'region': province.region
            } for province in provinces]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/locations/wards', methods=['GET'])
@jwt_required()
@admin_required
def get_wards():
    """Get wards/communes by province. The districts table stores ward/commune names."""
    try:
        province_id = request.args.get('province_id', type=int)
        query = District.query
        if province_id:
            query = query.filter_by(province_id=province_id)

        wards = query.order_by(District.district_name.asc()).all()
        return jsonify({
            'data': [{
                'district_id': ward.district_id,
                'district_name': ward.district_name,
                'province_id': ward.province_id,
                'province_name': ward.province.province_name if ward.province else None
            } for ward in wards]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/students', methods=['GET'])
@jwt_required()
@admin_required
def get_students():
    """Get all students for QTV overview."""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        search = request.args.get('search', type=str)

        query = Student.query
        if search:
            query = query.filter(
                (Student.full_name.ilike(f'%{search}%')) |
                (Student.cccd.ilike(f'%{search}%')) |
                (Student.class_name.ilike(f'%{search}%'))
            )

        total = query.count()
        students = query.order_by(Student.full_name.asc()).paginate(page=page, per_page=limit, error_out=False)
        data = []
        for student in students.items:
            user = User.query.get(student.user_id)
            school = School.query.get(student.school_id)
            data.append({
                'student_id': student.student_id,
                'cccd': student.cccd,
                'full_name': student.full_name,
                'email': user.email if user else None,
                'phone': student.phone,
                'class_name': student.class_name,
                'school_name': _school_display_name(school) if school else None,
                'is_active': user.is_active if user else False
            })

        return jsonify({
            'total': total,
            'page': page,
            'pages': (total + limit - 1) // limit,
            'data': data
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/teachers', methods=['POST'])
@jwt_required()
@admin_required
def create_teacher_account():
    """Create teacher account for a school."""
    try:
        data = request.get_json() or {}
        required = ['username', 'full_name', 'school_id']
        if not all(data.get(field) for field in required):
            return jsonify({'error': 'Missing required fields'}), 400

        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400

        school = School.query.get(data['school_id'])
        if not school:
            return jsonify({'error': 'School not found'}), 404

        temp_password = data.get('temporary_password') or f"Temp@{str(data['username'])[-6:]}"
        user = User(
            username=data['username'],
            email=data.get('email'),
            phone=data.get('phone'),
            full_name=data['full_name'],
            role='teacher',
            school_id=school.school_id,
            is_active=True,
            is_first_login=True
        )
        user.set_password(temp_password)
        db.session.add(user)
        db.session.flush()

        teacher = Teacher(
            user_id=user.user_id,
            school_id=school.school_id,
            subject_specialty=data.get('subject_specialty'),
            qualification_level=data.get('qualification_level'),
            approval_status='approved',
            approval_date=datetime.utcnow(),
            approved_by=get_jwt_identity()
        )
        db.session.add(teacher)
        db.session.commit()

        return jsonify({
            'message': 'Teacher account created',
            'teacher_id': teacher.teacher_id,
            'username': user.username,
            'temporary_password': temp_password
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/results', methods=['GET'])
@jwt_required()
@admin_required
def get_all_results():
    """Get exam results for management and publication overview."""
    try:
        session_id = request.args.get('exam_session_id', type=int)
        query = ExamResult.query
        if session_id:
            query = query.filter_by(exam_session_id=session_id)

        results = query.order_by(ExamResult.updated_at.desc()).limit(500).all()
        data = []
        for result in results:
            student = Student.query.get(result.student_id)
            session = ExamSession.query.get(result.exam_session_id)
            subject = Subject.query.get(result.subject_id)
            data.append({
                'result_id': result.result_id,
                'student_name': student.full_name if student else None,
                'student_cccd': student.cccd if student else None,
                'class_name': student.class_name if student else None,
                'school_name': _school_display_name(student.school) if student and student.school else None,
                'session_name': session.session_name if session else None,
                'subject_name': subject.subject_name if subject else None,
                'score': float(result.score) if result.score is not None else None,
                'grade': result.grade,
                'status': result.status,
                'published': result.published,
                'published_date': result.published_date.isoformat() if result.published_date else None
            })

        return jsonify({'data': data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _grade_from_score(score):
    if score >= 8.5:
        return 'A'
    if score >= 7.0:
        return 'B'
    if score >= 5.5:
        return 'C'
    if score >= 4.0:
        return 'D'
    return 'F'


def _school_display_name(school):
    if not school:
        return None
    parts = [
        school.school_name,
        school.district.district_name if school.district else None,
        school.province.province_name if school.province else None,
    ]
    return ' - '.join(part for part in parts if part)

# ============================================================
# GRADING ASSIGNMENT MANAGEMENT
# ============================================================
@admin_bp.route('/essay-assignments', methods=['GET'])
@jwt_required()
@admin_required
def get_essay_assignments():
    """Lấy danh sách các bài tự luận và người chấm"""
    from app.models import EssayGrade, Question, StudentResponse, ExamAttempt, Student, Subject, User
    
    session_id = request.args.get('exam_session_id', type=int)
    
    query = db.session.query(
        StudentResponse.response_id,
        ExamAttempt.attempt_id,
        Student.cccd.label('student_name'),
        Student.school_id.label('student_school_id'),
        Question.question_number,
        Subject.subject_name
    ).join(ExamAttempt, StudentResponse.attempt_id == ExamAttempt.attempt_id)\
     .join(Student, ExamAttempt.student_id == Student.student_id)\
     .join(Question, StudentResponse.question_id == Question.question_id)\
     .join(Subject, ExamAttempt.subject_id == Subject.subject_id)\
     .filter(Question.question_type == 'essay')
     
    if session_id:
        query = query.filter(ExamAttempt.exam_session_id == session_id)
        
    responses = query.all()
    
    data = []
    for r in responses:
        grades = EssayGrade.query.filter_by(response_id=r.response_id).all()
        graders = []
        for g in grades:
            grader_user = User.query.get(g.grader_id)
            graders.append({
                'grade_id': g.grade_id,
                'grader_id': g.grader_id,
                'grader_name': grader_user.full_name if grader_user else 'Unknown',
                'grading_order': g.grading_order,
                'status': g.final_status,
                'score': float(g.score) if g.score is not None else None
            })
        
        data.append({
            'response_id': r.response_id,
            'attempt_id': r.attempt_id,
            'student_name': r.student_name,
            'student_school_id': r.student_school_id,
            'question_number': r.question_number,
            'subject_name': r.subject_name,
            'graders': graders
        })
        
    return jsonify({'data': data}), 200

@admin_bp.route('/graders', methods=['GET'])
@jwt_required()
@admin_required
def get_eligible_graders():
    """Lấy danh sách các giáo viên đủ điều kiện chấm tự luận"""
    from app.models import Teacher, User, School
    teachers = Teacher.query.filter_by(approval_status='approved', subject_specialty='NGU_VAN_GRADER').all()
    data = []
    for t in teachers:
        user = User.query.get(t.user_id)
        school = School.query.get(t.school_id)
        data.append({
            'user_id': t.user_id,
            'teacher_id': t.teacher_id,
            'full_name': user.full_name if user else 'Unknown',
            'school_id': t.school_id,
            'school_name': school.school_name if school else 'Unknown'
        })
    return jsonify({'data': data}), 200

@admin_bp.route('/essay-assignments/assign', methods=['POST'])
@jwt_required()
@admin_required
def assign_grader():
    """Phân công giáo viên chấm thi"""
    from app.models import EssayGrade
    data = request.get_json()
    response_id = data.get('response_id')
    grader_id = data.get('grader_id')
    grading_order = data.get('grading_order')
    
    if not all([response_id, grader_id, grading_order]):
        return jsonify({'error': 'Thiếu thông tin phân công'}), 400
        
    grade = EssayGrade.query.filter_by(response_id=response_id, grading_order=grading_order).first()
    
    if grade:
        if grade.final_status == 'completed':
            return jsonify({'error': 'Không thể phân công lại bài đã chấm xong'}), 400
        grade.grader_id = grader_id
    else:
        grade = EssayGrade(
            response_id=response_id,
            grader_id=grader_id,
            grading_order=grading_order,
            is_first_grader=(grading_order == 1),
            is_second_grader=(grading_order == 2),
            is_third_grader=(grading_order == 3),
            final_status='pending'
        )
        db.session.add(grade)
        
    db.session.commit()
    return jsonify({'success': True, 'message': 'Phân công thành công'}), 200

@admin_bp.route('/essay-assignments/<int:grade_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def remove_grader_assignment(grade_id):
    """Xóa phân công chấm thi"""
    from app.models import EssayGrade
    grade = EssayGrade.query.get(grade_id)
    if not grade:
         return jsonify({'error': 'Không tìm thấy thông tin chấm'}), 404
    if grade.final_status == 'completed':
         return jsonify({'error': 'Không thể rút bài khi đã chấm xong'}), 400
    db.session.delete(grade)
    db.session.commit()
    return jsonify({'success': True}), 200

# ============================================================
@admin_bp.route('/force-submit-overdue', methods=['POST'])
@jwt_required()
@admin_required
def force_submit_overdue():
    success, result = ExamScoringService.auto_submit_overdue_exams()
    if success:
        return jsonify({
            'success': True, 
            'message': f'Đã quét và tự động thu {result} bài thi quá hạn.'
        }), 200
        
    return jsonify({'error': result}), 400