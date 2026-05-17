"""REST API routes for exporting system data to CSV and Excel (XLSX) formats"""
import csv
import io
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Student, ExamAttempt, Subject, ExamSession
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from . import export_bp


def get_school_id_for_user(user):
    """Helper to get school_id for the current user session"""
    return user.school_id if user else None


@export_bp.route('/<string:entity_type>/<string:export_type>', methods=['POST'])
@jwt_required()
def export_system_data(entity_type, export_type):
    """
    Export database records (students or results) directly to memory 
    and stream back as file download without saving disk files.
    
    entity_type: 'students' hoặc 'results'
    export_type: 'csv' hoặc 'xlsx'
    """
    try:
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)
        if not current_user:
            return jsonify({'error': 'Người dùng không tồn tại'}), 401
            
        school_id = get_school_id_for_user(current_user)
        req_data = request.get_json() or {}

        # ----------------------------------------------------
        # LUỒNG 1: TRÍCH XUẤT DỮ LIỆU TỪ DATABASE
        # ----------------------------------------------------
        headers = []
        data_rows = []
        filename = f"export_{entity_type}"

        if entity_type == 'students':
            headers = ['Mã Học Sinh', 'Họ và Tên', 'CCCD/Mã Định Danh', 'Giới Tính', 'Ngày Sinh', 'Lớp', 'Số Điện Thoại', 'Địa Chỉ']
            # Bộ lọc theo lớp học nếu phía Frontend gửi lên
            class_name = req_data.get('class_name')
            
            query = Student.query.filter_by(school_id=school_id)
            if class_name:
                query = query.filter_by(class_name=class_name)
                filename += f"_{class_name}"
                
            students = query.order_by(Student.class_name, Student.full_name).all()
            for s in students:
                data_rows.append([
                    s.student_code or '',
                    s.full_name or '',
                    s.cccd or '',
                    'Nam' if s.gender == 'male' else 'Nữ',
                    str(s.date_of_birth) if s.date_of_birth else '',
                    s.class_name or '',
                    s.phone or '',
                    s.address or ''
                ])

        elif entity_type == 'results':
            headers = ['Số Thứ Tự', 'Họ và Tên', 'CCCD/SBD', 'Môn Thi', 'Điểm Số Trắc Nghiệm', 'Trạng Thái']
            session_id = req_data.get('exam_session_id')
            subject_id = req_data.get('subject_id')
            
            if not session_id:
                return jsonify({'error': 'Thiếu thông tin tham số kỳ thi (exam_session_id)'}), 400

            query = ExamAttempt.query.filter_by(exam_session_id=int(session_id))
            if subject_id:
                query = query.filter_by(subject_id=int(subject_id))
                
            attempts = query.order_by(ExamAttempt.total_score.desc()).all()
            
            # Lọc danh sách theo trường của Giáo viên/Quản lý đang đăng nhập
            for idx, att in enumerate(attempts, start=1):
                student = Student.query.get(att.student_id)
                if student and student.school_id == school_id:
                    subject = Subject.query.get(att.subject_id)
                    data_rows.append([
                        idx,
                        student.full_name,
                        student.cccd,
                        subject.subject_name if subject else f"Mã môn: {att.subject_id}",
                        float(att.total_score) if att.total_score is not None else 0.0,
                        'Đã hoàn thành' if att.status in ['graded', 'completed'] else 'Chưa hoàn thành'
                    ])
            filename += f"_session_{session_id}"
        else:
            return jsonify({'error': 'Phân hệ dữ liệu (Entity) không hỗ trợ'}), 400

        # ----------------------------------------------------
        # LUỒNG 2: BIÊN DỊCH VÀ ĐÓNG GÓI ĐỊNH DẠNG FILE
        # ----------------------------------------------------
        if export_type == 'csv':
            # Tạo file CSV trong bộ nhớ đệm (StringIO)
            output = io.StringIO()
            # Sử dụng excel dialect và chèn dấu BOM để Excel hiển thị tiếng Việt không lỗi font
            output.write('\ufeff') 
            writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            
            writer.writerow(headers)
            writer.writerows(data_rows)
            
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8-sig')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f"{filename}.csv"
            )

        elif export_type == 'xlsx':
            # Tạo file Excel chất lượng cao bằng Openpyxl
            wb = Workbook()
            ws = wb.active
            ws.title = entity_type.capitalize()
            
            # Bật hiển thị lưới ô vuông (Gridlines) trực quan
            ws.views.sheetView[0].showGridLines = True
            
            # Thiết lập định dạng bảng biểu (Bảng màu tối giản, tinh gọn)
            font_header = Font(name='Segoe UI', size=11, bold=True, color='1E3A8A') # Xanh đậm tinh tế
            fill_header = PatternFill(start_color='F8FAFC', end_color='F8FAFC', fill_type='solid') # Xám nhạt dịu mắt
            font_body = Font(name='Segoe UI', size=11, bold=False, color='0F172A')
            
            thin_border = Border(
                left=Side(style='thin', color='E2E8F0'),
                right=Side(style='thin', color='E2E8F0'),
                top=Side(style='thin', color='E2E8F0'),
                bottom=Side(style='thin', color='E2E8F0')
            )
            
            # Ghi dòng tiêu đề
            ws.append(headers)
            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.font = font_header
                cell.fill = fill_header
                cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
                cell.border = thin_border
            
            # Ghi toàn bộ các dòng dữ liệu
            for r_data in data_rows:
                ws.append(r_data)
                curr_row = ws.max_row
                for col_idx in range(1, len(r_data) + 1):
                    cell = ws.cell(row=curr_row, column=col_idx)
                    cell.font = font_body
                    cell.border = thin_border
                    
                    # Tự động căn lề phải cho cột Điểm số / Số thứ tự
                    if isinstance(r_data[col_idx-1], (int, float)):
                        cell.alignment = Alignment(horizontal='right', vertical='center')
                        cell.number_format = '0.00' if isinstance(r_data[col_idx-1], float) else '0'
                    else:
                        cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            
            # Tự động tính toán và co giãn độ rộng cột dựa trên nội dung chữ dài ngắn
            for col in ws.columns:
                max_len = 0
                col_letter = col[0].column_letter
                for cell in col:
                    if cell.value:
                        max_len = max(max_len, len(str(cell.value)))
                ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
                
            # Đóng gói Bytes mượt mà để trả về stream tải xuống
            file_stream = io.BytesIO()
            wb.save(file_stream)
            file_stream.seek(0)
            
            return send_file(
                file_stream,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f"{filename}.xlsx"
            )
        else:
            return jsonify({'error': 'Định dạng tệp không được hỗ trợ (chỉ dùng csv/xlsx)'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Tiến trình trích xuất dữ liệu thất bại: {str(e)}'}), 500