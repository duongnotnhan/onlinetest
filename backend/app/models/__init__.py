"""Database Models"""

from app import db
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON
from werkzeug.security import generate_password_hash, check_password_hash


class Province(db.Model):
    __tablename__ = "provinces"

    province_id = db.Column(db.Integer, primary_key=True)
    province_name = db.Column(db.String(100), nullable=False, unique=True)
    province_code = db.Column(db.String(10), unique=True)
    region = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    districts = db.relationship(
        "District", backref="province", lazy="dynamic", cascade="all, delete-orphan"
    )


class District(db.Model):
    __tablename__ = "districts"

    district_id = db.Column(db.Integer, primary_key=True)
    province_id = db.Column(
        db.Integer, db.ForeignKey("provinces.province_id"), nullable=False
    )
    district_name = db.Column(db.String(100), nullable=False)
    district_code = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    schools = db.relationship("School", backref="district", lazy="dynamic")


class School(db.Model):
    __tablename__ = "schools"

    school_id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(255), nullable=False)
    district_id = db.Column(
        db.Integer, db.ForeignKey("districts.district_id"), nullable=True
    )
    province_id = db.Column(
        db.Integer, db.ForeignKey("provinces.province_id"), nullable=True
    )
    address = db.Column(db.String(500))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    users = db.relationship("User", backref="school", lazy="dynamic")
    teachers = db.relationship("Teacher", backref="school", lazy="dynamic")
    students = db.relationship("Student", backref="school", lazy="dynamic")

    province = db.relationship("Province", foreign_keys=[province_id])


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, index=True)
    email = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15))
    full_name = db.Column(db.String(255))
    role = db.Column(db.Enum("student", "teacher", "admin"), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.school_id"), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_first_login = db.Column(db.Boolean, default=True)
    two_fa_secret = db.Column(db.String(255))
    two_fa_enabled = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Teacher(db.Model):
    __tablename__ = "teachers"

    teacher_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), nullable=False, unique=True
    )
    school_id = db.Column(
        db.Integer, db.ForeignKey("schools.school_id"), nullable=False
    )
    subject_specialty = db.Column(db.String(100))
    qualification_level = db.Column(db.String(100))
    approval_status = db.Column(
        db.Enum("pending", "approved", "rejected"), default="pending"
    )
    approval_date = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id])


class Admin(db.Model):
    __tablename__ = "admins"

    admin_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), nullable=False, unique=True
    )
    permission_level = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="admin_profile")


class Student(db.Model):
    __tablename__ = "students"

    student_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), nullable=False, unique=True
    )
    school_id = db.Column(
        db.Integer, db.ForeignKey("schools.school_id"), nullable=False
    )
    student_code = db.Column(db.String(50))
    cccd = db.Column(db.String(20), nullable=False, unique=True, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.Enum("male", "female", "other"))
    date_of_birth = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(500))
    phone = db.Column(db.String(15))
    class_name = db.Column(db.String(50))
    registration_date = db.Column(db.DateTime)
    profile_photo = db.Column(db.LargeBinary)
    profile_photo_filename = db.Column(db.String(255))
    permanent_address = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="student_profile")


class Subject(db.Model):
    __tablename__ = "subjects"

    subject_id = db.Column(db.Integer, primary_key=True)
    subject_code = db.Column(db.String(20), nullable=False, unique=True)
    subject_name = db.Column(db.String(100), nullable=False, unique=True)
    group_code = db.Column(db.String(20))
    exam_type = db.Column(db.Enum("multiple_choice", "essay", "mixed"), nullable=False)
    duration_minutes = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ExamSession(db.Model):
    __tablename__ = "exam_sessions"

    exam_session_id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(255), nullable=False)
    session_type = db.Column(db.Enum("official", "test", "makeup"), default="official")
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_published = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    published_by = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    published_date = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class ExamSchedule(db.Model):
    __tablename__ = "exam_schedules"

    schedule_id = db.Column(db.Integer, primary_key=True)
    exam_session_id = db.Column(
        db.Integer, db.ForeignKey("exam_sessions.exam_session_id"), nullable=False
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.subject_id"), nullable=False
    )
    exam_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    duration_minutes = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    exam_session = db.relationship("ExamSession")
    subject = db.relationship("Subject")


class ExamPaper(db.Model):
    __tablename__ = "exam_papers"

    paper_id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.subject_id"), nullable=False
    )
    exam_session_id = db.Column(
        db.Integer, db.ForeignKey("exam_sessions.exam_session_id")
    )
    paper_code = db.Column(db.String(50), nullable=False, unique=True)
    paper_version = db.Column(db.Integer, default=1)
    total_points = db.Column(db.Numeric(5, 2), default=10.0)
    is_published = db.Column(db.Boolean, default=False)
    is_finalized = db.Column(db.Boolean, default=False)
    randomization_enabled = db.Column(db.Boolean, default=True)
    randomization_seed = db.Column(db.Integer)
    reading_material = db.Column(
        db.Text,
        nullable=True,
        comment="Shared reading material for Vietnamese Language (Ngữ Văn)",
    )
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    approval_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    subject = db.relationship("Subject")
    questions = db.relationship(
        "Question", backref="exam_paper", lazy="dynamic", cascade="all, delete-orphan"
    )


class Question(db.Model):
    __tablename__ = "questions"

    question_id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(
        db.Integer, db.ForeignKey("exam_papers.paper_id"), nullable=False
    )
    question_number = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(
        db.Enum("multiple_choice", "true_false", "short_answer", "essay"),
        nullable=False,
    )

    # CẬP NHẬT: Mở rộng Enum để hỗ trợ toàn bộ các phân vùng của Tiếng Anh
    part = db.Column(
        db.Enum(
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
        ),
        nullable=False,
    )

    points = db.Column(db.Numeric(5, 2))
    max_words = db.Column(db.Integer)
    max_chars = db.Column(db.Integer)
    answer_format = db.Column(
        db.Enum("choice", "true_false_set", "four_cell_text", "essay_text"),
        nullable=True,
    )
    informatics_track = db.Column(
        db.Enum("common", "computer_science", "applied_informatics"), nullable=True
    )
    display_order = db.Column(db.Integer)
    is_visible = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Hỗ trợ Section, Passage, Rich Text, và Media
    section_id = db.Column(
        db.Integer, db.ForeignKey("question_sections.section_id"), nullable=True
    )
    passage_id = db.Column(
        db.Integer, db.ForeignKey("question_passages.passage_id"), nullable=True
    )
    display_order_in_section = db.Column(db.Integer)
    is_rich_text = db.Column(db.Boolean, default=True)
    difficulty_level = db.Column(
        db.Enum("easy", "medium", "hard", "very_hard"), default="medium"
    )
    bloom_level = db.Column(
        db.Enum("remember", "understand", "apply", "analyze", "evaluate", "create"),
        default="understand",
    )
    estimated_time_seconds = db.Column(db.Integer, default=60)
    is_template = db.Column(db.Boolean, default=False)
    template_category = db.Column(db.String(100))

    choices = db.relationship(
        "AnswerChoice", backref="question", lazy="dynamic", cascade="all, delete-orphan"
    )
    items = db.relationship(
        "QuestionItem", backref="question", lazy="dynamic", cascade="all, delete-orphan"
    )
    answers = db.relationship(
        "Answer", backref="question", lazy="dynamic", cascade="all, delete-orphan"
    )


class AnswerChoice(db.Model):
    __tablename__ = "answer_choices"

    choice_id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(
        db.Integer, db.ForeignKey("questions.question_id"), nullable=False
    )
    choice_label = db.Column(db.String(10))
    choice_text = db.Column(db.Text)
    display_order = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Rich Text và Media
    is_rich_text = db.Column(db.Boolean, default=True)
    media_id = db.Column(
        db.Integer, db.ForeignKey("question_media.media_id"), nullable=True
    )


class QuestionItem(db.Model):
    __tablename__ = "question_items"

    item_id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(
        db.Integer, db.ForeignKey("questions.question_id"), nullable=False
    )
    item_label = db.Column(db.String(10), nullable=False)
    item_text = db.Column(db.Text)
    correct_value = db.Column(db.String(20))
    display_order = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Rich Text và Media
    is_rich_text = db.Column(db.Boolean, default=True)
    media_id = db.Column(
        db.Integer, db.ForeignKey("question_media.media_id"), nullable=True
    )


class Answer(db.Model):
    __tablename__ = "answers"

    answer_id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(
        db.Integer, db.ForeignKey("questions.question_id"), nullable=False
    )
    answer_type = db.Column(
        db.Enum("choice", "true_false", "text", "numeric"), nullable=False
    )
    answer_value = db.Column(db.String(255))
    points = db.Column(db.Numeric(5, 2))
    explanation = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Rich Text
    is_rich_text = db.Column(db.Boolean, default=True)
    explanation_html = db.Column(db.Text)


class GeneratedPaper(db.Model):
    __tablename__ = "generated_papers"

    generated_paper_id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(
        db.Integer, db.ForeignKey("exam_papers.paper_id"), nullable=False
    )
    paper_code_version = db.Column(db.String(50), nullable=False, unique=True)
    randomization_seed = db.Column(db.Integer)
    question_order = db.Column(JSON)
    generated_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)


class ExamAttempt(db.Model):
    __tablename__ = "exam_attempts"

    attempt_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.student_id"), nullable=False
    )
    schedule_id = db.Column(
        db.Integer, db.ForeignKey("exam_schedules.schedule_id"), nullable=False
    )
    generated_paper_id = db.Column(
        db.Integer, db.ForeignKey("generated_papers.generated_paper_id"), nullable=False
    )
    exam_session_id = db.Column(
        db.Integer, db.ForeignKey("exam_sessions.exam_session_id"), nullable=False
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.subject_id"), nullable=False
    )
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    submitted_time = db.Column(db.DateTime)
    is_submitted = db.Column(db.Boolean, default=False)
    total_score = db.Column(db.Numeric(5, 2))
    selected_informatics_track = db.Column(
        db.Enum("computer_science", "applied_informatics"), nullable=True
    )
    status = db.Column(
        db.Enum("ongoing", "completed", "graded", "invalid"), default="ongoing"
    )
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student")
    schedule = db.relationship("ExamSchedule")
    subject = db.relationship("Subject")
    responses = db.relationship(
        "StudentResponse",
        backref="attempt",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )


class StudentResponse(db.Model):
    __tablename__ = "student_responses"

    response_id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(
        db.Integer, db.ForeignKey("exam_attempts.attempt_id"), nullable=False
    )
    question_id = db.Column(
        db.Integer, db.ForeignKey("questions.question_id"), nullable=False
    )
    response_type = db.Column(
        db.Enum("choice", "true_false", "text", "numeric", "essay"), nullable=False
    )
    response_value = db.Column(db.Text)
    marked_correct = db.Column(db.Boolean)
    points_earned = db.Column(db.Numeric(5, 2))
    grader_notes = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime)

    question = db.relationship("Question")


class EssayGrade(db.Model):
    __tablename__ = "essay_grades"

    grade_id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(
        db.Integer, db.ForeignKey("student_responses.response_id"), nullable=False
    )
    grader_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    grading_order = db.Column(db.Integer)
    is_first_grader = db.Column(db.Boolean)
    is_second_grader = db.Column(db.Boolean)
    is_third_grader = db.Column(db.Boolean)
    score = db.Column(db.Numeric(5, 2))
    feedback = db.Column(db.Text)
    grading_date = db.Column(db.DateTime)
    final_status = db.Column(
        db.Enum("pending", "grading", "completed"), default="pending"
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    response = db.relationship("StudentResponse")
    grader = db.relationship("User")

    @property
    def attempt(self):
        return self.response.attempt if self.response else None


class MakeupRegistration(db.Model):
    __tablename__ = "makeup_registrations"

    registration_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.student_id"), nullable=False
    )
    exam_session_id = db.Column(
        db.Integer, db.ForeignKey("exam_sessions.exam_session_id"), nullable=False
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.subject_id"), nullable=False
    )
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    requested_by = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    approval_status = db.Column(
        db.Enum("pending", "approved", "rejected"), default="pending"
    )
    approved_by = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    approval_date = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    scheduled_date = db.Column(db.Date)
    scheduled_start_time = db.Column(db.Time)
    scheduled_end_time = db.Column(db.Time)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class StudentSubjectRegistration(db.Model):
    __tablename__ = "student_subject_registration"

    registration_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.student_id"), nullable=False
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.subject_id"), nullable=False
    )
    exam_session_id = db.Column(
        db.Integer, db.ForeignKey("exam_sessions.exam_session_id"), nullable=False
    )
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    registered_by = db.Column(db.Integer, db.ForeignKey("users.user_id"))


class ExamResult(db.Model):
    __tablename__ = "exam_results"

    result_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.student_id"), nullable=False
    )
    exam_session_id = db.Column(
        db.Integer, db.ForeignKey("exam_sessions.exam_session_id"), nullable=False
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.subject_id"), nullable=False
    )
    score = db.Column(db.Numeric(5, 2))
    grade = db.Column(db.String(1))
    status = db.Column(db.Enum("completed", "failed"), default="completed")
    published = db.Column(db.Boolean, default=False)
    published_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class ResultQuery(db.Model):
    __tablename__ = "result_queries"

    query_id = db.Column(db.Integer, primary_key=True)
    cccd = db.Column(db.String(20), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    query_date = db.Column(db.DateTime, default=datetime.utcnow)
    query_ip = db.Column(db.String(50))


class SpecialQuestionGroup(db.Model):
    __tablename__ = "special_question_groups"

    group_id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(
        db.Integer, db.ForeignKey("questions.question_id"), nullable=False
    )
    group_type = db.Column(
        db.Enum("common", "computer_science", "applied_informatics"), nullable=False
    )


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    action = db.Column(db.String(255), nullable=False)
    target_table = db.Column(db.String(100))
    target_id = db.Column(db.Integer)
    old_values = db.Column(JSON)
    new_values = db.Column(JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class CaptchaSession(db.Model):
    __tablename__ = "captcha_sessions"

    session_id = db.Column(db.String(255), primary_key=True)
    captcha_text = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_verified = db.Column(db.Boolean, default=False)


# ============================================================
# QUESTION SECTIONS, RICH TEXT, VÀ MEDIA
# ============================================================


class QuestionSectionType(db.Model):
    __tablename__ = "question_section_types"

    section_type_id = db.Column(db.Integer, primary_key=True)
    section_type_name = db.Column(db.String(100), nullable=False, unique=True)
    section_type_key = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sections = db.relationship(
        "QuestionSection", backref="section_type", lazy="dynamic"
    )


class QuestionSection(db.Model):
    __tablename__ = "question_sections"

    section_id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(
        db.Integer, db.ForeignKey("exam_papers.paper_id"), nullable=False
    )
    section_type_id = db.Column(
        db.Integer,
        db.ForeignKey("question_section_types.section_type_id"),
        nullable=True,
    )
    section_name = db.Column(db.String(255))
    section_description = db.Column(db.Text)
    display_order = db.Column(db.Integer, nullable=False)
    is_visible = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    exam_paper = db.relationship("ExamPaper")
    creator = db.relationship("User", foreign_keys=[created_by])
    passages = db.relationship(
        "QuestionPassage",
        backref="section",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    questions = db.relationship(
        "Question",
        backref="section",
        lazy="dynamic",
        foreign_keys="Question.section_id",
    )


class QuestionPassage(db.Model):
    __tablename__ = "question_passages"

    passage_id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(
        db.Integer, db.ForeignKey("question_sections.section_id"), nullable=True
    )
    passage_text = db.Column(db.Text, nullable=False)
    passage_title = db.Column(db.String(255))
    author_name = db.Column(db.String(255))
    source_info = db.Column(db.String(500))
    display_order = db.Column(db.Integer)
    is_visible = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    creator = db.relationship("User", foreign_keys=[created_by])
    media_items = db.relationship(
        "QuestionMedia",
        backref="passage",
        lazy="dynamic",
        foreign_keys="QuestionMedia.passage_id",
    )
    questions = db.relationship(
        "Question",
        backref="passage_ref",
        lazy="dynamic",
        foreign_keys="Question.passage_id",
    )


class QuestionMedia(db.Model):
    __tablename__ = "question_media"

    media_id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(
        db.Integer, db.ForeignKey("questions.question_id"), nullable=True
    )
    section_id = db.Column(
        db.Integer, db.ForeignKey("question_sections.section_id"), nullable=True
    )
    passage_id = db.Column(
        db.Integer, db.ForeignKey("question_passages.passage_id"), nullable=True
    )
    media_type = db.Column(
        db.Enum("image", "audio", "video", "document"), default="image"
    )
    media_filename = db.Column(db.String(500), nullable=False)
    media_path = db.Column(db.String(1000), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    alt_text = db.Column(db.Text)
    caption = db.Column(db.Text)
    display_order = db.Column(db.Integer)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    question = db.relationship(
        "Question",
        backref=db.backref("media_items", lazy="dynamic"),
        foreign_keys=[question_id],
    )
    section = db.relationship(
        "QuestionSection",
        backref=db.backref("media_items", lazy="dynamic"),
        foreign_keys=[section_id],
    )
    creator = db.relationship("User", foreign_keys=[created_by])


class MediaUploadLog(db.Model):
    __tablename__ = "media_upload_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(
        db.Integer, db.ForeignKey("question_media.media_id"), nullable=True
    )
    upload_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    original_filename = db.Column(db.String(500))
    stored_filename = db.Column(db.String(500))
    file_path = db.Column(db.String(1000))
    file_size = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    media = db.relationship("QuestionMedia")
    uploader = db.relationship("User", foreign_keys=[upload_by])


class RichTextTemplate(db.Model):
    __tablename__ = "rich_text_templates"

    template_id = db.Column(db.Integer, primary_key=True)
    template_name = db.Column(db.String(255), nullable=False)
    template_code = db.Column(db.String(100), nullable=False, unique=True)
    html_content = db.Column(db.Text, nullable=False)
    preview_text = db.Column(db.String(500))
    category = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", foreign_keys=[created_by])


class QuestionComment(db.Model):
    __tablename__ = "question_comments"

    comment_id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(
        db.Integer, db.ForeignKey("questions.question_id"), nullable=False
    )
    comment_text = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    question = db.relationship("Question", backref="comments")
    creator = db.relationship("User", foreign_keys=[created_by])


class QuestionEditHistory(db.Model):
    __tablename__ = "question_edit_history"

    history_id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(
        db.Integer, db.ForeignKey("questions.question_id"), nullable=False
    )
    edited_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    old_data = db.Column(JSON)
    new_data = db.Column(JSON)
    change_type = db.Column(db.String(50))
    edit_date = db.Column(db.DateTime, default=datetime.utcnow)

    question = db.relationship("Question", backref="edit_history")
    editor = db.relationship("User", foreign_keys=[edited_by])


class QuestionMultiSection(db.Model):
    __tablename__ = "question_multi_section"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(
        db.Integer, db.ForeignKey("questions.question_id"), nullable=False
    )
    section_id = db.Column(
        db.Integer, db.ForeignKey("question_sections.section_id"), nullable=False
    )
    display_order = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class QuestionTemplate(db.Model):
    __tablename__ = "question_templates"

    template_id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(
        db.Integer, db.ForeignKey("questions.question_id"), nullable=True
    )
    template_name = db.Column(db.String(255), nullable=False, unique=True)
    template_category = db.Column(db.String(100))
    description = db.Column(db.Text)
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.subject_id"), nullable=True
    )
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    question = db.relationship("Question", foreign_keys=[question_id])
    subject = db.relationship("Subject")
    creator = db.relationship("User", foreign_keys=[created_by])
