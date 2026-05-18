#!/usr/bin/env python
import os

from app import create_app, db
from dotenv import load_dotenv
from flask import Flask
from flask_apscheduler import APScheduler

load_dotenv()

app = create_app(os.getenv('FLASK_ENV', 'development'))

# ==========================================
# SCHEDULER SETUP
# ==========================================
scheduler = APScheduler()
scheduler.init_app(app)


@scheduler.task('interval', id='auto_submit_overdue_job', minutes=1)
def run_auto_submit():
    with app.app_context():
        try:
            from app.services.exam_service import ExamScoringService
            ExamScoringService.auto_submit_overdue_exams()
        except Exception as e:
            print(f"[System Error] Lỗi khi chạy auto submit job: {str(e)}")


scheduler.start()
# ==========================================


@app.shell_context_processor
def make_shell_context():
    """For flask shell"""
    return {'db': db}


@app.cli.command()
def init_db():
    """Initialize database"""
    db.create_all()
    print('Database initialized.')


@app.cli.command()
def seed_db():
    """Seed database with initial data"""
    from app.models import Subject

    # Insert subjects
    subjects_data = [
        ('TOAN', 'Toán', 'group1', 'multiple_choice', 90),
        ('NVVAN', 'Ngữ Văn', 'group1', 'essay', 120),
        ('VAT_LI', 'Vật Lí', 'group2', 'multiple_choice', 50),
        ('HOA_HO', 'Hóa Học', 'group2', 'multiple_choice', 50),
        ('SINH_H', 'Sinh Học', 'group2', 'multiple_choice', 50),
        ('DIA_LI', 'Địa Lí', 'group3', 'multiple_choice', 50),
        ('LICH_S', 'Lịch Sử', 'group3', 'multiple_choice', 50),
        ('GDKTVL', 'Giáo Dục Kinh Tế và Pháp Luật', 'group3', 'multiple_choice', 50),
        ('TIN_HO', 'Tin Học', 'group4', 'multiple_choice', 50),
        ('CNNG', 'Công Nghệ Công Nghiệp', 'group5', 'multiple_choice', 50),
        ('CNNN', 'Công Nghệ Nông Nghiệp', 'group5', 'multiple_choice', 50),
        ('TIENG_ANH', 'Tiếng Anh', 'language', 'multiple_choice', 50),
        ('TIENG_RU', 'Tiếng Nga', 'language', 'multiple_choice', 50),
        ('TIENG_PH', 'Tiếng Pháp', 'language', 'multiple_choice', 50),
        ('TIENG_TR', 'Tiếng Trung', 'language', 'multiple_choice', 50),
        ('TIENG_DU', 'Tiếng Đức', 'language', 'multiple_choice', 50),
        ('TIENG_NH', 'Tiếng Nhật', 'language', 'multiple_choice', 50),
        ('TIENG_HAN', 'Tiếng Hàn', 'language', 'multiple_choice', 50),
        ('MT', 'Miễn thi', 'group0', 'multiple_choice', 0)
    ]

    for code, name, group, exam_type, duration in subjects_data:
        if not Subject.query.filter_by(subject_code=code).first():
            subject = Subject(
                subject_code=code,
                subject_name=name,
                group_code=group,
                exam_type=exam_type,
                duration_minutes=duration
            )
            db.session.add(subject)

    db.session.commit()
    print('Database seeded with subjects.')


if __name__ == '__main__':
    app.run(
        host=os.getenv('SERVER_HOST', '0.0.0.0'),
        port=int(os.getenv('SERVER_PORT', '5000')),
        debug=app.config['DEBUG'] if os.getenv('DEBUG') == 'True' else False,
        use_reloader=False
    )
