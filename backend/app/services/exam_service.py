"""Authentication and Exam services"""

import json
import random
from datetime import datetime, timedelta

from app import db
from app.models import (Answer, AnswerChoice, ExamAttempt, ExamPaper,
                        ExamResult, ExamSchedule, ExamSession, GeneratedPaper,
                        Question, QuestionItem, QuestionSection, Student,
                        StudentResponse, StudentSubjectRegistration, Subject,
                        User)


class AuthService:
    """Authentication service"""

    @staticmethod
    def create_user(
        username,
        password,
        email=None,
        phone=None,
        full_name=None,
        role="student",
        school_id=None,
    ):
        """Create a new user"""
        user = User(
            username=username,
            email=email,
            phone=phone,
            full_name=full_name,
            role=role,
            school_id=school_id,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        return user

    @staticmethod
    def get_user_by_username(username):
        """Get user by username"""
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        return User.query.get(user_id)

    @staticmethod
    def verify_password(user, password):
        """Verify user password"""
        return user.check_password(password)

    @staticmethod
    def change_password(user, new_password):
        """Change user password"""
        user.set_password(new_password)
        user.is_first_login = False
        db.session.commit()

    @staticmethod
    def update_last_login(user):
        """Update user last login time"""
        user.last_login = datetime.utcnow()
        db.session.commit()


class StudentService:
    """Student service"""

    @staticmethod
    def get_student_profile(student_id):
        """Get student profile"""
        return Student.query.get(student_id)

    @staticmethod
    def get_student_by_cccd(cccd):
        """Get student by CCCD"""
        return Student.query.filter_by(cccd=cccd).first()

    @staticmethod
    def get_student_exam_schedule(student_id, exam_session_id):
        """Get student exam schedule"""
        student = Student.query.get(student_id)
        if not student:
            return None

        registrations = StudentSubjectRegistration.query.filter_by(
            student_id=student_id, exam_session_id=exam_session_id
        ).all()

        schedules = []
        for reg in registrations:
            schedule = ExamSchedule.query.filter_by(
                exam_session_id=exam_session_id, subject_id=reg.subject_id
            ).first()
            if schedule:
                schedules.append(schedule)

        return schedules

    @staticmethod
    def register_student_for_exam(
        student_id, exam_session_id, subject_ids, registered_by=None
    ):
        """Register student for exam subjects"""
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
                    registered_by=registered_by,
                )
                db.session.add(registration)

        db.session.commit()


class ExamService:
    """Exam service"""

    @staticmethod
    def create_exam_session(
            session_name,
            session_type,
            start_date,
            end_date,
            created_by,
            description=None):
        """Create exam session"""
        session = ExamSession(
            session_name=session_name,
            session_type=session_type,
            start_date=start_date,
            end_date=end_date,
            created_by=created_by,
            description=description,
        )
        db.session.add(session)
        db.session.commit()
        return session

    @staticmethod
    def publish_exam_session(session_id, published_by):
        """Publish exam session"""
        session = ExamSession.query.get(session_id)
        if session:
            session.is_published = True
            session.published_by = published_by
            session.published_date = datetime.utcnow()
            db.session.commit()
            return True
        return False

    @staticmethod
    def lock_exam_session(session_id):
        """Lock exam session"""
        session = ExamSession.query.get(session_id)
        if session:
            session.is_locked = True
            db.session.commit()
            return True
        return False

    @staticmethod
    def create_exam_schedule(
        exam_session_id, subject_id, exam_date, start_time, end_time
    ):
        """Create exam schedule"""
        schedule = ExamSchedule(
            exam_session_id=exam_session_id,
            subject_id=subject_id,
            exam_date=exam_date,
            start_time=start_time,
            end_time=end_time,
        )
        db.session.add(schedule)
        db.session.commit()
        return schedule


class ResultService:
    """Result service"""

    @staticmethod
    def calculate_score(exam_attempt_id):
        """Calculate exam score"""
        attempt = ExamAttempt.query.get(exam_attempt_id)
        if not attempt:
            return None

        total_score = 0
        responses = StudentResponse.query.filter_by(
            attempt_id=exam_attempt_id).all()

        for response in responses:
            answer = Answer.query.filter_by(
                question_id=response.question_id).first()

            if answer and response.response_value == answer.answer_value:
                response.marked_correct = True
                response.points_earned = answer.points
                total_score += float(answer.points) if answer.points else 0
            else:
                response.marked_correct = False
                response.points_earned = 0

        attempt.total_score = total_score
        attempt.status = "graded"
        db.session.commit()

        return total_score

    @staticmethod
    def publish_results(exam_session_id):
        """Publish exam results"""
        attempts = ExamAttempt.query.filter_by(
            exam_session_id=exam_session_id, status="graded"
        ).all()

        for attempt in attempts:
            result = ExamResult.query.filter_by(
                student_id=attempt.student_id,
                exam_session_id=exam_session_id,
                subject_id=attempt.subject_id,
            ).first()

            if result:
                result.score = attempt.total_score
                result.published = True
                result.published_date = datetime.utcnow()
                score = float(
                    attempt.total_score) if attempt.total_score else 0
                if score >= 8.5:
                    result.grade = "A"
                elif score >= 7.0:
                    result.grade = "B"
                elif score >= 5.5:
                    result.grade = "C"
                elif score >= 4.0:
                    result.grade = "D"
                else:
                    result.grade = "F"
                result.status = "completed"

        db.session.commit()


# ============================================================
# EXAM PAPER SERVICE
# ============================================================


class ExamPaperService:
    """Service for managing exam papers"""

    SUBJECT_STRUCTURES = {
        "Toán": {
            "parts": {
                "Phần I": {"questions": 4, "points_per_q": 0.25},
                "Phần II": {"questions": 6, "points_per_q": 1.67},
                "Phần III": {"questions": 2, "points_per_q": 4.5},
            },
            "total_questions": 12,
            "total_points": 10.0,
        },
        "Vật Lí": {
            "parts": {
                "Phần I": {"questions": 4, "points_per_q": 0.25},
                "Phần II": {"questions": 6, "points_per_q": 1.0},
                "Phần III": {"questions": 8, "points_per_q": 0.25},
            },
            "total_questions": 18,
            "total_points": 10.0,
        },
        "Hóa Học": {
            "parts": {
                "Phần I": {"questions": 4, "points_per_q": 0.25},
                "Phần II": {"questions": 6, "points_per_q": 1.0},
                "Phần III": {"questions": 8, "points_per_q": 0.25},
            },
            "total_questions": 18,
            "total_points": 10.0,
        },
        "Sinh Học": {
            "parts": {
                "Phần I": {"questions": 4, "points_per_q": 0.25},
                "Phần II": {"questions": 6, "points_per_q": 1.0},
                "Phần III": {"questions": 8, "points_per_q": 0.25},
            },
            "total_questions": 18,
            "total_points": 10.0,
        },
        "Địa Lí": {
            "parts": {
                "Phần I": {"questions": 4, "points_per_q": 0.25},
                "Phần II": {"questions": 6, "points_per_q": 1.0},
                "Phần III": {"questions": 8, "points_per_q": 0.25},
            },
            "total_questions": 18,
            "total_points": 10.0,
        },
        "Lịch Sử": {
            "parts": {
                "Phần I": {"questions": 4, "points_per_q": 0.25},
                "Phần III": {"questions": 20, "points_per_q": 0.25},
            },
            "total_questions": 24,
            "total_points": 10.0,
        },
        "Giáo Dục Kinh Tế và Pháp Luật": {
            "parts": {
                "Phần I": {"questions": 4, "points_per_q": 0.25},
                "Phần III": {"questions": 20, "points_per_q": 0.25},
            },
            "total_questions": 24,
            "total_points": 10.0,
        },
        "Ngữ Văn": {
            "parts": {
                "Đọc Hiểu": {"questions": 5, "points_per_q": 0.8},
                "Viết": {"questions": 2, "points_per_q": 3.0},
            },
            "total_questions": 7,
            "total_points": 10.0,
            "note": "Viết: Câu 1 = 2 điểm, Câu 2 = 4 điểm",
        },
        # Bổ sung trọn vẹn format chuẩn hóa cho Tiếng Anh / Ngoại ngữ
        "Tiếng Anh": {
            "parts": {
                "Reading Comprehension 1": {"questions": 8, "points_per_q": 0.25},
                "Reading Comprehension 2": {"questions": 10, "points_per_q": 0.25},
                "Reading Fill in the Blank 1": {"questions": 6, "points_per_q": 0.25},
                "Reading Fill in the Blank 2": {"questions": 6, "points_per_q": 0.25},
                "Reading Fill in the Blank 3": {"questions": 5, "points_per_q": 0.25},
                "Reordering Sentences": {"questions": 5, "points_per_q": 0.25},
            },
            "total_questions": 40,
            "total_points": 10.0,
        },
        "Ngoại Ngữ": {
            "parts": {"Part 1": {"questions": 40, "points_per_q": 0.25}},
            "total_questions": 40,
            "total_points": 10.0,
        },
        "Tin Học": {
            "parts": {
                "Phần I": {"questions": 18, "points_per_q": 0.25},
                "Phần II": {"questions": 6, "points_per_q": 1.0},
            },
            "total_questions": 24,
            "total_points": 10.0,
        },
    }

    @staticmethod
    def create_exam_paper(subject_id, exam_session_id, paper_code, created_by):
        """Create exam paper for subject"""
        try:
            subject = Subject.query.get(subject_id)
            if not subject:
                return False, "Subject not found"

            existing = ExamPaper.query.filter_by(
                subject_id=subject_id, exam_session_id=exam_session_id
            ).first()

            if existing:
                return False, "Paper already exists for this subject"

            structure = ExamPaperService.SUBJECT_STRUCTURES.get(
                subject.subject_name)
            # Quét mở rộng hỗ trợ tên môn chứa từ khóa Tiếng Anh
            if not structure and "tiếng anh" in subject.subject_name.lower():
                structure = ExamPaperService.SUBJECT_STRUCTURES.get(
                    "Tiếng Anh")

            if not structure:
                structure = {
                    "parts": {
                        "Phần I": {
                            "questions": 40,
                            "points_per_q": 0.25}},
                    "total_questions": 40,
                    "total_points": 10.0,
                }

            paper = ExamPaper(
                subject_id=subject_id,
                exam_session_id=exam_session_id,
                paper_code=paper_code,
                total_points=structure["total_points"],
                created_by=created_by,
            )

            db.session.add(paper)
            db.session.commit()

            return True, {
                "paper_id": paper.paper_id,
                "subject_name": subject.subject_name,
                "total_questions": structure["total_questions"],
                "total_points": structure["total_points"],
                "parts": structure["parts"],
            }
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def add_question(
        paper_id,
        question_type,
        question_text,
        part,
        question_number,
        points=None,
        created_by=None,
        choices=None,
        items=None,
        answer_value=None,
        max_words=None,
        max_chars=None,
        informatics_track=None,
        shuffle_enabled=True,
        subsection_id=None,
    ):
        """Add question to paper"""
        try:
            paper = ExamPaper.query.get(paper_id)
            if not paper:
                return False, "Paper not found"

            if not points:
                points = _default_points_for_question(
                    paper.subject, question_type, part
                )

            normalized_part = _normalize_question_part(part)
            question = Question(
                paper_id=paper_id,
                section_id=subsection_id,
                question_type=question_type,
                question_text=question_text,
                question_number=question_number,
                part=normalized_part,
                points=points,
                max_words=max_words,
                max_chars=max_chars,
                answer_format=_answer_format_for_question(question_type),
                informatics_track=informatics_track,
                display_order=question_number,
                template_category=None if shuffle_enabled else "no_shuffle",
                created_by=created_by,
            )

            db.session.add(question)
            db.session.flush()

            if question_type == "multiple_choice":
                for idx, choice_data in enumerate(choices or [], start=1):
                    choice = AnswerChoice(
                        question_id=question.question_id,
                        choice_label=choice_data.get("choice_label")
                        or choice_data.get("label")
                        or chr(64 + idx),
                        choice_text=choice_data.get("choice_text")
                        or choice_data.get("text"),
                        display_order=choice_data.get("display_order", idx),
                    )
                    db.session.add(choice)

            if question_type == "true_false":
                for idx, item_data in enumerate(items or [], start=1):
                    item = QuestionItem(
                        question_id=question.question_id,
                        item_label=item_data.get("item_label")
                        or item_data.get("label")
                        or str(idx),
                        item_text=item_data.get("item_text") or item_data.get("text"),
                        correct_value=(
                            str(item_data.get("correct_value")).lower()
                            if item_data.get("correct_value") is not None
                            else None
                        ),
                        display_order=item_data.get("display_order", idx),
                    )
                    db.session.add(item)

            if answer_value is not None:
                answer = Answer(
                    question_id=question.question_id,
                    answer_type=_answer_type_for_question(question_type),
                    answer_value=str(answer_value),
                    points=points,
                    created_by=created_by,
                )
                db.session.add(answer)

            db.session.commit()

            return True, {
                "question_id": question.question_id,
                "question_number": question_number,
                "part": normalized_part,
                "points": points,
            }
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def add_answer_choice(
            question_id,
            choice_label,
            choice_text,
            display_order):
        """Add answer choice to question"""
        try:
            question = Question.query.get(question_id)
            if not question:
                return False, "Question not found"

            choice = AnswerChoice(
                question_id=question_id,
                choice_label=choice_label,
                choice_text=choice_text,
                display_order=display_order,
            )

            db.session.add(choice)
            db.session.commit()

            return True, {
                "choice_id": choice.choice_id,
                "choice_label": choice_label,
                "display_order": display_order,
            }
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def set_answer_key(question_id, correct_answer, created_by):
        """Set answer key for question"""
        try:
            question = Question.query.get(question_id)
            if not question:
                return False, "Question not found"

            answer = Answer.query.filter_by(question_id=question_id).first()
            if not answer:
                answer = Answer(
                    question_id=question_id,
                    answer_type=_answer_type_for_question(
                        question.question_type),
                    created_by=created_by,
                )

            answer.answer_value = correct_answer

            db.session.add(answer)
            db.session.commit()

            return True, {"question_id": question_id,
                          "correct_answer": correct_answer}
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def generate_paper_versions(paper_id, num_versions=3):
        """Generate randomized paper versions"""
        try:
            paper = ExamPaper.query.get(paper_id)
            if not paper:
                return False, "Paper not found"

            questions = Question.query.filter_by(paper_id=paper_id).all()
            if not questions:
                return False, "No questions in paper"

            sections = QuestionSection.query.filter_by(
                paper_id=paper_id, is_visible=True
            ).all()
            subsections_map = {sec.section_id: sec for sec in sections}

            questions_by_part = {}
            for q in questions:
                # Bảo toàn chuỗi định danh mã part Tiếng Anh khi trộn đề
                mapped_part = q.part
                if mapped_part == "reading":
                    mapped_part = "part1"
                elif mapped_part == "writing":
                    mapped_part = "part2"

                if mapped_part not in questions_by_part:
                    questions_by_part[mapped_part] = []
                questions_by_part[mapped_part].append(q)

            created_versions = []

            for version_num in range(num_versions):
                randomized_order = []

                # Việc sắp xếp string tự động xử lý trật tự bảng chữ cái cực kỳ khớp:
                # part1 -> part2 -> part3 HOẶC rc1 -> rc2 -> rf1 -> rf2 -> rf3
                # -> rs
                for part_name in sorted(questions_by_part.keys()):
                    part_qs = questions_by_part[part_name]

                    if (
                        paper.subject
                        and paper.subject.subject_code == "TIN_HO"
                        and part_name == "part2"
                    ):
                        tracks = {
                            "common": [],
                            "computer_science": [],
                            "applied_informatics": [],
                        }
                        for q in part_qs:
                            track = (
                                q.informatics_track if q.informatics_track else "common")
                            if track not in tracks:
                                track = "common"
                            tracks[track].append(q)

                        part_final_order = []
                        for track_name in [
                            "common",
                            "computer_science",
                            "applied_informatics",
                        ]:
                            track_qs = tracks[track_name]
                            if not track_qs:
                                continue

                            track_qs.sort(key=lambda q: q.question_number)
                            if paper.randomization_enabled:
                                movable_qs = [
                                    q
                                    for q in track_qs
                                    if q.template_category != "no_shuffle"
                                ]
                                random.shuffle(movable_qs)
                                movable_iter = iter(movable_qs)
                                track_qs = [
                                    (
                                        q
                                        if q.template_category == "no_shuffle"
                                        else next(movable_iter)
                                    )
                                    for q in track_qs
                                ]

                            part_final_order.extend(track_qs)

                        randomized_order.extend(
                            [q.question_id for q in part_final_order]
                        )
                        continue

                    blocks = {}
                    block_meta = {}

                    for q in part_qs:
                        if q.section_id:
                            b_id = f"sub_{q.section_id}"
                            if b_id not in blocks:
                                blocks[b_id] = []
                                sec = subsections_map.get(q.section_id)
                                meta = {}
                                if sec and sec.section_description:
                                    try:
                                        meta = json.loads(
                                            sec.section_description)
                                    except BaseException:
                                        pass

                                sec_type = (
                                    sec.section_type.section_type_key
                                    if sec and sec.section_type
                                    else "normal"
                                )
                                if sec_type == "reading_fill_in":
                                    meta["shuffle_questions"] = False

                                block_meta[b_id] = {
                                    "type": "subsection", "shuffle": meta.get(
                                        "shuffle_questions", True), "min_q": q.question_number, }
                            blocks[b_id].append(q)
                            block_meta[b_id]["min_q"] = min(
                                block_meta[b_id]["min_q"], q.question_number
                            )
                        else:
                            b_id = f"loose_{q.question_id}"
                            blocks[b_id] = [q]
                            block_meta[b_id] = {
                                "type": "loose",
                                "shuffle": q.template_category != "no_shuffle",
                                "min_q": q.question_number,
                            }

                    block_ids = list(blocks.keys())
                    block_ids.sort(key=lambda x, bm=block_meta: bm[x]["min_q"])

                    if paper.randomization_enabled:
                        movable_bids = [
                            bid
                            for bid in block_ids
                            if block_meta[bid]["type"] == "subsection"
                            or block_meta[bid]["shuffle"]
                        ]
                        random.shuffle(movable_bids)
                        movable_iter = iter(movable_bids)
                        shuffled_bids = [
                            (
                                bid
                                if (
                                    block_meta[bid]["type"] == "loose"
                                    and not block_meta[bid]["shuffle"]
                                )
                                else next(movable_iter)
                            )
                            for bid in block_ids
                        ]
                    else:
                        shuffled_bids = block_ids

                    part_final_order = []
                    for bid in shuffled_bids:
                        b_qs = blocks[bid]
                        if block_meta[bid]["type"] == "subsection":
                            b_qs.sort(key=lambda q: q.question_number)
                            if (
                                paper.randomization_enabled
                                and block_meta[bid]["shuffle"]
                            ):
                                movable_qs = [
                                    q
                                    for q in b_qs
                                    if q.template_category != "no_shuffle"
                                ]
                                random.shuffle(movable_qs)
                                movable_iter = iter(movable_qs)
                                b_qs = [
                                    (
                                        q
                                        if q.template_category == "no_shuffle"
                                        else next(movable_iter)
                                    )
                                    for q in b_qs
                                ]
                        part_final_order.extend(b_qs)

                    randomized_order.extend(
                        [q.question_id for q in part_final_order])

                generated = GeneratedPaper(
                    paper_id=paper_id,
                    paper_code_version=f"{paper.paper_code}-{version_num + 1}",
                    randomization_seed=random.randint(1, 999999),
                    question_order=randomized_order,
                    is_active=True,
                )
                db.session.add(generated)
                created_versions.append(generated)

            db.session.commit()
            return True, {
                "paper_id": paper_id, "versions_created": num_versions, "version_ids": [
                    v.generated_paper_id for v in created_versions], }
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def finalize_paper(paper_id):
        """Finalize paper"""
        try:
            paper = ExamPaper.query.get(paper_id)
            if not paper:
                return False, "Paper not found"

            q_count = Question.query.filter_by(paper_id=paper_id).count()
            if q_count == 0:
                return False, "Paper has no questions"

            questions_without_answers = Question.query.filter_by(
                paper_id=paper_id
            ).all()
            for q in questions_without_answers:
                answer = Answer.query.filter_by(
                    question_id=q.question_id).first()
                if not answer and q.question_type == "multiple_choice":
                    return False, f"Question {
                        q.question_number} has no answer key"
                if q.question_type == "short_answer" and not answer:
                    return False, f"Question {
                        q.question_number} has no short answer key"
                if q.question_type == "true_false" and q.items.count() != 4:
                    return False, f"Question {
                        q.question_number} must have 4 true/false items"

            versions = GeneratedPaper.query.filter_by(
                paper_id=paper_id).count()
            if versions == 0:
                return False, "Paper has no generated versions"

            paper.is_finalized = True
            db.session.commit()

            return True, {
                "paper_id": paper_id,
                "message": "Paper finalized and locked",
                "total_questions": q_count,
                "versions": versions,
            }
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def get_paper_details(paper_id):
        """Get paper details with questions and answer keys"""
        try:
            paper = ExamPaper.query.get(paper_id)
            if not paper:
                return None

            questions = Question.query.filter_by(paper_id=paper_id).all()
            versions = GeneratedPaper.query.filter_by(
                paper_id=paper_id).count()
            subject = Subject.query.get(paper.subject_id)

            sections = (
                QuestionSection.query.filter_by(
                    paper_id=paper_id,
                    is_visible=True) .order_by(
                    QuestionSection.display_order) .all())
            subsections_data = []
            for sec in sections:
                meta = {}
                try:
                    if sec.section_description:
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
                        "shuffle_questions": meta.get("shuffle_questions", True),
                        "shuffle_choices": meta.get("shuffle_choices", True),
                        "shuffle_items": meta.get("shuffle_items", True),
                    }
                )

            questions_data = []
            for q in questions:
                q_data = {
                    "question_id": q.question_id,
                    "question_number": q.question_number,
                    "part": q.part,
                    "type": q.question_type,
                    "points": float(q.points) if q.points else None,
                    "text": q.question_text,
                    "subsection_id": q.section_id,
                    "answer_format": q.answer_format,
                    "max_words": q.max_words,
                    "max_chars": q.max_chars,
                    "informatics_track": q.informatics_track,
                    "shuffle_enabled": q.template_category != "no_shuffle",
                }

                answer = Answer.query.filter_by(
                    question_id=q.question_id).first()
                if answer:
                    q_data["answer_key"] = answer.answer_value

                if q.question_type == "multiple_choice":
                    choices = AnswerChoice.query.filter_by(
                        question_id=q.question_id
                    ).all()
                    q_data["choices"] = [
                        {
                            "choice_id": c.choice_id,
                            "choice_label": c.choice_label,
                            "choice_text": c.choice_text,
                            "order": c.display_order,
                        }
                        for c in choices
                    ]
                if q.question_type == "true_false":
                    items = (
                        QuestionItem.query.filter_by(question_id=q.question_id)
                        .order_by(QuestionItem.display_order)
                        .all()
                    )
                    q_data["items"] = [
                        {
                            "item_id": item.item_id,
                            "item_label": item.item_label,
                            "item_text": item.item_text,
                            "correct_value": item.correct_value,
                            "order": item.display_order,
                        }
                        for item in items
                    ]

                questions_data.append(q_data)

            return {
                "paper_id": paper_id,
                "subject_name": subject.subject_name if subject else None,
                "paper_code": paper.paper_code,
                "total_questions": len(questions_data),
                "total_points": (
                    float(paper.total_points) if paper.total_points else 10.0
                ),
                "is_finalized": paper.is_finalized,
                "versions_count": versions,
                "reading_material": paper.reading_material,
                "subsections": subsections_data,
                "questions": questions_data,
            }
        except Exception:
            return None


class ExamScoringService:
    """Service for scoring exams"""

    @staticmethod
    def auto_score_multiple_choice(attempt_id):
        """Auto-score multiple choice questions"""
        try:
            attempt = ExamAttempt.query.get(attempt_id)
            if not attempt:
                return False, "Attempt not found"

            responses = StudentResponse.query.filter_by(
                attempt_id=attempt_id).all()

            total_score = 0
            correct_count = 0
            essay_count = 0

            for response in responses:
                question = Question.query.get(response.question_id)
                if question and question.question_type == "essay":
                    essay_count += 1
                if not question or question.question_type == "essay":
                    continue
                if _should_skip_for_informatics(attempt, question):
                    response.marked_correct = None
                    response.points_earned = 0
                    continue
                score, is_correct = _score_response(
                    attempt, question, response)
                total_score += score
                if is_correct:
                    correct_count += 1
                response.marked_correct = is_correct
                response.points_earned = score

            attempt.total_score = total_score
            attempt.status = "graded" if essay_count == 0 else "completed"
            db.session.commit()

            return True, {
                "attempt_id": attempt_id,
                "mc_score": round(total_score, 2),
                "correct_count": correct_count,
            }
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def auto_submit_overdue_exams():
        """Auto-submit exams that have passed their end time or duration"""
        try:
            now = datetime.utcnow()
            ongoing_attempts = ExamAttempt.query.filter_by(
                status="ongoing", is_submitted=0
            ).all()

            closed_count = 0
            grace_period = timedelta(minutes=2)  # additional delay

            for attempt in ongoing_attempts:
                cutoff_time = None

                if attempt.end_time:
                    cutoff_time = attempt.end_time
                elif attempt.schedule and attempt.schedule.duration_minutes:
                    cutoff_time = attempt.start_time + timedelta(
                        minutes=attempt.schedule.duration_minutes
                    )

                if cutoff_time and now > (cutoff_time + grace_period):
                    attempt.is_submitted = 1
                    attempt.submitted_time = cutoff_time

                    ExamScoringService.auto_score_multiple_choice(
                        attempt.attempt_id)
                    closed_count += 1

            if closed_count > 0:
                db.session.commit()
                print(
                    f"[System] Đã tự động thu và chấm {closed_count} bài thi quá hạn.")

            return True, closed_count
        except Exception as e:
            db.session.rollback()
            print(f"[System Error] Lỗi tiến trình tự động thu bài: {str(e)}")
            return False, str(e)


def _answer_type_for_question(question_type):
    return {
        "multiple_choice": "choice",
        "true_false": "true_false",
        "short_answer": "text",
        "essay": "text",
    }.get(question_type, "text")


def _answer_format_for_question(question_type):
    return {
        "multiple_choice": "choice",
        "true_false": "true_false_set",
        "short_answer": "four_cell_text",
        "essay": "essay_text",
    }.get(question_type)


def _normalize_question_part(part):
    part_value = (part or "").strip().lower()
    mapping = {
        "phần i": "part1",
        "phan i": "part1",
        "part 1": "part1",
        "part1": "part1",
        "phần ii": "part2",
        "phan ii": "part2",
        "part 2": "part2",
        "part2": "part2",
        "phần iii": "part3",
        "phan iii": "part3",
        "part 3": "part3",
        "part3": "part3",
        "reading": "reading",
        "writing": "writing",
        "essay": "writing",
        "rc1": "rc1",
        "rc2": "rc2",
        "rf1": "rf1",
        "rf2": "rf2",
        "rf3": "rf3",
        "rs": "rs",
    }
    allowed_parts = {
        "part1",
        "part2",
        "part3",
        "reading",
        "writing",
        "rc1",
        "rc2",
        "rf1",
        "rf2",
        "rf3",
        "rs",
    }
    return mapping.get(part_value, part if part in allowed_parts else "part1")


def _default_points_for_question(subject, question_type, part):
    normalized_part = _normalize_question_part(part)
    if question_type == "essay":
        return 1.0
    if question_type == "true_false":
        return 1.0
    if question_type == "short_answer":
        return 0.5 if subject and subject.subject_code == "TOAN" else 0.25
    if normalized_part in {"rc1", "rc2", "rf1", "rf2", "rf3", "rs"}:
        return 0.25
    if normalized_part == "part1":
        return 0.25
    return 0.25


def _should_skip_for_informatics(attempt, question):
    subject = attempt.subject
    if not subject or subject.subject_code != "TIN_HO" or question.part != "part2":
        return False
    if question.informatics_track in (None, "common"):
        return False
    if not attempt.selected_informatics_track:
        return True
    return question.informatics_track != attempt.selected_informatics_track


def _score_response(attempt, question, response):
    if (
        response.response_value is None
        or str(response.response_value).strip().lower() == "null"
    ):
        return 0, False

    if question.question_type == "multiple_choice":
        answer = Answer.query.filter_by(
            question_id=response.question_id).first()
        if not answer:
            return 0, False

        expected_label = answer.answer_value
        generated_paper = None
        if attempt.generated_paper_id:
            generated_paper = GeneratedPaper.query.get(
                attempt.generated_paper_id)
        paper = question.exam_paper

        shuffle_choices = True
        if question.section_id:
            sec = QuestionSection.query.get(question.section_id)
            if sec and sec.section_description:
                try:
                    meta = json.loads(sec.section_description)
                    shuffle_choices = meta.get("shuffle_choices", True)
                except BaseException:
                    pass

        if (
            shuffle_choices
            and paper
            and paper.randomization_enabled
            and generated_paper
        ):
            choices = AnswerChoice.query.filter_by(
                question_id=question.question_id
            ).all()
            choice_list = [{"choice_label": c.choice_label} for c in choices]

            rng = random.Random(
                generated_paper.randomization_seed + question.question_id
            )
            labels = [c["choice_label"] for c in choice_list]
            rng.shuffle(choice_list)

            for i, c in enumerate(choice_list):
                new_label = labels[i] if i < len(labels) else chr(65 + i)
                if c["choice_label"] == answer.answer_value:
                    expected_label = new_label
                    break

        is_correct = bool(
            _normalize_answer(response.response_value)
            == _normalize_answer(expected_label)
        )
        return (
            float(
                question.points or 0.25),
            True) if is_correct else (
            0,
            False)

    if question.question_type == "true_false":
        return _score_true_false(question, response.response_value)

    if question.question_type == "short_answer":
        answer = Answer.query.filter_by(
            question_id=response.question_id).first()
        is_correct = bool(
            answer
            and _normalize_short_answer(response.response_value)
            == _normalize_short_answer(answer.answer_value)
        )
        points = float(
            question.points
            or (
                0.5
                if attempt.subject and attempt.subject.subject_code == "TOAN"
                else 0.25
            )
        )
        return (points, True) if is_correct else (0, False)

    return 0, False


def _score_true_false(question, response_value):
    try:
        answers = (
            response_value
            if isinstance(response_value, dict)
            else json.loads(response_value or "{}")
        )
    except Exception:
        answers = {}

    correct = 0
    for item in question.items.all():
        submitted = answers.get(
            str(item.item_id), answers.get(item.item_label))
        if submitted is None:
            continue
        if _normalize_bool(submitted) == _normalize_bool(item.correct_value):
            correct += 1

    score_map = {1: 0.1, 2: 0.25, 3: 0.5, 4: 1.0}
    return score_map.get(correct, 0), correct == 4


def _normalize_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {
        "true", "1", "yes", "y", "đúng", "dung", "d"}


def _normalize_answer(value):
    return str(value or "").strip().upper()


def _normalize_short_answer(value):
    return str(value or "").strip().replace(" ", "").replace(".", ",")
