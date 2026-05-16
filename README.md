# Hệ Thống Thi Tốt Nghiệp THPT Quốc Gia

Hệ thống tạo đề, tổ chức và chấm thi mô phỏng kỳ thi tốt nghiệp THPT Quốc Gia trực tuyến.

## Yêu Cầu Hệ Thống

- Python 3.8+
- MariaDB/MySQL 5.7+
- Node.js 14+

## Cài Đặt Backend

### 1. Clone Repository

```bash
git clone https://github.com/duongnotnhan/onlinetest.git
cd onlinetest/backend
```

### 2. Tạo Môi trường ảo

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# hoặc
source venv/bin/activate  # Linux/MacOS
```

**Lưu ý: Môi trường ảo VENV phải được duy trì xuyên suốt toàn bộ các câu lệnh.**

### 3. Cài Đặt Thư Viện

```bash
pip install -r requirements.txt
```

### 4. Cấu Hình CSDL

Trước tiên, hãy đảm bảo CMD đang ở thư mục `onlinetest`.

#### Tạo CSDL trong MariaDB

```sql
CREATE DATABASE exam_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'exam_user'@'localhost' IDENTIFIED BY 'password123';
GRANT ALL PRIVILEGES ON exam_system.* TO 'exam_user'@'localhost';
FLUSH PRIVILEGES;
```

#### Chạy SQL Schema

```bash
mysql -u exam_user -p exam_system < ..\database_schema.sql
```

### 5. Cấu Hình Environment

Tại thư mục `onlinetest`, sao chép file `.env` từ `.env.example`:

```bash
cp .env.example .env
```

Chỉnh sửa `.env` với thông tin của bạn:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=exam_user
DB_PASSWORD=password123
DB_NAME=exam_system
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=jwt-secret-key-change-in-production
MAIL_SERVER= # 3 dòng dưới này không cần thiết
MAIL_PORT=587 # tính năng gửi email 
MAIL_USE_TLS=true # đang trong quá trình phát triển
```

### 6. Khởi Tạo Database

Tại thư mục `onlinetest/backend`:

```bash
flask db init
flask db migrate
flask db upgrade
flask seed-db
```

Về lại thư mục `onlinetest`, tạo tài khoản admin:

```bash
python create_admin.py
```

Thực hiện theo hướng dẫn của command prompt.

### 7. Chạy Backend

```bash
python app.py
# hoặc
flask run
```

Backend sẽ chạy tại `http://localhost:5000`

### 8. Chạy Frontend

Tại thư mục `onlinetest`, chạy:

```bash
cd frontend
npm install
npm run dev
```

Frontend sẽ chạy tại `http://localhost:3000`, nhà phát triển có thể điều chỉnh port của Frontend/Backend.

## Lưu Ý Phát Triển

### Database

- Sử dụng MariaDB 10.3+ hoặc MySQL 5.7+
- Charset: `utf8mb4_unicode_ci` cho hỗ trợ tiếng Việt

### Models

- Tất cả model kế thừa từ `db.Model`
- Sử dụng relationships để tự động xóa khi delete parent

### Logging

- Bật SQLALCHEMY_ECHO=True trong development để debug SQL

### Error Handling

- Luôn rollback transaction khi có lỗi
- Return appropriate HTTP status codes

## Maintenance

### Database Cleanup

Tại thư mục `onlinetest/backend`:

```bash
# Xóa audit logs cũ (>30 ngày)
python manage.py cleanup-logs
```
