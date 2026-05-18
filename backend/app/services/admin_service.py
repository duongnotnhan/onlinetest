"""Admin Service - Business logic for QTV operations"""

from datetime import datetime

from app import db
from app.models import (ExamAttempt, ExamResult, ExamSchedule, ExamSession,
                        MakeupRegistration, StudentResponse, Subject, Teacher,
                        User)


class AdminService:
    """Service for admin operations"""

    @staticmethod
    def get_pending_teachers(page=1, limit=20):
        """Get teachers pending approval"""
        query = Teacher.query.filter_by(approval_status="pending")
        total = query.count()
        teachers = query.paginate(page=page, per_page=limit, error_out=False)
        return total, teachers.items

    @staticmethod
    def approve_teacher(teacher_id, approved_by):
        """Approve teacher"""
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            return False, "Teacher not found"

        try:
            teacher.approval_status = "approved"
            teacher.approved_by = approved_by
            teacher.approval_date = datetime.utcnow()

            user = User.query.get(teacher.user_id)
            user.is_active = True

            db.session.commit()
            return True, "Teacher approved"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def reject_teacher(teacher_id, rejected_by, reason):
        """Reject teacher"""
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            return False, "Teacher not found"

        try:
            teacher.approval_status = "rejected"
            teacher.approved_by = rejected_by
            teacher.approval_date = datetime.utcnow()
            teacher.rejection_reason = reason

            db.session.commit()
            return True, "Teacher rejected"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def create_exam_session(
            session_name,
            session_type,
            start_date,
            end_date,
            created_by,
            description=None):
        """Create exam session"""
        try:
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
            return True, session
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def publish_exam_session(session_id, published_by):
        """Publish exam session"""
        session = ExamSession.query.get(session_id)
        if not session:
            return False, "Session not found"

        # Verify schedules exist
        schedules_count = ExamSchedule.query.filter_by(
            exam_session_id=session_id
        ).count()
        if schedules_count == 0:
            return False, "No schedules defined"

        try:
            session.is_published = True
            session.published_by = published_by
            session.published_date = datetime.utcnow()

            db.session.commit()
            return True, "Session published"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def lock_exam_session(session_id):
        """Lock exam session (after publishing results)"""
        session = ExamSession.query.get(session_id)
        if not session:
            return False, "Session not found"

        try:
            session.is_locked = True
            db.session.commit()
            return True, "Session locked"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def approve_makeup_exam(
        registration_id, scheduled_date, start_time, end_time, approved_by
    ):
        """Approve makeup exam registration"""
        registration = MakeupRegistration.query.get(registration_id)
        if not registration:
            return False, "Registration not found"

        try:
            registration.approval_status = "approved"
            registration.approved_by = approved_by
            registration.approval_date = datetime.utcnow()
            registration.scheduled_date = scheduled_date
            registration.scheduled_start_time = start_time
            registration.scheduled_end_time = end_time

            db.session.commit()
            return True, "Makeup exam approved"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def publish_results(session_id):
        """Publish exam results"""
        try:
            # Check all essays are graded
            incomplete = ExamAttempt.query.filter(
                ExamAttempt.exam_session_id == session_id,
                ExamAttempt.status != "graded",
            ).first()

            if incomplete:
                return False, "Not all exams are graded"

            attempts = ExamAttempt.query.filter_by(
                exam_session_id=session_id, status="graded"
            ).all()
            published_count = 0
            for attempt in attempts:
                result = ExamResult.query.filter_by(
                    student_id=attempt.student_id,
                    exam_session_id=session_id,
                    subject_id=attempt.subject_id,
                ).first()
                if not result:
                    result = ExamResult(
                        student_id=attempt.student_id,
                        exam_session_id=session_id,
                        subject_id=attempt.subject_id,
                    )
                    db.session.add(result)

                score = float(attempt.total_score or 0)
                result.score = score
                result.grade = _grade_from_score(score)
                result.status = "passed" if score >= 5.0 else "failed"
                result.published = True
                result.published_date = datetime.utcnow()
                published_count += 1

            # Lock session
            session = ExamSession.query.get(session_id)
            session.is_locked = True

            db.session.commit()
            return True, f"{published_count} results published"
        except Exception as e:
            db.session.rollback()
            return False, str(e)


class ExamStatisticsService:
    """Service for exam statistics and reporting"""

    @staticmethod
    def get_session_statistics(session_id):
        """Get statistics for exam session"""
        try:
            total_attempts = ExamAttempt.query.filter_by(
                exam_session_id=session_id
            ).count()
            completed = ExamAttempt.query.filter_by(
                exam_session_id=session_id, status="graded"
            ).count()
            pending_grading = ExamAttempt.query.filter_by(
                exam_session_id=session_id, status="completed"
            ).count()

            # Calculate average score
            graded = ExamAttempt.query.filter_by(
                exam_session_id=session_id, status="graded"
            ).all()

            avg_score = 0
            if graded:
                total_score = sum(float(a.total_score)
                                  if a.total_score else 0 for a in graded)
                avg_score = total_score / len(graded)

            return {
                "total_attempts": total_attempts,
                "completed": completed,
                "pending_grading": pending_grading,
                "average_score": round(avg_score, 2),
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_subject_statistics(session_id, subject_id):
        """Get statistics for specific subject in session"""
        try:
            attempts = ExamAttempt.query.filter_by(
                exam_session_id=session_id, subject_id=subject_id
            ).all()

            total = len(attempts)
            passed = sum(
                1 for a in attempts if a.total_score and float(
                    a.total_score) >= 5.0)
            failed = total - passed

            avg_score = 0
            if total > 0:
                total_score = sum(float(a.total_score)
                                  if a.total_score else 0 for a in attempts)
                avg_score = total_score / total

            return {
                "total": total,
                "passed": passed,
                "failed": failed,
                "average_score": round(avg_score, 2),
            }
        except Exception as e:
            return {"error": str(e)}


def _grade_from_score(score):
    if score >= 8.5:
        return "A"
    if score >= 7.0:
        return "B"
    if score >= 5.5:
        return "C"
    if score >= 4.0:
        return "D"
    return "F"
