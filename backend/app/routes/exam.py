"""Exam routes - Exam paper management"""
from app.models import QuestionSection, QuestionSectionType
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from functools import wraps
import json
import csv
import io

from app import db
from app.models import (
    User,
    ExamPaper,
    Question,
    AnswerChoice,
    Answer,
    GeneratedPaper,
    QuestionItem,
    Subject,
    ExamSession,
    ExamSchedule,
    ExamAttempt,
    StudentResponse,
    Student,
    EssayGrade,
    Teacher)
from app.services.exam_service import ExamPaperService, ExamScoringService
from . import exam_bp


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


# ============================================================
# EXAM PAPER MANAGEMENT
# ============================================================

@exam_bp.route('/exam-papers', methods=['POST'])
@jwt_required()
@admin_required
def create_exam_paper():
    """Create exam paper"""
    try:
        data = request.get_json()

        if not data.get('subject_id') or not data.get(
                'exam_session_id') or not data.get('paper_code'):
            return jsonify({'error': 'Missing required fields'}), 400

        success, result = ExamPaperService.create_exam_paper(
            subject_id=data['subject_id'],
            exam_session_id=data['exam_session_id'],
            paper_code=data['paper_code'],
            created_by=get_jwt_identity()
        )

        if not success:
            return jsonify({'error': result}), 400

        paper = ExamPaper.query.get(result.get('paper_id'))
        if paper:
            if 'randomization_enabled' in data:
                paper.randomization_enabled = bool(
                    data['randomization_enabled'])

            # For Vietnamese Language (Ngữ Văn), set shared reading material if
            # provided
            if 'reading_material' in data and data['reading_material']:
                paper.reading_material = data['reading_material']

            db.session.commit()

        return jsonify(result), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@exam_bp.route('/exam-papers/<int:paper_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_exam_paper(paper_id):
    """Get exam paper details"""
    try:
        paper_data = ExamPaperService.get_paper_details(paper_id)

        if not paper_data:
            return jsonify({'error': 'Paper not found'}), 404

        return jsonify(paper_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@exam_bp.route('/exam-papers/<int:paper_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_exam_paper(paper_id):
    """Update exam paper (e.g., reading material for Vietnamese Language)"""
    try:
        data = request.get_json()
        paper = ExamPaper.query.get(paper_id)

        if not paper:
            return jsonify({'error': 'Paper not found'}), 404

        # Update reading material for Vietnamese Language (Ngữ Văn)
        if 'reading_material' in data:
            paper.reading_material = data['reading_material']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Paper updated successfully',
            'paper_id': paper.paper_id,
            'reading_material': paper.reading_material
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@exam_bp.route('/exam-papers', methods=['GET'])
@jwt_required()
@admin_required
def get_exam_papers():
    """Get all exam papers for session"""
    try:
        exam_session_id = request.args.get('exam_session_id', type=int)
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)

        query = ExamPaper.query
        if exam_session_id:
            query = query.filter_by(exam_session_id=exam_session_id)
        total = query.count()
        papers = query.order_by(
            ExamPaper.created_at.desc()).paginate(
            page=page, per_page=limit, error_out=False)

        data = []
        for paper in papers.items:
            subject = Subject.query.get(paper.subject_id)
            q_count = Question.query.filter_by(paper_id=paper.paper_id).count()
            v_count = GeneratedPaper.query.filter_by(
                paper_id=paper.paper_id).count()

            data.append(
                {
                    'paper_id': paper.paper_id,
                    'exam_session_id': paper.exam_session_id,
                    'session_name': ExamSession.query.get(
                        paper.exam_session_id).session_name if paper.exam_session_id else None,
                    'subject_id': paper.subject_id,
                    'subject_name': subject.subject_name if subject else None,
                    'paper_code': paper.paper_code,
                    'total_questions': q_count,
                    'current_questions': q_count,
                    'total_points': float(
                        paper.total_points) if paper.total_points else 10.0,
                    'is_finalized': paper.is_finalized,
                    'versions': v_count})

        return jsonify({
            'total': total,
            'page': page,
            'pages': (total + limit - 1) // limit,
            'data': data
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# QUESTION MANAGEMENT
# ============================================================

@exam_bp.route('/exam-papers/<int:paper_id>/questions', methods=['POST'])
@jwt_required()
@admin_required
def add_question(paper_id):
    """Add question to paper"""
    try:
        data = request.get_json()

        if not data.get('question_type') or not data.get(
                'question_text') or not data.get('part'):
            return jsonify({'error': 'Missing required fields'}), 400

        # Get next question number
        last_q = Question.query.filter_by(
            paper_id=paper_id).order_by(
            Question.question_number.desc()).first()
        question_number = (last_q.question_number + 1) if last_q else 1

        success, result = ExamPaperService.add_question(
            paper_id=paper_id,
            question_type=data['question_type'],
            # 'multiple_choice', 'essay', 'short_answer'
            question_text=data['question_text'],
            part=data['part'],
            question_number=question_number,
            points=data.get('points'),
            created_by=get_jwt_identity(),
            choices=data.get('choices'),
            items=data.get('items'),
            answer_value=data.get(
                'answer_value') or data.get('correct_answer'),
            max_words=data.get('max_words'),
            max_chars=data.get('max_chars'),
            informatics_track=data.get('informatics_track'),
            shuffle_enabled=data.get('shuffle_enabled', True),
            subsection_id=data.get('subsection_id')
        )

        if not success:
            return jsonify({'error': result}), 400

        return jsonify(result), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@exam_bp.route('/exam-papers/questions/<int:question_id>/choices',
               methods=['POST'])
@jwt_required()
@admin_required
def add_answer_choice(question_id):
    """Add answer choice to question"""
    try:
        data = request.get_json()

        if not data.get('choice_label') or not data.get(
                'choice_text') or not data.get('display_order'):
            return jsonify({'error': 'Missing required fields'}), 400

        success, result = ExamPaperService.add_answer_choice(
            question_id=question_id,
            choice_label=data['choice_label'],
            choice_text=data['choice_text'],
            display_order=data['display_order']
        )

        if not success:
            return jsonify({'error': result}), 400

        return jsonify(result), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@exam_bp.route('/exam-papers/questions/<int:question_id>/answer',
               methods=['POST'])
@jwt_required()
@admin_required
def set_answer_key(question_id):
    """Set answer key"""
    try:
        data = request.get_json()

        if not data.get('correct_answer'):
            return jsonify({'error': 'correct_answer required'}), 400

        success, result = ExamPaperService.set_answer_key(
            question_id=question_id,
            correct_answer=data['correct_answer'],
            created_by=get_jwt_identity()
        )

        if not success:
            return jsonify({'error': result}), 400

        return jsonify(result), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# PAPER VERSION GENERATION & FINALIZATION
# ============================================================

@exam_bp.route('/exam-papers/<int:paper_id>/generate-versions',
               methods=['POST'])
@jwt_required()
@admin_required
def generate_paper_versions(paper_id):
    """Generate randomized paper versions"""
    try:
        data = request.get_json()
        num_versions = data.get('num_versions', 3)

        if num_versions < 1 or num_versions > 10:
            return jsonify({'error': 'num_versions must be 1-10'}), 400

        success, result = ExamPaperService.generate_paper_versions(
            paper_id=paper_id,
            num_versions=num_versions
        )

        if not success:
            return jsonify({'error': result}), 400

        return jsonify(result), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@exam_bp.route('/exam-papers/<int:paper_id>/finalize', methods=['POST'])
@jwt_required()
@admin_required
def finalize_exam_paper(paper_id):
    """Finalize paper (lock for editing)"""
    try:
        success, result = ExamPaperService.finalize_paper(paper_id)

        if not success:
            return jsonify({'error': result}), 400

        return jsonify(result), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# QUESTION MANAGEMENT (EDIT/DELETE)
# ============================================================

@exam_bp.route('/questions/<int:question_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_question(question_id):
    """Update question"""
    try:
        data = request.get_json()
        question = Question.query.get(question_id)

        if not question:
            return jsonify({'error': 'Question not found'}), 404

        # Update basic fields
        if 'question_text' in data:
            question.question_text = data['question_text']
        if 'points' in data:
            question.points = data['points']
        if 'max_words' in data:
            question.max_words = data['max_words']
        if 'max_chars' in data:
            question.max_chars = data['max_chars']
        if 'shuffle_enabled' in data:
            question.shuffle_enabled = data['shuffle_enabled']
        if 'subsection_id' in data:
            question.section_id = data['subsection_id']

        # Update answer (for essay/short answer)
        if 'correct_answer' in data and data['correct_answer']:
            answer = Answer.query.filter_by(question_id=question_id).first()
            if answer:
                answer.answer_value = data['correct_answer']
            else:
                answer = Answer(
                    question_id=question_id,
                    answer_value=data['correct_answer'],
                    created_by=get_jwt_identity()
                )
                db.session.add(answer)

        # Update multiple choice answers
        if 'choices' in data and question.question_type == 'multiple_choice':
            # Delete existing choices
            AnswerChoice.query.filter_by(question_id=question_id).delete()
            # Add new choices
            for choice in data['choices']:
                db.session.add(AnswerChoice(
                    question_id=question_id,
                    choice_label=choice.get('choice_label'),
                    choice_text=choice.get('choice_text'),
                    display_order=choice.get('display_order')
                ))

        # Update true/false items
        if 'items' in data and question.question_type == 'true_false':
            # Delete existing items
            QuestionItem.query.filter_by(question_id=question_id).delete()
            # Add new items
            for item in data['items']:
                db.session.add(QuestionItem(
                    question_id=question_id,
                    item_label=item.get('item_label'),
                    item_text=item.get('item_text'),
                    correct_value=item.get('correct_value'),
                    display_order=item.get('display_order')
                ))

        question.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Question updated successfully',
            'question_id': question_id
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@exam_bp.route('/questions/<int:question_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_question(question_id):
    """Delete question"""
    try:
        question = Question.query.get(question_id)

        if not question:
            return jsonify({'error': 'Question not found'}), 404

        # Prevent deletion if exam is finalized
        paper = ExamPaper.query.get(question.paper_id)
        if paper and paper.is_finalized:
            return jsonify(
                {'error': 'Cannot delete questions from finalized papers'}), 400

        paper_id = question.paper_id

        # Delete cascading: answers, choices, items
        Answer.query.filter_by(question_id=question_id).delete()
        AnswerChoice.query.filter_by(question_id=question_id).delete()
        QuestionItem.query.filter_by(question_id=question_id).delete()
        StudentResponse.query.filter_by(question_id=question_id).delete()

        # Delete question
        db.session.delete(question)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Question deleted successfully',
            'paper_id': paper_id
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# EXAM ATTEMPT & RESPONSE HANDLING
# ============================================================

@exam_bp.route('/exam-attempts/<int:attempt_id>/responses', methods=['POST'])
@jwt_required()
def submit_response(attempt_id):
    """Submit response to question"""
    try:
        data = request.get_json()

        if not data.get('question_id') or 'student_answer' not in data:
            return jsonify({'error': 'Missing required fields'}), 400

        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.is_first_login:
            return jsonify({'error': 'Password change required'}), 403

        attempt = ExamAttempt.query.get(attempt_id)
        if not attempt:
            return jsonify({'error': 'Attempt not found'}), 404

        # Verify student owns this attempt
        student = Student.query.filter_by(user_id=user_id).first()
        if not student or attempt.student_id != student.student_id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Check if still in time window
        now = datetime.utcnow()
        schedule = ExamSchedule.query.get(attempt.schedule_id)
        exam_datetime_end = attempt.end_time or datetime.combine(
            schedule.exam_date, schedule.end_time)

        if now > exam_datetime_end:
            return jsonify({'error': 'Exam time has expired'}), 400

        # Create or update response
        response = StudentResponse.query.filter_by(
            attempt_id=attempt_id,
            question_id=data['question_id']
        ).first()

        question = Question.query.get(data['question_id'])
        if not question:
            return jsonify({'error': 'Question not found'}), 404

        if data.get('selected_informatics_track') in [
                'computer_science', 'applied_informatics']:
            attempt.selected_informatics_track = data['selected_informatics_track']

        if question.question_type == 'short_answer' and not _is_valid_four_cell_answer(
                data['student_answer']):
            return jsonify(
                {'error': 'Short answer may contain only digits, minus sign, and comma, up to 4 cells'}), 400

        response_value = data['student_answer']
        if isinstance(response_value, (dict, list)):
            response_value = json.dumps(response_value, ensure_ascii=False)

        if not response:
            response = StudentResponse(
                attempt_id=attempt_id,
                question_id=data['question_id'],
                response_type=_response_type_for_question(
                    question.question_type),
                response_value=response_value)
            db.session.add(response)
        else:
            response.response_value = response_value

        response.submitted_at = now

        db.session.commit()

        return jsonify({
            'message': 'Response submitted',
            'question_id': data['question_id']
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@exam_bp.route('/exam-attempts/<int:attempt_id>/submit', methods=['POST'])
@jwt_required()
def submit_exam(attempt_id):
    """Submit exam (finalize attempt)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.is_first_login:
            return jsonify({'error': 'Password change required'}), 403

        attempt = ExamAttempt.query.get(attempt_id)
        if not attempt:
            return jsonify({'error': 'Attempt not found'}), 404

        # Verify student owns this attempt
        student = Student.query.filter_by(user_id=user_id).first()
        if not student or attempt.student_id != student.student_id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Mark as submitted
        attempt.submitted_time = datetime.utcnow()
        attempt.is_submitted = True
        attempt.status = 'completed'

        # Auto-score multiple choice
        success, score_result = ExamScoringService.auto_score_multiple_choice(
            attempt_id)
        has_essay = db.session.query(Question).join(
            StudentResponse,
            Question.question_id == StudentResponse.question_id).filter(
            StudentResponse.attempt_id == attempt_id,
            Question.question_type == 'essay').first() is not None

        if has_essay:
            _assign_essay_graders(attempt)
        elif success:
            attempt.status = 'graded'

        db.session.commit()

        return jsonify({
            'message': 'Exam submitted',
            'attempt_id': attempt_id,
            'auto_scored': success,
            'score_info': score_result if success else None,
            'requires_manual_grading': has_essay
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@exam_bp.route('/exam-attempts/<int:attempt_id>/status', methods=['GET'])
@jwt_required()
def get_attempt_status(attempt_id):
    """Get exam attempt status"""
    try:
        attempt = ExamAttempt.query.get(attempt_id)
        if not attempt:
            return jsonify({'error': 'Attempt not found'}), 404

        schedule = ExamSchedule.query.get(attempt.schedule_id)
        subject = Subject.query.get(attempt.subject_id)

        # Get response count
        response_count = StudentResponse.query.filter_by(
            attempt_id=attempt_id).count()

        # Calculate time remaining
        now = datetime.utcnow()
        exam_datetime_end = attempt.end_time or datetime.combine(
            schedule.exam_date, schedule.end_time)
        time_remaining = max(
            0, int(
                (exam_datetime_end - now).total_seconds() / 60))

        return jsonify({
            'attempt_id': attempt_id,
            'subject_name': subject.subject_name if subject else None,
            'status': attempt.status,
            'start_time': attempt.start_time.isoformat() if attempt.start_time else None,
            'submitted_time': attempt.submitted_time.isoformat() if attempt.submitted_time else None,
            'responses_submitted': response_count,
            'time_remaining_minutes': time_remaining,
            'total_score': float(attempt.total_score) if attempt.total_score else None
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _response_type_for_question(question_type):
    """Map question types to the response enum used by StudentResponse."""
    return {
        'multiple_choice': 'choice',
        'true_false': 'true_false',
        'short_answer': 'text',
        'essay': 'essay'
    }.get(question_type, 'text')


def _is_valid_four_cell_answer(value):
    value = str(value or '').strip()
    if len(value) > 4:
        return False
    return all(ch.isdigit() or ch in {'-', ','} for ch in value)


def _assign_essay_graders(attempt):
    essay_responses = db.session.query(StudentResponse).join(
        Question, StudentResponse.question_id == Question.question_id
    ).filter(
        StudentResponse.attempt_id == attempt.attempt_id,
        Question.question_type == 'essay'
    ).all()

    if not essay_responses:
        return

    teachers = Teacher.query.filter_by(approval_status='approved').all()
    eligible = [teacher.user_id for teacher in teachers if teacher.school_id !=
                attempt.student.school_id]
    if len(eligible) < 2:
        eligible = [teacher.user_id for teacher in teachers]

    for response in essay_responses:
        existing = EssayGrade.query.filter_by(
            response_id=response.response_id).count()
        if existing:
            continue
        for order, grader_id in enumerate(eligible[:2], start=1):
            db.session.add(EssayGrade(
                response_id=response.response_id,
                grader_id=grader_id,
                grading_order=order,
                is_first_grader=(order == 1),
                is_second_grader=(order == 2),
                final_status='pending'
            ))

# -----------------------------------------------------------
# SUBSECTION MANAGEMENT (PARTS)
# -----------------------------------------------------------


@exam_bp.route('/exam-papers/<int:paper_id>/subsections', methods=['POST'])
@jwt_required()
@admin_required
def add_subsection(paper_id):
    """Create a subsection"""
    try:
        data = request.get_json()
        type_key = data.get('type', 'normal')

        section_type = QuestionSectionType.query.filter_by(
            section_type_key=type_key).first()
        if not section_type:
            section_type = QuestionSectionType(
                section_type_name=type_key, section_type_key=type_key)
            db.session.add(section_type)
            db.session.commit()

        meta = {
            'part': data.get('part', 'part1'),
            'content': data.get('content', ''),
            'shuffle_questions': data.get('shuffle_questions', True),
            'shuffle_choices': data.get('shuffle_choices', True),
            'shuffle_items': data.get('shuffle_items', True)
        }

        # Get next order
        last_sec = QuestionSection.query.filter_by(
            paper_id=paper_id).order_by(
            QuestionSection.display_order.desc()).first()
        display_order = (last_sec.display_order + 1) if last_sec else 1

        section = QuestionSection(
            paper_id=paper_id,
            section_type_id=section_type.section_type_id,
            section_name=data.get('title'),
            # Lưu data xáo trộn và ngữ liệu vào description
            section_description=json.dumps(meta),
            display_order=display_order,
            created_by=get_jwt_identity()
        )
        db.session.add(section)
        db.session.commit()
        return jsonify(
            {'success': True, 'subsection_id': section.section_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@exam_bp.route('/subsections/<int:section_id>', methods=['PUT', 'DELETE'])
@jwt_required()
@admin_required
def modify_subsection(section_id):
    """Update or Delete a subsection"""
    try:
        section = QuestionSection.query.get(section_id)
        if not section:
            return jsonify({'error': 'Subsection not found'}), 404

        if request.method == 'DELETE':
            section.is_visible = False
            # Đồng thời unlink các câu hỏi khỏi section này
            Question.query.filter_by(
                section_id=section_id).update({'section_id': None})
            db.session.commit()
            return jsonify({'success': True}), 200

        # Update
        data = request.get_json()
        type_key = data.get('type', 'normal')
        section_type = QuestionSectionType.query.filter_by(
            section_type_key=type_key).first()
        if section_type:
            section.section_type_id = section_type.section_type_id

        meta = {
            'part': data.get('part', 'part1'),
            'content': data.get('content', ''),
            'shuffle_questions': data.get('shuffle_questions', True),
            'shuffle_choices': data.get('shuffle_choices', True),
            'shuffle_items': data.get('shuffle_items', True)
        }
        section.section_name = data.get('title')
        section.section_description = json.dumps(meta)

        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============================================================
# IMPORT & REORDER QUESTIONS
# ============================================================


@exam_bp.route('/exam-papers/<int:paper_id>/import-questions',
               methods=['POST'])
@jwt_required()
@admin_required
def import_questions_csv(paper_id):
    """Import câu hỏi từ file CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Không tìm thấy file'}), 400

        file = request.files['file']
        part = request.form.get('part', 'part1')
        question_type = request.form.get('question_type')

        if not question_type:
            return jsonify({'error': 'Vui lòng chọn loại câu hỏi'}), 400

        stream = io.StringIO(
            file.stream.read().decode('utf-8-sig'),
            newline=None)
        csv_data = csv.DictReader(stream, delimiter=',;')

        # Tìm số thứ tự câu hỏi lớn nhất hiện tại
        last_q = Question.query.filter_by(
            paper_id=paper_id).order_by(
            Question.question_number.desc()).first()
        current_q_num = (last_q.question_number) if last_q else 0

        imported = 0
        user_id = get_jwt_identity()

        for row in csv_data:
            current_q_num += 1
            text = row.get('NoiDung', '').strip()
            points = row.get('Diem', '0.25').strip()
            track = row.get('DinhHuong', '').strip()

            if not text:
                continue

            track_val = None
            if track.lower() in [
                'cs',
                'computer_science',
                    'khoa học máy tính']:
                track_val = 'computer_science'
            elif track.lower() in ['ict', 'applied_informatics', 'tin học ứng dụng']:
                track_val = 'applied_informatics'
            elif track.lower() in ['common', 'chung']:
                track_val = 'common'

            if question_type == 'multiple_choice':
                choices = [
                    {'label': 'A', 'text': row.get('A', '').strip()},
                    {'label': 'B', 'text': row.get('B', '').strip()},
                    {'label': 'C', 'text': row.get('C', '').strip()},
                    {'label': 'D', 'text': row.get('D', '').strip()}
                ]
                correct = row.get('DapAnDung', 'A').strip().upper()
                ExamPaperService.add_question(
                    paper_id=paper_id,
                    question_type=question_type,
                    question_text=text,
                    part=part,
                    question_number=current_q_num,
                    points=points,
                    created_by=user_id,
                    choices=choices,
                    answer_value=correct,
                    informatics_track=track_val)
                imported += 1

            elif question_type == 'true_false':
                items = [
                    {
                        'label': 'a', 'text': row.get(
                            'Y_a', '').strip(), 'correct_value': 'true' if row.get(
                            'DS_a', '').strip().lower() in [
                            'đ', 'đúng', 'true', '1'] else 'false'}, {
                        'label': 'b', 'text': row.get(
                            'Y_b', '').strip(), 'correct_value': 'true' if row.get(
                                'DS_b', '').strip().lower() in [
                                    'đ', 'đúng', 'true', '1'] else 'false'}, {
                                        'label': 'c', 'text': row.get(
                                            'Y_c', '').strip(), 'correct_value': 'true' if row.get(
                                                'DS_c', '').strip().lower() in [
                                                    'đ', 'đúng', 'true', '1'] else 'false'}, {
                                                        'label': 'd', 'text': row.get(
                                                            'Y_d', '').strip(), 'correct_value': 'true' if row.get(
                                                                'DS_d', '').strip().lower() in [
                                                                    'đ', 'đúng', 'true', '1'] else 'false'}]
                ExamPaperService.add_question(
                    paper_id=paper_id,
                    question_type=question_type,
                    question_text=text,
                    part=part,
                    question_number=current_q_num,
                    points=points,
                    created_by=user_id,
                    items=items,
                    informatics_track=track_val)
                imported += 1

            elif question_type == 'short_answer':
                correct = row.get('DapAn', '').strip()
                ExamPaperService.add_question(
                    paper_id=paper_id,
                    question_type=question_type,
                    question_text=text,
                    part=part,
                    question_number=current_q_num,
                    points=points,
                    created_by=user_id,
                    answer_value=correct,
                    informatics_track=track_val)
                imported += 1

        db.session.commit()
        return jsonify({'success': True, 'imported': imported}), 200

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@exam_bp.route('/exam-papers/<int:paper_id>/reorder', methods=['POST'])
@jwt_required()
@admin_required
def reorder_questions(paper_id):
    """Cập nhật lại số thứ tự câu hỏi dựa trên mảng ID truyền lên"""
    try:
        data = request.get_json()
        q_ids = data.get('ordered_question_ids', [])

        if not q_ids:
            return jsonify({'success': True})

        # Lấy tất cả câu hỏi của đề này
        questions = Question.query.filter(
            Question.question_id.in_(q_ids),
            Question.paper_id == paper_id
        ).all()

        q_dict = {q.question_id: q for q in questions}

        # BƯỚC 1: Đẩy tất cả question_number sang số âm để tránh lỗi Unique Constraint
        # Dùng session.no_autoflush để tránh SQLAlchemy tự động đẩy câu lệnh
        # lỗi lên DB sớm
        with db.session.no_autoflush:
            for index, qid in enumerate(q_ids, start=1):
                if qid in q_dict:
                    # Gán tạm số âm (-1, -2, -3...)
                    q_dict[qid].question_number = -index

            # Commit tạm thời trạng thái âm xuống DB
            db.session.commit()

            # BƯỚC 2: Cập nhật lại số chuẩn từ 1 -> N
            for index, qid in enumerate(q_ids, start=1):
                if qid in q_dict:
                    q_dict[qid].question_number = index

        # Commit lần cuối chốt danh sách
        db.session.commit()

        return jsonify(
            {'success': True, 'message': 'Đã cập nhật lại số thứ tự'}), 200

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
