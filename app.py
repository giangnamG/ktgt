from flask import Flask, request, render_template_string, render_template, send_file, redirect, url_for, flash, session
import os, random, string
import cv2
import numpy as np
from crypto import *
from db import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()  # Tạo bảng trong cơ sở dữ liệu
    migrate(db)

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

        # Truy vấn cơ sở dữ liệu để kiểm tra username
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:  # So sánh mật khẩu
            session["user"] = username
            flash("✅ Đăng nhập thành công!", "success")
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

# Route đăng ký
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

        # Kiểm tra xem username đã tồn tại chưa
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("❌ Tên người dùng đã tồn tại!", "danger")
        else:
            # Thêm người dùng vào cơ sở dữ liệu
            new_user = User(
                username=username,
                password=password,
                email=email,
                phone=phone,
                address=address,
                job=job,
                dob=datetime.strptime(dob, "%Y-%m-%d").date() if dob else None,
                hobbies=','.join(hobbies)  # Lưu hobbies dưới dạng chuỗi
            )
            db.session.add(new_user)
            db.session.commit()
            flash("✅ Đăng ký thành công! Vui lòng đăng nhập.", "success")
            return redirect(url_for("login"))

    return render_template("register.html")

# Trang hồ sơ (BẢO VỆ KHỎI SSTI)
@app.route("/profile/")
def profile():
    # if "user" not in session or session["user"] != username:
    #     flash("Bạn cần đăng nhập!", "danger")
    #     return redirect(url_for("login"))

    username = request.args.get('user', 'Anonymous')
    user = User.query.filter_by(username=username).first()
    if not user:
        user = {}
        flash("Người dùng không tồn tại!", "danger")
        # return redirect(url_for("index"))
    else:
        user = user.to_dict()

    # Safely construct the HTML template
    backup_link = (
        f"""<a href="/account/{username}/backup" class="btn btn-success">Tạo Khóa backup</a>"""
        if not user.get("is_active_backup", False)
        else ""
    )

    html_template = f"""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Hồ sơ người dùng</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        </head>
        <body class="container mt-5">
            <h2 class="text-center text-primary">👤 Hồ sơ của {username}</h2>
            <div class="profile-info">
                <p><strong>📧 Email:</strong> {user.get('email', '')}</p>
                <p><strong>📞 Số điện thoại:</strong> {user.get('phone', '')}</p>
                <p><strong>🏠 Địa chỉ:</strong> {user.get('address', '')}</p>
                <p><strong>💼 Nghề nghiệp:</strong> {user.get('job', '')}</p>
                <p><strong>🎂 Ngày sinh:</strong> {user.get('dob', '')}</p>
                <p><strong>🎯 Sở thích:</strong> {", ".join(user.get('hobbies', []))}</p>
            </div>
            {backup_link}
            <a href="/logout" class="btn btn-danger logout-btn">🔓 Đăng xuất</a>
        </body>
        </html>
    """
    return render_template_string(html_template)

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
    # Cập nhật tên ảnh đã chọn vào cơ sở dữ liệu của người dùng
    user = User.query.filter_by(username=username).first()  # Lấy người dùng từ cơ sở dữ liệu
    if not user:
        return "User not found", 404
    
    # 🖼️ Chọn ngẫu nhiên 1 ảnh trong folder
    random_image = get_random_image(COVER_IMAGE_FILEPATH)
    # print(random_image)
    # 🔑 Tạo chuỗi ngẫu nhiên 32 ký tự
    secret = generate_secret_string(32)
    
    # và sau đó nhúng secret key vừa tạo vào ảnh 
    DCT = DCTApp(
        message=secret,
        cover_image_name=random_image,
        stego_image_name=f'{username}.png'
    )
    
    user.secret_key = secret
    user.cover_image_name = random_image  # Cập nhật cover_image_name
    db.session.commit()  # Lưu thay đổi vào cơ sở dữ liệu
    
    DCT.Encode()
      # ✅ Trả về ảnh đã giấu tin để người dùng tải về
    try:
        return send_file(f'./{STEGO_IMAGE_FILEPATH}/{username}.png', as_attachment=True)
    except FileNotFoundError:
        return "Stego image not found", 404


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = "tmp/"


# Kiểm tra loại tệp có hợp lệ không
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/account/activate", methods=["GET", "POST"])
def activate():
    if request.method == 'GET':
        # Trả về trang HTML cho phép tải lên tệp
        return render_template("uploadBackUpImage.html")  # Giả sử bạn có template upload.html

    elif request.method == 'POST':
        # Nhận username từ form
        username = request.form.get('username')
        # Tìm người dùng trong cơ sở dữ liệu
        user = User.query.filter_by(username=username).first()  # Tìm người dùng theo username
        if not user:
            return 'User not found', 404  # Nếu không tìm thấy người dùng, trả về lỗi
        
        # Lấy đường dẫn cover_image_name của người dùng
        cover_image_path = user.cover_image_name
        if not cover_image_path:
            return 'Cover image not found', 404  # Nếu không có ảnh cover, trả về lỗi
        
        
        # Kiểm tra nếu có tệp được gửi
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']

        # Nếu tệp không được chọn, trả về thông báo
        if file.filename == '':
            return 'No selected file'

        # Kiểm tra tệp có hợp lệ không
        if file and allowed_file(file.filename):
            # Tạo tên tệp mới để lưu trữ
            filename = os.path.join(UPLOAD_FOLDER, file.filename)
            # Lưu tệp vào thư mục đã cấu hình
            file.save(filename)
        # DCT Decrypt to check secret_key
            secret_key = user.to_dict().get('secret_key',None)
            cover_image_name = user.to_dict().get('cover_image_name',None)
            if secret_key is None:
                return "Account is blocked !!!", 403
            
            if cover_image_name is None:
                return "This Account may not activated `backup` function"
            
            DCT = DCTApp(
                message=None,
                cover_image_name=random_image,
                stego_image_name=filename
            )
            secret_key_decoded = DCT.Decode()
            print(secret_key_decoded)
            if secret_key_decoded == secret_key:
                return """
                        <script>alert("Activate Success!!! Your old password is: <b>{}<b/>"); window.location="/login"</script>
                    """.format(user.to_dict().get('password','')), 200
            else:
                return """
                    <script>alert("Your Secret Image Seem To Be Not Matched")</script>
                    """, 403
        else:
            return 'Invalid file type. Only PNG, JPG, JPEG, GIF allowed.'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
