#!/usr/bin/env python3
import sys
import requests
import json
import traceback
import logging

# SỬA LỖI: Thay đổi cách import checklib
import checklib # Import module chính
from checklib import ( # Import các thành phần cần thiết từ top-level
    BaseChecker, Status, cquit, get_initialized_session,
    rnd_username, rnd_password, rnd_string
)
# ChecklibException có thể không được export trực tiếp, sẽ xử lý sau

# Token và endpoint nội bộ
CHECKER_TOKEN = "super_secret_key"
CHECKER_API_ENDPOINT = "/api/checker/allowed"
ADMIN_FLAG_ID = "admin_secret_key_v1"

# Cấu hình ghi log
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("/tmp/checker.log", mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

class FlaskStegoChecker(BaseChecker):
    vulns: int = 1
    timeout: int = 5
    uses_attack_data: bool = True
    session: requests.Session = get_initialized_session()
    
    def __init__(self, host, port, *args, **kwargs):
        super(FlaskStegoChecker, self).__init__(host, *args, **kwargs)
        self.port = port
        self.api_url = f"http://{self.host}:{self.port}{CHECKER_API_ENDPOINT}"
        self.base_url = f"http://{self.host}:{self.port}"

    def _make_api_request(self, session, action, data=None, check_response=True):
        payload = {"token": CHECKER_TOKEN, "action": action}
        if data:
            payload.update(data)

        logger.debug(f"API CALL to {self.api_url}: action={action}, data={str(data)[:50]}")
        try:
            response = session.post(self.api_url, json=payload, timeout=self.timeout)
            logger.debug(f"API RESP from {self.api_url} [{response.status_code}]: {response.text[:150]}")

            if response.status_code != 200:
                self.cquit(Status.MUMBLE, f"API Error: Status {response.status_code}", f"URL: {self.api_url}, Payload: {payload}, Response: {response.text[:100]}")

            try:
                resp_json = response.json()
            except json.JSONDecodeError:
                if response.text == '{}' and not check_response:
                    logger.warning(f"API ({self.api_url}) returned empty JSON but not checking response.")
                    return {}
                self.cquit(Status.MUMBLE, "Invalid JSON response", f"API ({self.api_url}) Raw: {response.text[:100]}")

            if check_response:
                if action == "put_secret_key" and not resp_json.get("success"):
                    msg = resp_json.get("message", "Unknown error")
                    self.cquit(Status.MUMBLE, f"Put secret key failed: {msg}", f"API ({self.api_url}) Response: {resp_json}")
                if action == "get_secret_key" and "secret_key" not in resp_json:
                    self.cquit(Status.MUMBLE, "Response missing 'secret_key'", f"API ({self.api_url}) Response: {resp_json}")
            return resp_json
        except requests.exceptions.Timeout:
            logger.error(f"API timeout after {self.timeout}s for {self.api_url}")
            self.cquit(Status.DOWN, "API request timed out", f"Timeout ({self.timeout}s) for {self.api_url}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"API connection error for {self.api_url}: {e}")
            self.cquit(Status.DOWN, "API connection error", f"URL: {self.api_url}, Error: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error during API request to {self.api_url}")
            self.cquit(Status.MUMBLE, "Unexpected API error", traceback.format_exc())

    def action(self, action_name, *args, **kwargs):
        logger.info(f"Running action: {action_name} with args: {args}")
        try:
            super().action(action_name, *args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error during action {action_name}: {e}")
            self.cquit(Status.DOWN, 'Service Connection error', str(e))
        except requests.exceptions.Timeout:
            logger.error(f"Timeout during action {action_name}")
            self.cquit(Status.DOWN, 'Service Timeout', f'Timeout ({self.timeout}s) during service interaction')

    def check(self):
        logger.info("Starting check() method")
        session = self.session
        logger.debug("Checking homepage...")
        try:
            r = session.get(f"{self.base_url}/", timeout=self.timeout)
            self.assert_eq(r.status_code, 200, "Homepage request failed")
            self.assert_in("<!DOCTYPE html>", r.text, "Homepage content invalid", status=Status.MUMBLE)
            logger.debug("Homepage OK")
        except Exception as e:
            logger.error(f"Error checking homepage: {e}")
            self.cquit(Status.DOWN, "Error accessing homepage", str(e))

        logger.debug("Attempting user registration...")
        username = rnd_username()
        password = rnd_password()
        register_data = {
            "username": username, "password": password, "email": f"{username}@ctf.io",
            "phone": rnd_string(10, '0123456789'), "address": "CTF Street", "job": "CTF Player",
            "dob": "2000-01-01", "hobbies": "pwning,reversing"
        }
        try:
            r = session.post(f"{self.base_url}/register", data=register_data, timeout=self.timeout, allow_redirects=False)
            self.assert_eq(r.status_code, 302, "Registration request did not redirect", status=Status.MUMBLE)
            self.assert_in("/login", r.headers.get("Location", ""), "Registration redirected to wrong page", status=Status.MUMBLE)
            logger.debug(f"Registration OK for user {username}")
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            self.cquit(Status.MUMBLE, "Error during user registration", str(e))

        logger.debug(f"Attempting login for user {username}...")
        try:
            r = session.post(f"{self.base_url}/login", data={"username": username, "password": password}, timeout=self.timeout, allow_redirects=False)
            self.assert_eq(r.status_code, 302, "Login request did not redirect", status=Status.MUMBLE)
            location = r.headers.get("Location", "")
            is_redirect_ok = location == "/" or location.endswith(f"{self.base_url}/") # Flask thường redirect về /
            self.assert_eq(is_redirect_ok, True, f"Login redirected to unexpected page: '{location}'", status=Status.MUMBLE)
            self.assert_in("session", session.cookies, "Session cookie not set after login", status=Status.MUMBLE)
            logger.debug(f"Login OK for user {username}")
        except Exception as e:
            logger.error(f"Error during login: {e}")
            self.cquit(Status.MUMBLE, "Error during user login", str(e))

        logger.info("check() method completed successfully")
        self.cquit(Status.OK)

    def put(self, flag_id: str, flag: str, vuln: str):
        logger.info(f"Starting put(): flag_id={flag_id}, flag='{flag[:10]}...', vuln={vuln}")
        session = self.session
        self._make_api_request(session, "put_secret_key", data={"new_flag": flag})
        logger.debug("put_secret_key API call finished. Now verifying...")
        result = self._make_api_request(session, "get_secret_key")
        retrieved_flag = result.get("secret_key")
        self.assert_eq(retrieved_flag, flag, "Flag put/get mismatch after storing", status=Status.MUMBLE)
        logger.info(f"Flag '{flag[:10]}...' stored and verified successfully.")
        self.cquit(Status.OK, ADMIN_FLAG_ID, f"Flag stored: {flag[:15]}...")

    def get(self, flag_id: str, flag: str, vuln: str):
        logger.info(f"Starting get(): flag_id='{flag_id}', expected_flag='{flag[:10]}...', vuln={vuln}")
        session = self.session
        result = self._make_api_request(session, "get_secret_key")
        retrieved_flag = result.get("secret_key")
        if retrieved_flag is None:
            self.cquit(Status.CORRUPT, "Retrieved flag is None", f"API response for get_secret_key did not contain 'secret_key'. Response: {result}")
        self.assert_eq(retrieved_flag, flag, "Retrieved flag does not match expected flag", status=Status.CORRUPT)
        logger.info(f"Flag '{flag[:10]}...' validated successfully.")
        self.cquit(Status.OK)

# --- ENTRYPOINT ---
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <check|put|get> <host[:port]> [args...]", file=sys.stderr)
        # SỬA LỖI: Sử dụng hằng số từ checklib nếu có, hoặc mã số
        sys.exit(checklib.VERDICT_CHECKER_ERROR if hasattr(checklib, 'VERDICT_CHECKER_ERROR') else 101)


    host_arg = sys.argv[2]
    try:
        if ':' in host_arg:
            host, port_str = host_arg.rsplit(':', 1)
            port = int(port_str)
        else:
            host = host_arg
            port = 5000
            logger.warning(f"Port not specified in host argument '{host_arg}', defaulting to {port}")
    except ValueError:
        logger.error(f"Invalid port number in host argument: {host_arg}")
        sys.exit(checklib.VERDICT_CHECKER_ERROR if hasattr(checklib, 'VERDICT_CHECKER_ERROR') else 101)

    checker = FlaskStegoChecker(host, port)
    try:
        action_name = sys.argv[1]
        action_args = sys.argv[3:]
        logger.info(f"--- Running checker: Action='{action_name}', Target='{host}:{port}', Args='{action_args}' ---")
        checker.action(action_name, *action_args)
    except checker.get_check_finished_exception():
        cquit(Status(checker.status), checker.public, checker.private)
    # SỬA LỖI: Thay vì bắt ChecklibException, hãy bắt Exception chung hơn
    # vì get_check_finished_exception() nên bắt các lỗi thoát chuẩn của checklib.
    # Các lỗi khác có thể là lỗi Python thuần túy.
    except Exception as e:
        logger.critical(f"An unexpected top-level Python error occurred: {e}", exc_info=True)
        detailed_error = traceback.format_exc()
        # Sử dụng Status.CHECKER_ERROR cho các lỗi không mong muốn này
        cquit(Status.CHECKER_ERROR, "Internal Checker Error", detailed_error)