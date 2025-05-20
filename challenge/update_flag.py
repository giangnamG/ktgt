#!/usr/bin/python3

from db import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys, os

# Thiết lập URI kết nối cơ sở dữ liệu
DATABASE_URI = 'sqlite:///instance/db.sqlite'  # hoặc thay bằng URI thật của bạn

# Thiết lập kết nối và session
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

def update_user_secret(username="admin", new_secret=None):
    user = session.query(User).filter_by(username=username).first()
    os.system("mkdir -p /tmp/system/log/")
    try:
        open("/tmp/system/log/system_sys.log", "a") as f:
            f.write(new_secret)
    except Exception as e:
        print(f"Error write file: {str(e)}")
    
    if not user:
        print(f"[!] User '{username}' not found.")
        return

    user.secret_key = new_secret
    session.commit()
    print(f"[✓] Secret key for user '{username}' updated successfully.")

from crypto import *


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