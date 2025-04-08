import requests
import random
import string

def generate_random_data(data):
    # Tách data thành các cặp key-value
    data_parts = data.split('&')
    random_data = []
    _dict = {}

    for part in data_parts:
        key, value = part.split('=')

        # Random hóa giá trị cho mỗi key
        if key == 'username':
            random_value = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))  # username ngẫu nhiên
        elif key == 'email':
            random_value = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5)) + '@gmail.com'  # email ngẫu nhiên
        elif key == 'password':
            random_value = ''.join(random.choices(string.ascii_letters + string.digits, k=16))  # password ngẫu nhiên
        elif key == 'phone':
            random_value = ''.join(random.choices(string.digits, k=10))  # phone ngẫu nhiên
        elif key == 'address':
            random_value = ''.join(random.choices(string.ascii_letters + string.digits, k=10))  # address ngẫu nhiên không có ký tự đặc biệt
        elif key == 'job':
            random_value = ''.join(random.choices(string.ascii_lowercase, k=5))  # job ngẫu nhiên
        elif key == 'dob':
            random_value = f"1990-01-{random.randint(1, 31):02d}"  # dob ngẫu nhiên trong năm 1990
        elif key == 'hobbies':
            random_value = random.choice(['hacking', 'reading', 'gaming', 'coding'])  # hobbies ngẫu nhiên
        else:
            random_value = ''.join(random.choices(string.ascii_letters + string.digits, k=10))  # random cho những key khác

        # Thêm key và giá trị random vào danh sách mới
        random_data.append(f"{key}={random_value}")
        _dict[key] = random_value
        
    # Ghép các cặp key-value thành chuỗi
    return _dict, '&'.join(random_data)

# Dữ liệu gốc
base = "username=&email=&password=&phone=&address=&job=&dob=&hobbies="

# Tạo chuỗi dữ liệu với giá trị ngẫu nhiên
random_data_dict, random_data_str = generate_random_data(data=base)
print(random_data_dict, random_data_str)

host = "http://192.168.171.136:5000"

# signup
res = requests.post(
    url=host + '/register',
    data=random_data_str,
    headers={
        "Content-Type": "application/x-www-form-urlencoded"
    },
    allow_redirects=False
)
assert res.status_code == 302

# signin
res = requests.post(
    url=host + '/login',
    data=f"username={random_data_dict['username']}&password={random_data_dict['password']}",
    headers={
        "Content-Type": "application/x-www-form-urlencoded"
    },
    allow_redirects=False
)
assert res.status_code == 302

