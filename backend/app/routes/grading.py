"""Grading routes - Essay grading and scoring"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from functools import wraps

from app import db
from app.models import (
    User, Teacher, ExamAttempt, StudentResponse, Question,
    Answer, EssayGrade, ExamResult, ExamSession, Subject, ExamSchedule
)
from . import grading_bp


def grader_required(f):
    """Decorator to check if user is grader (teacher)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        teacher = Teacher.query.filter_by(
            user_id=user_id).first() if user else None
        if not user or user.role != 'teacher' or not teacher or teacher.approval_status != 'approved' or teacher.subject_specialty != 'NGU_VAN_GRADER':
            return jsonify({'error': 'Grader access required'}), 403

        if user.is_first_login:
            return jsonify({'error': 'Password change required'}), 403
        if not user.two_fa_enabled:
            return jsonify({'error': '2FA setup required'}), 403

        return f(*args, **kwargs)
    return decorated_function


# ============================================================
# ESSAY GRADING
# ============================================================

@grading_bp.route('/essays', methods=['GET'])
@jwt_required()
@grader_required
def get_essays_for_grading():
    """Get essays for current grader"""
    try:
        user_id = int(get_jwt_identity())

        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        status = request.args.get('status', 'pending', type=str)
        exam_session_id = request.args.get('exam_session_id', type=int)

        # Get essays assigned to this grader
        query = EssayGrade.query.filter_by(grader_id=user_id)

        if status:
            final_status = 'completed' if status == 'graded' else status
            query = query.filter_by(final_status=final_status)

        if exam_session_id:
            # Filter by session through attempt
            query = (
                query.join(
                    StudentResponse,
                    EssayGrade.response_id == StudentResponse.response_id) .join(
                    ExamAttempt,
                    StudentResponse.attempt_id == ExamAttempt.attempt_id) .filter(
                    ExamAttempt.exam_session_id == exam_session_id))

        total = query.count()
        essays = query.paginate(page=page, per_page=limit, error_out=False)

        data = []
        for essay in essays.items:
            response = StudentResponse.query.get(essay.response_id)
            attempt = response.attempt if response else None
            question = Question.query.get(
                response.question_id) if response else None

            data.append({
                'essay_grade_id': essay.grade_id,
                'attempt_id': attempt.attempt_id if attempt else None,
                'response_id': essay.response_id,
                'question_number': question.question_number if question else None,
                'student_name': attempt.student.full_name if attempt and attempt.student else None,
                'subject': attempt.subject.subject_name if attempt and attempt.subject else None,
                'status': essay.final_status,
                'score': float(essay.score) if essay.score is not None else None,
                'grader_sequence': essay.grading_order,
                'submitted_date': response.submitted_at.isoformat() if response and response.submitted_at else None
            })

        return jsonify({
            'total': total,
            'page': page,
            'pages': (total + limit - 1) // limit,
            'data': data
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@grading_bp.route('/essays/<int:essay_grade_id>', methods=['GET'])
@jwt_required()
@grader_required
def get_essay_details(essay_grade_id):
    """Get essay details for grading"""
    try:
        user_id = int(get_jwt_identity())

        essay = EssayGrade.query.get(essay_grade_id)
        if not essay:
            return jsonify({'error': 'Essay not found'}), 404

        # Verify grader has access
        if essay.grader_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403

        response = StudentResponse.query.get(essay.response_id)
        attempt = response.attempt if response else None
        question = Question.query.get(
            response.question_id) if response else None

        # TÍNH NĂNG MỚI: Lấy đáp án/hướng dẫn chấm từ database
        from app.models import Answer
        answer_record = Answer.query.filter_by(
            question_id=question.question_id).first() if question else None
        answer_key = answer_record.answer_value if answer_record else None

        # Lấy Ngữ liệu nếu có (Hỗ trợ giáo viên xem đoạn văn)
        reading_material = None
        if question and question.paper_id:
            from app.models import ExamPaper
            paper = ExamPaper.query.get(question.paper_id)
            if paper:
                reading_material = paper.reading_material

        return jsonify({
            'essay_grade_id': essay_grade_id,
            'attempt_id': attempt.attempt_id if attempt else None,
            'student_name': attempt.student.full_name if attempt and attempt.student else None,
            'student_cccd': attempt.student.cccd if attempt and attempt.student else None,
            'subject': attempt.subject.subject_name if attempt and attempt.subject else None,
            'question_number': question.question_number if question else None,
            'question_text': question.question_text if question else None,
            'student_answer': response.response_value if response else None,
            'max_points': float(question.points) if question else None,
            'current_score': float(essay.score) if essay.score is not None else None,
            'grader_sequence': essay.grading_order,
            'status': essay.final_status,
            'feedback': essay.feedback,
            'answer_key': answer_key,  # TRẢ VỀ HƯỚNG DẪN CHẤM
            # Trả về ngữ liệu (tùy chọn hiển thị)
            'reading_material': reading_material
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@grading_bp.route('/essays/<int:essay_grade_id>/grade', methods=['POST'])
@jwt_required()
@grader_required
def submit_essay_grade(essay_grade_id):
    """Submit grade for essay"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        if 'score' not in data:
            return jsonify({'error': 'Score required'}), 400

        essay = EssayGrade.query.get(essay_grade_id)
        if not essay:
            return jsonify({'error': 'Essay not found'}), 404

        # Verify grader has access
        if essay.grader_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Validate score range
        response = StudentResponse.query.get(essay.response_id)
        question = Question.query.get(response.question_id)
        max_score = float(question.points) if question else 10.0

        if not (0 <= data['score'] <= max_score):
            return jsonify(
                {'error': f'Score must be between 0 and {max_score}'}), 400

        # Update essay grade
        essay.score = data['score']
        essay.feedback = data.get('feedback', '')
        essay.grading_date = datetime.utcnow()
        essay.final_status = 'completed'
        response.points_earned = data['score']

        _assign_reviewer_if_ready(response, essay)
        db.session.commit()

        return jsonify({
            'message': 'Grade submitted',
            'essay_grade_id': essay_grade_id,
            'score': float(essay.score)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def _assign_reviewer_if_ready(response, current_grade):
    if current_grade.grading_order == 3:
        return

    completed = EssayGrade.query.filter_by(
        response_id=response.response_id,
        final_status='completed'
    ).count()

    existing_reviewer = EssayGrade.query.filter_by(
        response_id=response.response_id,
        grading_order=3
    ).first()

    if completed < 2 or existing_reviewer:
        return

    attempt = response.attempt

    # Những GK đã chấm bài này (GK1, GK2)
    assigned_ids = [
        grade.grader_id for grade in EssayGrade.query.filter_by(
            response_id=response.response_id).all()]

    # LẤY CHUẨN XÁC GIÁO VIÊN NGỮ VĂN ĐÃ DUYỆT (Loại trừ hoàn toàn GVQL)
    grader_teachers = Teacher.query.filter_by(
        approval_status='approved',
        subject_specialty='NGU_VAN_GRADER'
    ).all()

    # Ưu tiên GK3 khác trường thí sinh VÀ chưa từng chấm bài này
    candidates_cross = [
        t.user_id for t in grader_teachers if t.user_id not in assigned_ids and (
            not attempt or t.school_id != attempt.student.school_id)]

    if candidates_cross:
        chosen_grader_id = candidates_cross[0]
    else:
        # Dự phòng: Lấy GK3 cùng trường cũng được, nhưng tuyệt đối không trùng
        # GK1, GK2
        candidates_same = [
            t.user_id for t in grader_teachers if t.user_id not in assigned_ids]
        if not candidates_same:
            return  # Không còn ai chấm được nữa
        chosen_grader_id = candidates_same[0]

    db.session.add(EssayGrade(
        response_id=response.response_id,
        grader_id=chosen_grader_id,
        grading_order=3,
        is_third_grader=True,
        final_status='pending'
    ))


@grading_bp.route('/essays/<int:attempt_id>/finalize-scores', methods=['POST'])
@jwt_required()
def finalize_essay_scores(attempt_id):
    """Finalize essay scores (calculate final score from graders)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        # Only admin can finalize
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        attempt = ExamAttempt.query.get(attempt_id)
        if not attempt:
            return jsonify({'error': 'Attempt not found'}), 404

        # Get essay responses
        essay_responses = StudentResponse.query.filter_by(
            attempt_id=attempt_id,
            response_type='essay'
        ).all()

        if not essay_responses:
            return jsonify({'error': 'No essay questions in attempt'}), 400

        total_essay_score = 0
        processed = 0

        for response in essay_responses:
            # Get all grades for this essay
            grades = EssayGrade.query.filter_by(
                response_id=response.response_id,
                final_status='completed'
            ).all()

            if not grades:
                continue

            reviewer = next(
                (grade for grade in grades if grade.grading_order == 3), None)
            if not reviewer:
                return jsonify(
                    {'error': 'Reviewer grade is required before finalizing essay scores'}), 400

            # Calculate average
            if reviewer.score is not None:
                avg_score = float(reviewer.score)
            elif len(grades) == 2:
                # Two graders - check diff
                diff = abs(float(grades[0].score) - float(grades[1].score))
                if diff > 2.0:
                    # Use 3 graders if available
                    if len(grades) == 3:
                        avg_score = (
                            float(grades[0].score) + float(grades[1].score) + float(grades[2].score)) / 3
                    else:
                        # Average of 2
                        avg_score = (
                            float(grades[0].score) + float(grades[1].score)) / 2
                else:
                    avg_score = (
                        float(grades[0].score) + float(grades[1].score)) / 2
            else:
                # Single grader or average of all available
                avg_score = sum(float(g.score) for g in grades) / len(grades)

            total_essay_score += avg_score
            processed += 1

        # Update attempt
        non_essay_score = sum(
            float(response.points_earned or 0)
            for response in StudentResponse.query.filter(
                StudentResponse.attempt_id == attempt_id,
                StudentResponse.response_type != 'essay'
            ).all()
        )
        attempt.total_score = non_essay_score + total_essay_score
        attempt.status = 'graded'

        db.session.commit()

        return jsonify({
            'message': 'Essay scores finalized',
            'attempt_id': attempt_id,
            'total_essay_score': float(total_essay_score),
            'essays_processed': processed
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# GRADING STATISTICS
# ============================================================

@grading_bp.route('/grading-stats', methods=['GET'])
@jwt_required()
@grader_required
def get_grading_statistics():
    """Get grading statistics for grader"""
    try:
        user_id = get_jwt_identity()
        exam_session_id = request.args.get('exam_session_id', type=int)

        query = EssayGrade.query.filter_by(grader_id=user_id)

        if exam_session_id:
            query = (
                query.join(
                    StudentResponse,
                    EssayGrade.response_id == StudentResponse.response_id) .join(
                    ExamAttempt,
                    StudentResponse.attempt_id == ExamAttempt.attempt_id) .filter(
                    ExamAttempt.exam_session_id == exam_session_id))

        total = query.count()
        graded = query.filter(EssayGrade.final_status == 'completed').count()
        pending = query.filter(EssayGrade.final_status == 'pending').count()

        return jsonify({
            'total_essays': total,
            'graded': graded,
            'pending': pending,
            'grading_progress': f"{graded}/{total}" if total > 0 else "0/0"
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
