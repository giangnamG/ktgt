from typing import Optional

import checklib
from checklib import BaseChecker
import requests


PORT = 8000

class DCTLib:
    @property
    def host(self):
        return f'http://{self.host}:{self.port}/api'

    def __init__(self, checker: BaseChecker, port=PORT, host=None):
        self.c = checker
        self.port = port
        self.host = host or self.c.host

    def signup(self, session: requests.Session, username: str, password: str):
        
        try:
            resp = session.post(
                url=self.host + '/register',
                data=random_data_str,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                allow_redirects=False
            )
            
            self.c.assert_eq(resp.status_code, 302, 'Failed to signup')
            
            return resp.status_code == 302
        except Exception as e:
            return False
        
    def signin(self, session: requests.Session, username: str, password: str,
               status: checklib.Status = checklib.Status.MUMBLE):
        try:
            resp = session.post(
                url=self.host + '/login',
                data=f"username={username}&password={password}",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                allow_redirects=False
            )
            self.c.assert_eq(resp.status_code, 302, 'Failed to signin', status=status)
            return resp.status_code == 302
        except Exception as e:
            return False

