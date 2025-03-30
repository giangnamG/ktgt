# Sử dụng Python runtime chính thức
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Sao chép nội dung thư mục hiện tại vào thư mục /app trong container
COPY . /app

# Cập nhật pip và cài đặt các gói cần thiết từ requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose cổng 5000 để Flask có thể lắng nghe
EXPOSE 5000

# Thiết lập các biến môi trường cho Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Chạy lệnh khởi động ứng dụng Flask
CMD ["flask", "run"]
