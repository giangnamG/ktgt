#!/usr/bin/python3

from db import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

# Thiết lập URI kết nối cơ sở dữ liệu
DATABASE_URI = 'sqlite:///instance/db.sqlite'  # hoặc thay bằng URI thật của bạn

# Thiết lập kết nối và session
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

def get_user_secret(username="admin"):
    user = session.query(User).filter_by(username=username).first()
    if not user:
        print(f"[!] User '{username}' not found.")
        return None

    return user.to_dict().get('secret_key', None)
    


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_secret.py <new_secret_key>")
        sys.exit(1)

    secret_key = sys.argv[1]

    update_user_secret(new_secret=secret_key)

    app = DCTApp(
        message=secret_key,
        cover_image_name='1002.jpg',
        stego_image_name='admin.png'
        )

    app.Encode()
    app.Decode()