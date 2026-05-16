"""Routes initialization"""
from flask import Blueprint

# Create blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
teacher_bp = Blueprint('teacher', __name__, url_prefix='/api/teacher')
student_bp = Blueprint('student', __name__, url_prefix='/api/student')
exam_bp = Blueprint('exam', __name__, url_prefix='/api/exam')
grading_bp = Blueprint('grading', __name__, url_prefix='/api/grading')
result_bp = Blueprint('result', __name__, url_prefix='/api/results')
upload_bp = Blueprint('upload', __name__, url_prefix='/api/upload')

# Import routes
from . import auth, admin, teacher, student, exam, grading, result, upload

__all__ = ['auth_bp', 'admin_bp', 'teacher_bp', 'student_bp', 'exam_bp', 'grading_bp', 'result_bp', 'upload_bp']
