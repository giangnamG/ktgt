# Sử dụng image Python chính thức
FROM python:3.10-slim

# Cài đặt các công cụ cần thiết và thư viện phụ thuộc hệ thống
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép file requirements (cài package)
COPY requirements.txt .

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Mở cổng cho ứng dụng Flask
EXPOSE 5000

# Chạy ứng dụng
CMD ["python", "app.py"]
