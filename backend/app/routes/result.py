"""Result query routes"""

from flask import request, jsonify
from datetime import datetime
from . import result_bp
from app import db
from app.models import Student, ExamResult, ExamSession, Subject, ResultQuery


@result_bp.route("/query", methods=["POST"])
def query_results():
    """Public query for exam results"""
    data = request.get_json() or {}
    required = ["cccd", "date_of_birth", "phone"]
    if not all(data.get(field) for field in required):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        date_of_birth = datetime.strptime(
            data["date_of_birth"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400

    student = Student.query.filter_by(
        cccd=data["cccd"], date_of_birth=date_of_birth, phone=data["phone"]
    ).first()

    query_log = ResultQuery(
        cccd=data["cccd"],
        date_of_birth=date_of_birth,
        phone=data["phone"],
        query_ip=request.remote_addr,
    )
    db.session.add(query_log)
    db.session.commit()

    if not student:
        return jsonify({"error": "No matching student found"}), 404

    results = ExamResult.query.filter_by(
        student_id=student.student_id, published=True
    ).all()
    payload = []
    for result in results:
        session = ExamSession.query.get(result.exam_session_id)
        subject = Subject.query.get(result.subject_id)
        payload.append(
            {
                "session_name": session.session_name if session else None,
                "subject_name": subject.subject_name if subject else None,
                "score": float(
                    result.score) if result.score is not None else None,
                "grade": result.grade,
                "status": result.status,
                "published_date": (
                    result.published_date.isoformat() if result.published_date else None),
            })

    return (
        jsonify(
            {
                "student": {
                    "cccd": student.cccd,
                    "full_name": student.full_name,
                    "date_of_birth": student.date_of_birth.isoformat(),
                    "class_name": student.class_name,
                    "school_name": (
                        student.school.school_name if student.school else None
                    ),
                },
                "results": payload,
            }
        ),
        200,
    )
