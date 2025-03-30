from flask import Flask, request, render_template_string, render_template, send_file, redirect, url_for, flash, session
import os, random, string
import cv2
import numpy as np
from user_data import USER_DATA
from crypto import *

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Thư mục lưu avatar
AVATAR_DIR = "./avatars/"

# Trang chủ
@app.route("/")
def index():
    # Lấy username từ session (nếu có)
    username = session.get("user", None)
    return render_template("index.html", username=username)

# Trang đăng nhập
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        flash("⚠️ Bạn đã đăng nhập, không thể truy cập trang đăng nhập!", "warning")
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in USER_DATA and USER_DATA[username]["password"] == password:
            session["user"] = username
            # flash("✅ Đăng nhập thành công!", "success")
            return redirect(url_for("index"))
        else:
            flash("❌ Sai username hoặc password!", "danger")

    return render_template("login.html")

# Đăng xuất
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("🚪 Đã đăng xuất!", "info")
    return redirect(url_for("login"))

# Trang đăng ký
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")
        job = request.form.get("job")
        dob = request.form.get("dob")
        hobbies = request.form.get("hobbies").split(',')

        if username in USER_DATA:
            flash("❌ Tên người dùng đã tồn tại!", "danger")
        else:
            USER_DATA[username] = {
                "password": password,
                "email": email,
                "phone": phone,
                "address": address,
                "job": job,
                "dob": dob,
                "hobbies": hobbies,
                "avatar": "default.png",  # Đặt avatar mặc định
                "secret_key": "default_key"  # Đặt secret key mặc định
            }
            flash("✅ Đăng ký thành công! Vui lòng đăng nhập.", "success")
            return redirect(url_for("login"))

    return render_template("register.html")

# Trang hồ sơ (BẢO VỆ KHỎI SSTI)
@app.route("/profile/<username>")
def profile(username):
    if "user" not in session or username not in session['user']:
        flash("Bạn cần đăng nhập!", "danger")
        return redirect(url_for("login"))

    user = USER_DATA.get(username, {})
   
    # 🔥 LỖI: `username` được truyền trực tiếp vào template!
    return render_template_string(
        f"""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Hồ sơ người dùng</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        </head>
        <body class="container mt-5">
            <h2 class="text-center text-primary">👤 Hồ sơ của { username }</h2>
            <div class="profile-info">
                <p><strong>📧 Email:</strong> { user.get('email', '') }</p>
                <p><strong>📞 Số điện thoại:</strong> { user.get('phone','') }</p>
                <p><strong>🏠 Địa chỉ:</strong> { user.get('address','') }</p>
                <p><strong>💼 Nghề nghiệp:</strong> { user.get('job', '') }</p>
                <p><strong>🎂 Ngày sinh:</strong> { user.get('dob','') }</p>
                <p><strong>🎯 Sở thích:</strong> { ", ".join(user.get('hobbies',[])) }</p>
            </div>
            """ + 
            """<a href="/account/{username}/backup" class="btn btn-success">Tạo Khóa backup</a>""" if USER_DATA[username]['is_active_backup'] == False else ''
            """
            <a href="{{ url_for('logout') }}" class="btn btn-danger logout-btn">🔓 Đăng xuất</a>
        </body>
        </html>
        """,
        username=username,  # 🛑 Đây chính là điểm gây lỗi SSTI
    )

def get_random_image(folder_path):
    # Lấy danh sách file trong folder
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]

    if not files:
        raise FileNotFoundError("❌ Không có ảnh nào trong thư mục!")

    return random.choice(files)

def generate_secret_string(length=16):
    characters = string.ascii_letters + string.digits  # Chữ hoa, chữ thường, số
    return ''.join(random.choices(characters, k=length))

# Trang active backup tài khoản
@app.route("/account/<username>/backup", methods=["GET", "POST"])
def backup_account(username):
    # 🖼️ Chọn ngẫu nhiên 1 ảnh trong folder
    random_image = get_random_image(COVER_IMAGE_FILEPATH)
    print(random_image)
    # 🔑 Tạo chuỗi ngẫu nhiên 32 ký tự
    secret = generate_secret_string(32)
    
    # và sau đó nhúng secret key vừa tạo vào ảnh 
    DCT = DCTApp(
        message=secret,
        cover_image_name=random_image,
        stego_image_name=f'{username}.png'
    )
    DCT.Encode()
      # ✅ Trả về ảnh đã giấu tin để người dùng tải về
    return send_file(f'./{STEGO_IMAGE_FILEPATH}/{username}.png', as_attachment=True)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
