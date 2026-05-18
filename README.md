# Hệ Thống Thi Tốt Nghiệp THPT Quốc Gia

[![CodeFactor](https://www.codefactor.io/repository/github/duongnotnhan/onlinetest/badge)](https://www.codefactor.io/repository/github/duongnotnhan/onlinetest)

Hệ thống tạo đề, tổ chức và chấm thi mô phỏng kỳ thi tốt nghiệp THPT Quốc Gia trực tuyến.

## Yêu Cầu Hệ Thống

- Python 3.12+ (nên sử dụng [Python 3.14](https://www.python.org/downloads/release/python-3140/) để đảm bảo tương thích với các thư viện của sản phẩm sử dụng)
- MariaDB 11.6+ ([Windows](https://mariadb.org/download/?t=mariadb&o=true&p=mariadb&r=11.6.2&os=windows&cpu=x86_64&pkg=msi&mirror=archive) | Linux/MacOS có thể cài đặt qua các bước bên dưới)
- Node.js v24+ và npm 11+ ([Windows](https://nodejs.org/dist/v24.15.0/node-v24.15.0-x64.msi) | Linux/MacOS có thể cài đặt qua các bước bên dưới)

***Các bước hướng dẫn dưới đây yêu cầu chạy trong môi trường terminal (CMD, Terminal, v.v.) và có thể khác nhau tùy vào hệ điều hành mà hệ thống sẽ được triển khai. Đối với Windows, KHÔNG sử dụng PowerShell để chạy các câu lệnh, thay vào đó hãy sử dụng CMD hoặc Windows Terminal với profile CMD.***

## Cài Đặt Frontend

### Cài Đặt Node.js và npm

- Đối với Windows, có thể sử dụng đường dẫn phía trên để tải và cài đặt Node.js, npm sẽ được cài đặt cùng Node.js (lưu ý phải đảm bảo rằng Node.js và npm được thêm vào PATH).
- Đối với Linux/MacOS, có thể sử dụng các lệnh sau để cài đặt Node.js và npm:

```bash
# Đối với Ubuntu/Debian
$ curl -sL https://deb.nodesource.com/setup_24.x | sudo -E bash -
$ apt install -y nodejs
# Đối với Fedora
$ curl -sL https://rpm.nodesource.com/setup_24.x | sudo bash -
$ dnf install -y nodejs
# Đối với MacOS
$ curl -o- https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh | bash # nếu chưa cài Homebrew
$ brew install node@24
```

Kiểm tra phiên bản Node.js và npm sau khi cài đặt:

```bash
# Xác nhận phiên bản Node.js:
node -v # "v24.x.y"
# Xác nhận phiên bản npm:
npm -v # "11.z.w"
```

## Cài Đặt Backend

**Lưu ý:** tất cả các câu lệnh xuất hiện dưới đây sẽ có thể khác nhau tùy theo hệ điều hành mà hệ thống sẽ được triển khai. Một số hướng dẫn có thể lỗi thời bởi phiên bản thư viện mà nhóm phát triển sử dụng có thể không còn mới nữa.

### 1. Clone Repository

```bash
$> git clone https://github.com/duongnotnhan/onlinetest.git
$> cd onlinetest
```

### 2. Tạo Môi trường ảo

Truy cập thư mục `backend`:

```bash
onlinetest/$> cd backend
```

Nếu máy chưa có thư viện hỗ trợ tạo môi trường ảo (`venv`), thực hiện chạy:

```bash
# Đối với Linux/MacOS
onlinetest/backend/$ sudo apt update
onlinetest/backend/$ sudo apt install python3 python3-pip python3-venv
# Đối với Windows, cài đặt Python từ trang chính thức và đảm bảo chọn tùy chọn "Add Python to PATH" trong quá trình cài đặt.
```

Tiến hành tạo và kích hoạt môi trường ảo:

```bash
# Đối với Windows
onlinetest/backend/> python -m venv myenv
onlinetest/backend/> myenv\Scripts\activate
# hoặc đối với Linux/MacOS
onlinetest/backend/$ python3 -m venv myenv
onlinetest/backend/$ source myenv/bin/activate
```

Nếu đã có môi trường ảo, hãy kích hoạt nó trước khi tiếp tục với các bước cài đặt tiếp theo chỉ bằng lệnh:

```bash
onlinetest/backend/$ source myenv/bin/activate  # Linux/MacOS
onlinetest/backend/> myenv\Scripts\activate     # Windows
```

**Lưu ý: Môi trường ảo VENV phải được duy trì xuyên suốt toàn bộ các câu lệnh.**

### 3. Cài Đặt Thư Viện

```bash
(myenv) onlinetest/backend/$ pip install -r requirements.txt
```

### 4. Cấu Hình CSDL

Trước tiên, hãy đảm bảo CMD đang ở thư mục `onlinetest`.

#### Tạo CSDL trong MariaDB

**Lưu ý trước khi chạy:** Phải đảm bảo rằng trong MariaDB của hệ thống chưa có CSDL nào tên là `exam_system`. Nếu đã tồn tại, hãy xóa hoặc thay đổi tên của CSDL hoặc người điều hành hệ thống có thể điều chỉnh để phù hợp.

Tiến hành cài đặt MariaDB nếu chưa có:

```bash
# Đối với Linux/MacOS
(myenv) onlinetest/backend/$ sudo apt update
(myenv) onlinetest/backend/$ sudo apt install mariadb-server libmysqlclient-dev
# Đối với Windows, tải và cài đặt MariaDB từ trang chính thức: https://mariadb.org/download/
```

**Lưu ý:** Sau khi cài đặt, hãy ghi nhớ mật khẩu và port đã nhập ở phần thiết lập MariaDB, vì chúng sẽ được sử dụng trong phần cấu hình environment. Nếu không có, có thể người dùng đang sử dụng cấu hình mặc định (user: root, password: rỗng, port: 3306).

```bash
# Đối với Linux/MacOS
(myenv) onlinetest/backend/$ sudo mysql
mariadb> CREATE DATABASE exam_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
mariadb> GRANT ALL PRIVILEGES ON exam_system.* TO 'exam_user'@'localhost' IDENTIFIED BY '<mariadb user password>';
mariadb> FLUSH PRIVILEGES;
mariadb> exit;
# Đối với Windows, có thể sử dụng phần mềm https://www.heidisql.com/ để sử dụng CSDL dưới người dùng root.
```

#### Chạy SQL Schema

```bash
# Đối với Linux/MacOS
(myenv) onlinetest/backend/$ cd ..
(myenv) onlinetest/$ mysql -u exam_user -p exam_system < ..\database_schema.sql
# Đối với Windows, có thể sử dụng phần mềm https://www.heidisql.com/ để nhập CSDL từ tệp database_schema.sql vào CSDL.
```

**Lưu ý:** Sau khi cài đặt CSDL, CSDL `exam_system` chỉ có chứa danh sách các tỉnh thành (sau sáp nhập), người dùng phải tự nhập danh sách phường/xã vào bảng `districts` và danh sách các trường vào bảng `schools` trong CSDL.

### 5. Cấu Hình Environment

#### Env 1

Tại thư mục `onlinetest`, sao chép file `.env` từ `.env.example`:

```bash
# Đối với Linux/MacOS
(myenv) onlinetest/$ cp .env.example .env
# hoặc đối với Windows
(myenv) onlinetest/> copy .env.example .env
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
MAIL_SERVER=      # 3 dòng dưới này không cần thiết
MAIL_PORT=587     # tính năng gửi email 
MAIL_USE_TLS=true # đang trong quá trình phát triển
```

#### Env 2

Tiến hành tương tự với `frontend`:

```bash
(myenv) onlinetest/$ cd frontend
(myenv) onlinetest/frontend/$ cp .env.example .env # Linux/MacOS
(myenv) onlinetest/frontend/> copy .env.example .env # Windows
```

Chỉnh sửa `.env` với thông tin của bạn (khuyến nghị nên giữ nguyên toàn bộ nội dung):

```env
# Frontend Environment Configuration
# Copy this to .env and adjust values as needed

# API Base URL
VITE_API_URL=/api

# App environment
VITE_ENV=development
```

#### Env 3

Nối tiếp phần lệnh trên, chạy:

```bash
(myenv) onlinetest/frontend/$ cd ../backend
(myenv) onlinetest/backend/$ cp .env.example .env # Linux/MacOS
(myenv) onlinetest/backend/> copy .env.example .env # Windows
```

Chỉnh sửa `.env` tương tự:

```env
# Thông tin truy cập vào CSDL
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=password
DB_NAME=exam_system
DB_PORT=3306

# Cấu hình Flask
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-in-production # Nên tạo một mã secret cho hai dòng này
JWT_SECRET_KEY=your-jwt-secret-key-here

# Cấu hình JWT, nên giữ nguyên
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Cấu hình máy chủ backend, nên giữ nguyên
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
DEBUG=True

# Cấu hình Email (Optional)
# Tính năng đang phát triển, chưa cần sử dụng
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Cấu hình tải file lên, nên giữ nguyên
MAX_CONTENT_LENGTH=52428800
UPLOAD_FOLDER=uploads
ALLOWED_EXTENSIONS=jpg,jpeg,png,csv,xlsx,xls

# Cấu hình 2FA, nên giữ nguyên
TWO_FA_ISSUER=ExamSystem
```

### 6. Khởi Tạo Database

Tại thư mục `onlinetest/backend`:

```bash
(myenv) onlinetest/backend/$> flask db init
(myenv) onlinetest/backend/$> flask db migrate
(myenv) onlinetest/backend/$> flask db upgrade
(myenv) onlinetest/backend/$> flask seed-db
```

Về lại thư mục `onlinetest`, tạo tài khoản admin:

```bash
(myenv) onlinetest/$> python create_admin.py
```

Thực hiện tạo tài khoản QTV theo hướng dẫn của script.

### 7. Chạy Backend

```bash
(myenv) onlinetest/backend/$> python app.py
# hoặc
(myenv) onlinetest/backend/$> flask run # không khuyến nghị sử dụng lệnh này
```

Backend sẽ chạy tại `http://localhost:5000` hoặc địa chỉ khác tùy vào cấu hình mà người dùng sử dụng.

### 8. Chạy Frontend

Nếu frontend lần đầu được chạy, tại thư mục `onlinetest`, chạy:

```bash
(myenv) onlinetest/$> cd frontend
(myenv) onlinetest/frontend/$> npm install
```

Chạy lệnh dưới đây sau khi đảm bảo các gói thư viện được cài đặt đầy đủ:

```bash
(myenv) onlinetest/frontend/$> npm run dev
```

Nếu chạy từ lần thứ hai trở đi, người dùng chỉ việc truy cập thư mục `frontend` và chạy lệnh `npm run dev` để tiến hành khởi chạy frontend.

Frontend sẽ chạy tại `http://localhost:3000`, nhà phát triển có thể điều chỉnh port của Frontend/Backend.

Frontend và backend sẽ chạy song song với nhau, người dùng có thể mở hai terminal khác nhau để chạy từng phần riêng biệt.

## Lưu Ý Phát Triển

### Cơ sở dữ liệu

- Sử dụng MariaDB 10.3+
- Charset: `utf8mb4_unicode_ci` cho hỗ trợ tiếng Việt

### Mô hình

- Tất cả mô hình kế thừa từ `db.Model`
- Sử dụng relationships để tự động xóa khi delete parent

### Nhật ký

- Bật `SQLALCHEMY_ECHO=True` trong development để debug CSDL

### Xử lý lỗi

- Luôn rollback transaction khi có lỗi
- Trả về mã lỗi HTTP

## Bảo trì

### Dọn dẹp nhật ký

Tại thư mục `onlinetest/backend`:

```bash
# Xóa audit logs cũ (>30 ngày)
(myenv) onlinetest/backend/$> python manage.py cleanup-logs
```
