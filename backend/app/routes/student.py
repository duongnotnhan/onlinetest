"""Student routes"""

import io
import json
import random
from datetime import datetime, timedelta
from functools import wraps

from app import db
from app.models import (Answer, AnswerChoice, ExamAttempt, ExamPaper,
                        ExamResult, ExamSchedule, ExamSession, GeneratedPaper,
                        Question, QuestionItem, QuestionSection, Student,
                        StudentResponse, StudentSubjectRegistration, Subject,
                        User)
from flask import jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from . import student_bp


def student_required(f):
    """Decorator to check if user is student"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.role != "student":
            return jsonify({"error": "Student access required"}), 403
        if user.is_first_login:
            return jsonify({"error": "Password change required"}), 403
        return f(*args, **kwargs)

    return decorated_function


@student_bp.route("/profile", methods=["GET"])
@jwt_required()
@student_required
def get_profile():
    """Get student profile"""
    try:
        user_id = get_jwt_identity()
        student = Student.query.filter_by(user_id=user_id).first()

        if not student:
            return jsonify({"error": "Student profile not found"}), 404

        return (
            jsonify(
                {
                    "student_id": student.student_id,
                    "cccd": student.cccd,
                    "full_name": student.full_name,
                    "gender": student.gender,
                    "date_of_birth": (
                        student.date_of_birth.isoformat()
                        if student.date_of_birth
                        else None
                    ),
                    "address": student.address,
                    "permanent_address": student.permanent_address,
                    "phone": student.phone,
                    "class_name": student.class_name,
                    "school_name": (
                        student.school.school_name if student.school else None
                    ),
                    "has_profile_photo": bool(student.profile_photo),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@student_bp.route("/profile/photo", methods=["GET"])
@jwt_required()
@student_required
def get_profile_photo():
    """Get current student's exam photo."""
    try:
        user_id = get_jwt_identity()
        student = Student.query.filter_by(user_id=user_id).first()
        if not student or not student.profile_photo:
            return jsonify({"error": "Photo not found"}), 404
        filename = student.profile_photo_filename or "profile.jpg"
        mimetype = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
        return send_file(io.BytesIO(student.profile_photo), mimetype=mimetype)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@student_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@student_required
def get_dashboard():
    """Student home information and personal exam schedule."""
    try:
        user_id = get_jwt_identity()
        student = Student.query.filter_by(user_id=user_id).first()
        if not student:
            return jsonify({"error": "Student not found"}), 404

        profile = {
            "student_id": student.student_id,
            "cccd": student.cccd,
            "full_name": student.full_name,
            "gender": student.gender,
            "date_of_birth": (
                student.date_of_birth.isoformat() if student.date_of_birth else None),
            "address": student.address,
            "permanent_address": student.permanent_address,
            "phone": student.phone,
            "class_name": student.class_name,
            "school_name": student.school.school_name if student.school else None,
            "has_profile_photo": bool(
                student.profile_photo),
        }

        schedules_response, status = get_exam_schedule()
        schedules = (
            schedules_response.get_json().get(
                "schedules",
                []) if status == 200 else [])

        return jsonify({"profile": profile, "schedules": schedules}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@student_bp.route("/exam-schedule", methods=["GET"])
@jwt_required()
@student_required
def get_exam_schedule():
    """Get student exam schedule"""
    try:
        user_id = get_jwt_identity()
        student = Student.query.filter_by(user_id=user_id).first()

        if not student:
            return jsonify({"error": "Student not found"}), 404

        sessions = ExamSession.query.filter_by(is_published=True).all()
        schedule_data = []

        for session in sessions:
            registrations = StudentSubjectRegistration.query.filter_by(
                student_id=student.student_id, exam_session_id=session.exam_session_id).all()

            for reg in registrations:
                schedule = ExamSchedule.query.filter_by(
                    exam_session_id=session.exam_session_id,
                    subject_id=reg.subject_id).first()

                if schedule:
                    subject = Subject.query.get(reg.subject_id)
                    attempt = ExamAttempt.query.filter_by(
                        student_id=student.student_id, schedule_id=schedule.schedule_id).first()

                    status = "upcoming"
                    score = None

                    if attempt:
                        if attempt.submitted_time:
                            status = "completed"
                            score = (
                                float(attempt.total_score)
                                if attempt.total_score is not None
                                else None
                            )
                        else:
                            status = "ongoing"

                    schedule_data.append(
                        {
                            "schedule_id": schedule.schedule_id,
                            "subject_id": subject.subject_id,
                            "subject_name": subject.subject_name,
                            "subject_code": subject.subject_code,
                            "exam_date": (
                                schedule.exam_date.isoformat()
                                if schedule.exam_date
                                else None
                            ),
                            "start_time": (
                                str(schedule.start_time)
                                if schedule.start_time
                                else None
                            ),
                            "end_time": (
                                str(schedule.end_time) if schedule.end_time else None
                            ),
                            "duration_minutes": schedule.duration_minutes,
                            "status": status,
                            "score": score,
                            "attempt_id": attempt.attempt_id if attempt else None,
                        }
                    )

        return jsonify({"schedules": schedule_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@student_bp.route("/exam-attempts/<int:schedule_id>/start", methods=["POST"])
@jwt_required()
@student_required
def start_exam(schedule_id):
    """Start exam attempt"""
    try:
        user_id = get_jwt_identity()
        student = Student.query.filter_by(user_id=user_id).first()

        schedule = ExamSchedule.query.get(schedule_id)
        if not schedule:
            return jsonify({"error": "Schedule not found"}), 404
        subject = Subject.query.get(schedule.subject_id)

        registration = StudentSubjectRegistration.query.filter_by(
            student_id=student.student_id,
            subject_id=schedule.subject_id,
            exam_session_id=schedule.exam_session_id,
        ).first()
        if not registration:
            return jsonify(
                {"error": "Student not registered for this exam"}), 403

        existing_attempt = ExamAttempt.query.filter_by(
            student_id=student.student_id, schedule_id=schedule_id
        ).first()
        if existing_attempt:
            return jsonify({"error": "Already attempted this exam"}), 400

        now = datetime.utcnow()
        exam_datetime_start = datetime.combine(
            schedule.exam_date, schedule.start_time)
        exam_datetime_end = datetime.combine(
            schedule.exam_date, schedule.end_time)

        session = ExamSession.query.get(schedule.exam_session_id)
        if session.is_locked:
            return jsonify({"error": "Exam session is locked"}), 403

        duration = subject.duration_minutes if subject else 50

        if session.session_type == "test":
            exam_datetime_end = now + timedelta(minutes=duration)
        else:
            if not (
                exam_datetime_start -
                timedelta(
                    minutes=5) <= now <= exam_datetime_end):
                return jsonify(
                    {"error": "Exam is not available at this time"}), 400

            # Sửa lỗi thời gian: Bắt đầu tính giờ từ mốc now + duration
            calculated_end_time = now + timedelta(minutes=duration)
            # Học sinh vào trễ sẽ bị thiệt thòi thời gian
            exam_datetime_end = min(calculated_end_time, exam_datetime_end)

        paper = ExamPaper.query.filter_by(
            subject_id=schedule.subject_id,
            exam_session_id=schedule.exam_session_id,
            is_finalized=True,
        ).first()
        if not paper:
            return jsonify({"error": "Exam paper not available"}), 404

        # Chọn ngẫu nhiên 1 mã đề đã sinh cho học sinh
        generated_papers = GeneratedPaper.query.filter_by(
            paper_id=paper.paper_id, is_active=True
        ).all()
        if not generated_papers:
            return jsonify({"error": "Exam paper version not available"}), 404

        generated_paper = random.choice(generated_papers)

        attempt = ExamAttempt(
            student_id=student.student_id,
            schedule_id=schedule_id,
            generated_paper_id=generated_paper.generated_paper_id,
            exam_session_id=schedule.exam_session_id,
            subject_id=schedule.subject_id,
            start_time=now,
            end_time=exam_datetime_end,
        )

        db.session.add(attempt)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Exam started",
                    "attempt_id": attempt.attempt_id,
                    "subject_name": subject.subject_name if subject else None,
                    "duration_minutes": duration,
                    "end_time": exam_datetime_end.isoformat(),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@student_bp.route("/exam-attempts/<int:attempt_id>/paper", methods=["GET"])
@jwt_required()
@student_required
def get_exam_paper(attempt_id):
    """Get exam paper for taking exam with correct structure and renumbered questions"""
    try:
        user_id = get_jwt_identity()
        student = Student.query.filter_by(user_id=user_id).first()

        attempt = ExamAttempt.query.get(attempt_id)
        if not attempt:
            return jsonify({"error": "Attempt not found"}), 404

        if attempt.student_id != student.student_id:
            return jsonify({"error": "Unauthorized"}), 403

        now = datetime.utcnow()
        schedule = ExamSchedule.query.get(attempt.schedule_id)
        exam_datetime_end = attempt.end_time or datetime.combine(
            schedule.exam_date, schedule.end_time
        )

        if now > exam_datetime_end:
            return jsonify({"error": "Exam time has expired"}), 400

        generated_paper = GeneratedPaper.query.get(attempt.generated_paper_id)
        paper = ExamPaper.query.get(generated_paper.paper_id)

        all_questions = Question.query.filter_by(
            paper_id=paper.paper_id, is_visible=True
        ).all()
        q_map = {q.question_id: q for q in all_questions}

        ordered_questions = []
        if generated_paper.question_order:
            order_data = generated_paper.question_order
            if isinstance(order_data, str):
                order_data = json.loads(order_data)

            for qid in order_data:
                if qid in q_map:
                    ordered_questions.append(q_map[qid])
        else:
            ordered_questions = all_questions

        # Fetch Subsections
        sections = QuestionSection.query.filter_by(
            paper_id=paper.paper_id, is_visible=True
        ).all()
        subsections_data = []
        for sec in sections:
            meta = {}
            if sec.section_description:
                try:
                    meta = json.loads(sec.section_description)
                except BaseException:
                    pass
            subsections_data.append(
                {
                    "subsection_id": sec.section_id,
                    "title": sec.section_name,
                    "type": (
                        sec.section_type.section_type_key
                        if sec.section_type
                        else "normal"
                    ),
                    "part": meta.get("part", "part1"),
                    "content": meta.get("content", ""),
                }
            )

        questions_data = []
        new_q_num = 1

        for q in ordered_questions:
            q_data = {
                "question_id": q.question_id,
                "question_number": new_q_num,  # Số từ 1..N
                "original_number": q.question_number,
                "text": q.question_text,
                "type": q.question_type,
                "part": q.part,
                "mappedPart": (
                    "part1"
                    if q.part == "reading"
                    else ("part2" if q.part == "writing" else q.part)
                ),
                "subsection_id": q.section_id,
                "answer_format": q.answer_format,
                "max_words": q.max_words,
                "max_chars": q.max_chars,
                "informatics_track": q.informatics_track,
                "points": float(q.points) if q.points else None,
                "choices": [],
                "items": [],
            }
            new_q_num += 1

            if q.question_type == "multiple_choice":
                choices = AnswerChoice.query.filter_by(
                    question_id=q.question_id).all()

                shuffle_choices = True
                if q.section_id:
                    sec = next(
                        (s for s in sections if s.section_id == q.section_id), None)
                    if sec and sec.section_description:
                        try:
                            meta = json.loads(sec.section_description)
                            shuffle_choices = meta.get("shuffle_choices", True)
                        except BaseException:
                            pass

                choice_list = [
                    {
                        "choice_id": c.choice_id,
                        "choice_label": c.choice_label,
                        "choice_text": c.choice_text,
                        "display_order": c.display_order,
                    }
                    for c in choices
                ]

                if shuffle_choices and paper.randomization_enabled:
                    rng = random.Random(
                        generated_paper.randomization_seed + q.question_id
                    )
                    labels = [c["choice_label"] for c in choice_list]
                    rng.shuffle(choice_list)
                    for i, c in enumerate(choice_list):
                        c["choice_label"] = (
                            labels[i] if i < len(labels) else chr(65 + i)
                        )

                q_data["choices"] = choice_list

            elif q.question_type == "true_false":
                items = (
                    QuestionItem.query.filter_by(question_id=q.question_id)
                    .order_by(QuestionItem.display_order)
                    .all()
                )

                shuffle_items = True
                if q.section_id:
                    sec = next(
                        (s for s in sections if s.section_id == q.section_id), None)
                    if sec and sec.section_description:
                        try:
                            meta = json.loads(sec.section_description)
                            shuffle_items = meta.get("shuffle_items", True)
                        except BaseException:
                            pass

                item_list = [
                    {
                        "item_id": item.item_id,
                        "item_label": item.item_label,
                        "item_text": item.item_text,
                        "display_order": item.display_order,
                    }
                    for item in items
                ]

                if shuffle_items and paper.randomization_enabled:
                    rng = random.Random(
                        generated_paper.randomization_seed + q.question_id + 1000)
                    labels = [it["item_label"] for it in item_list]
                    rng.shuffle(item_list)
                    for i, it in enumerate(item_list):
                        it["item_label"] = labels[i] if i < len(
                            labels) else chr(97 + i)

                q_data["items"] = item_list

            questions_data.append(q_data)

        time_remaining_seconds = int((exam_datetime_end - now).total_seconds())
        # Format lại mã đề 3 chữ số (VD: 1000-1 -> 001)
        display_code = generated_paper.paper_code_version.split("-")[-1]
        if display_code.isdigit():
            display_code = f"{int(display_code):03d}"
        else:
            display_code = generated_paper.paper_code_version

        # KHÔI PHỤC TIẾN TRÌNH LÀM BÀI
        saved_responses = StudentResponse.query.filter_by(
            attempt_id=attempt_id).all()
        saved_answers_dict = {}
        for r in saved_responses:
            if r.response_value is not None:
                rtype = (
                    r.response_type.name
                    if hasattr(r.response_type, "name")
                    else str(r.response_type)
                )
                if rtype == "true_false":
                    try:
                        saved_answers_dict[r.question_id] = json.loads(
                            r.response_value)
                    except BaseException:
                        saved_answers_dict[r.question_id] = r.response_value
                else:
                    if str(r.response_value) != "null":
                        saved_answers_dict[r.question_id] = r.response_value

        return (
            jsonify(
                {
                    "attempt_id": attempt_id,
                    "subject_name": Subject.query.get(attempt.subject_id).subject_name,
                    "paper_code": display_code,
                    "total_points": (
                        float(
                            paper.total_points) if paper.total_points else 10.0
                    ),
                    "reading_material": paper.reading_material,
                    # GỬI SỐ GIÂY
                    "time_remaining_seconds": max(0, time_remaining_seconds),
                    "questions": questions_data,
                    "subsections": subsections_data,
                    "saved_answers": saved_answers_dict,
                }
            ),
            200,
        )

    except Exception as e:
        import traceback

        traceback.print_exc()  # Print the exact error line to backend console just in case
        return jsonify({"error": str(e)}), 500


@student_bp.route("/exam-attempts/<int:attempt_id>/responses",
                  methods=["POST"])
@jwt_required()
def submit_response(attempt_id):
    """Submit response to question"""
    try:
        data = request.get_json()

        # Nhận ngầm tham số track nếu học sinh click chọn phần thi
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.is_first_login:
            return jsonify({"error": "Password change required"}), 403

        attempt = ExamAttempt.query.get(attempt_id)
        if not attempt:
            return jsonify({"error": "Attempt not found"}), 404

        student = Student.query.filter_by(user_id=user_id).first()
        if not student or attempt.student_id != student.student_id:
            return jsonify({"error": "Unauthorized"}), 403

        now = datetime.utcnow()
        schedule = ExamSchedule.query.get(attempt.schedule_id)
        exam_datetime_end = attempt.end_time or datetime.combine(
            schedule.exam_date, schedule.end_time
        )

        if now > exam_datetime_end:
            return jsonify({"error": "Exam time has expired"}), 400

        # Cập nhật Informatics Track nếu có gửi lên (Bất kể là câu hỏi nào)
        # Frontend gọi API này với student_answer = null chỉ để chốt track
        if "student_answer" not in data and "selected_informatics_track" not in data:
            return jsonify({"error": "Missing required fields"}), 400

        # Ghi nhận thay đổi định hướng (Track)
        # Sửa file client gọi API (Frontend) sẽ truyền lên field thứ 4 (dữ liệu
        # thô) -> cần nhận ở backend

        if data.get("selected_informatics_track") in [
            "computer_science",
            "applied_informatics",
        ]:
            attempt.selected_informatics_track = data["selected_informatics_track"]
            db.session.commit()

        # Nếu gửi lên không có question_id mà chỉ có mục đích chốt track thì
        # kết thúc sớm.
        if not data.get("question_id"):
            return jsonify({"message": "Track updated"}), 200

        # Nếu có question_id, tiến hành lưu đáp án như bình thường
        response = StudentResponse.query.filter_by(
            attempt_id=attempt_id, question_id=data["question_id"]
        ).first()
        question = Question.query.get(data["question_id"])

        if not question:
            return jsonify({"error": "Question not found"}), 404

        if question.question_type == "short_answer" and not _is_valid_four_cell_answer(
                data.get("student_answer")):
            return (
                jsonify(
                    {
                        "error": "Short answer may contain only digits, minus sign, and comma, up to 4 cells"
                    }
                ),
                400,
            )

        response_value = data.get("student_answer")
        if isinstance(response_value, (dict, list)):
            response_value = json.dumps(response_value, ensure_ascii=False)

        if not response:
            response = StudentResponse(
                attempt_id=attempt_id,
                question_id=data["question_id"],
                response_type=_response_type_for_question(
                    question.question_type),
                response_value=response_value,
            )
            db.session.add(response)
        else:
            response.response_value = response_value

        response.submitted_at = now
        db.session.commit()

        return (
            jsonify(
                {"message": "Response submitted", "question_id": data["question_id"]}
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@student_bp.route("/exam-attempts/<int:attempt_id>/submit", methods=["POST"])
@jwt_required()
def submit_exam(attempt_id):
    """Submit exam (finalize attempt)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.is_first_login:
            return jsonify({"error": "Password change required"}), 403

        attempt = ExamAttempt.query.get(attempt_id)
        if not attempt:
            return jsonify({"error": "Attempt not found"}), 404

        student = Student.query.filter_by(user_id=user_id).first()
        if not student or attempt.student_id != student.student_id:
            return jsonify({"error": "Unauthorized"}), 403

        attempt.submitted_time = datetime.utcnow()
        attempt.is_submitted = True
        attempt.status = "completed"

        # Chấm tự động toàn bộ bài
        from app.services.exam_service import ExamScoringService

        success, score_result = ExamScoringService.auto_score_multiple_choice(
            attempt_id
        )

        # Kiểm tra CÓ THỰC SỰ CÓ câu tự luận không (loại trừ dạng short_answer)
        from app.models import EssayGrade, Teacher

        # Kiểm tra xem đề bài này có chứa câu hỏi loại 'essay' không
        generated_paper = GeneratedPaper.query.get(attempt.generated_paper_id)
        has_essay = (
            Question.query.filter_by(
                paper_id=generated_paper.paper_id,
                question_type="essay",
                is_visible=True,
            ).first()
            is not None
        )

        if has_essay:
            _assign_essay_graders(attempt)
        elif success:
            attempt.status = "graded"  # Chốt luôn trạng thái graded

        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Exam submitted",
                    "attempt_id": attempt_id,
                    "auto_scored": success,
                    "score_info": score_result if success else None,
                    "requires_manual_grading": has_essay,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@student_bp.route("/exam-attempts/<int:attempt_id>/status", methods=["GET"])
@jwt_required()
def get_attempt_status(attempt_id):
    """Get exam attempt status"""
    try:
        attempt = ExamAttempt.query.get(attempt_id)
        if not attempt:
            return jsonify({"error": "Attempt not found"}), 404

        schedule = ExamSchedule.query.get(attempt.schedule_id)
        subject = Subject.query.get(attempt.subject_id)

        response_count = StudentResponse.query.filter_by(
            attempt_id=attempt_id).count()

        now = datetime.utcnow()
        exam_datetime_end = attempt.end_time or datetime.combine(
            schedule.exam_date, schedule.end_time
        )
        time_remaining = max(
            0, int(
                (exam_datetime_end - now).total_seconds() / 60))

        return (
            jsonify(
                {
                    "attempt_id": attempt_id,
                    "subject_name": subject.subject_name if subject else None,
                    "status": attempt.status,
                    "start_time": (
                        attempt.start_time.isoformat() if attempt.start_time else None
                    ),
                    "submitted_time": (
                        attempt.submitted_time.isoformat()
                        if attempt.submitted_time
                        else None
                    ),
                    "responses_submitted": response_count,
                    "time_remaining_minutes": time_remaining,
                    "total_score": (
                        float(attempt.total_score) if attempt.total_score else None
                    ),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@student_bp.route("/results", methods=["GET"])
@jwt_required()
@student_required
def get_results():
    """Get exam results"""
    try:
        user_id = get_jwt_identity()
        student = Student.query.filter_by(user_id=user_id).first()

        results = ExamResult.query.filter_by(
            student_id=student.student_id, published=True
        ).all()

        data = []
        for result in results:
            session = ExamSession.query.get(result.exam_session_id)
            subject = Subject.query.get(result.subject_id)
            data.append(
                {
                    "result_id": result.result_id,
                    "session_name": session.session_name if session else None,
                    "subject_name": subject.subject_name if subject else None,
                    "score": (
                        float(result.score)
                        if result.score or result.score == "0" or result.score == 0
                        else None
                    ),
                    "grade": result.grade,
                    "status": result.status,
                    "published_date": (
                        result.published_date.isoformat()
                        if result.published_date
                        else None
                    ),
                }
            )

        return jsonify({"results": data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _response_type_for_question(question_type):
    return {
        "multiple_choice": "choice",
        "true_false": "true_false",
        "short_answer": "text",
        "essay": "essay",
    }.get(question_type, "text")


def _is_valid_four_cell_answer(value):
    if value is None:
        return True
    value = str(value).strip()
    if len(value) > 4:
        return False
    return all(ch.isdigit() or ch in {"-", ","} for ch in value)


def _assign_essay_graders(attempt):
    from app.models import EssayGrade, Teacher, User

    essay_responses = (
        db.session.query(StudentResponse)
        .join(Question, StudentResponse.question_id == Question.question_id)
        .filter(
            StudentResponse.attempt_id == attempt.attempt_id,
            Question.question_type == "essay",
        )
        .all()
    )

    if not essay_responses:
        return

    # LẤY CHUẨN XÁC GIÁO VIÊN NGỮ VĂN ĐÃ DUYỆT (Loại trừ hoàn toàn GVQL)
    grader_teachers = Teacher.query.filter_by(
        approval_status="approved", subject_specialty="NGU_VAN_GRADER"
    ).all()

    # Ưu tiên 1: Chéo trường (Giám khảo khác trường thí sinh)
    eligible_cross_school = [
        t.user_id for t in grader_teachers if t.school_id != attempt.student.school_id]

    # Nếu không đủ 2 người chéo trường, lấy tất cả giáo viên Ngữ Văn (chấp
    # nhận chấm cùng trường)
    if len(eligible_cross_school) >= 2:
        final_eligible = eligible_cross_school
    else:
        final_eligible = [t.user_id for t in grader_teachers]

    # Nếu hệ thống thậm chí không có giáo viên Ngữ Văn nào, thì bỏ qua không
    # tạo bản ghi rác
    if not final_eligible:
        return

    for response in essay_responses:
        existing = EssayGrade.query.filter_by(
            response_id=response.response_id).count()
        if existing:
            continue

        # Gán cho tối đa 2 người đầu tiên trong danh sách đủ điều kiện
        for order, grader_id in enumerate(final_eligible[:2], start=1):
            db.session.add(
                EssayGrade(
                    response_id=response.response_id,
                    grader_id=grader_id,
                    grading_order=order,
                    is_first_grader=(order == 1),
                    is_second_grader=(order == 2),
                    final_status="pending",
                )
            )
