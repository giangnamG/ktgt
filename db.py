from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from user_data import USER_DATA
import json

db = SQLAlchemy()

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    job = db.Column(db.String(120), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    hobbies = db.Column(db.Text, nullable=True)  # Lưu chuỗi JSON cho danh sách sở thích
    avatar = db.Column(db.String(120), nullable=True)
    is_active_backup = db.Column(db.Boolean, nullable=True)
    secret_key = db.Column(db.String(120), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "job": self.job,
            "dob": self.dob.strftime("%Y-%m-%d") if self.dob else None,  # Chuyển ngày sang chuỗi
            "hobbies": self.hobbies,  # Có thể là chuỗi JSON
            "avatar": self.avatar,
            "is_active_backup": self.is_active_backup,
            "secret_key": self.secret_key
        }
        
def migrate(db):
    for username, details in USER_DATA.items():
        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"Skipping: Username '{username}' already exists.")
        else:
            # Insert new user if username does not exist
            new_user = User(
                username=username,
                password=details["password"],
                email=details["email"],
                phone=details["phone"],
                address=details["address"],
                job=details["job"],
                dob=datetime.strptime(details["dob"], "%Y-%m-%d").date() if details.get("dob") else None,
                hobbies=json.dumps(details["hobbies"]),
                avatar=details.get("avatar", "default.png"),
                is_active_backup=details.get("is_active_backup", False),
                secret_key=details.get("secret_key", "default_key")
            )
            db.session.add(new_user)
    db.session.commit()
