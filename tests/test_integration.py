#!/usr/bin/env python3
import unittest
import urllib.request
import urllib.error
import ssl
import json
import hashlib
import secrets
import base64
import subprocess
import time
import os
import shutil

PORT = os.environ.get("PORT", "8080")
BASE_URL = f"https://127.0.0.1:{PORT}"
DATA_DIR = os.path.abspath("mapledrive_data")
CONTAINER_NAME = "mapledrive"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

TEST_USER = "testuser"
TEST_PASS = "testpassword123"

TEST_USER_2 = "user2"
TEST_PASS_2 = "user2password123"

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return f"scrypt:{salt.hex()}:{key.hex()}"

def make_request(path="", method="GET", user=None, password=None, data=None):
    url = f"{BASE_URL}/{path.lstrip('/')}"
    req = urllib.request.Request(url, data=data, method=method)
    if user is not None and password is not None:
        auth_str = f"{user}:{password}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        req.add_header("Authorization", f"Basic {b64_auth}")
    return urllib.request.urlopen(req, context=SSL_CTX)

def stop_container():
    subprocess.run(["podman", "rm", "-f", CONTAINER_NAME], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=False)

def setUpModule():
    # 1. Stop container if running
    stop_container()

    # 2. Clean mapledrive_data directory
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR, ignore_errors=True)

    config_dir = os.path.join(DATA_DIR, "config")
    os.makedirs(config_dir, exist_ok=True)

    # 3. Seed users.json
    users_file = os.path.join(config_dir, "users.json")
    users_data = {
        "users": {
            TEST_USER: {
                "password": hash_password(TEST_PASS)
            },
            TEST_USER_2: {
                "password": hash_password(TEST_PASS_2)
            }
        }
    }
    with open(users_file, "w") as f:
        json.dump(users_data, f, indent=2)

    # 4. Launch container via scripts/run.sh
    subprocess.run(["./scripts/run.sh"], check=True)

    # 5. Wait for server readiness
    start_time = time.time()
    ready = False
    while time.time() - start_time < 15:
        try:
            make_request()
        except urllib.error.HTTPError as e:
            if e.code in (401, 200, 207):
                ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)

    if not ready:
        raise RuntimeError("MapleDrive server failed to start within timeout.")

def tearDownModule():
    # Stop container and clean data directory
    stop_container()
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR, ignore_errors=True)

class TestMapleDriveIntegration(unittest.TestCase):

    def test_01_unauthenticated_request_returns_401(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            make_request()
        self.assertEqual(cm.exception.code, 401)

    def test_02_invalid_password_returns_401(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            make_request(user=TEST_USER, password="wrongpassword")
        self.assertEqual(cm.exception.code, 401)

    def test_03_invalid_username_returns_401(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            make_request(user="nonexistent", password=TEST_PASS)
        self.assertEqual(cm.exception.code, 401)

    def test_04_valid_auth_list_root(self):
        res = make_request(user=TEST_USER, password=TEST_PASS)
        self.assertIn(res.status, (200, 207))

    def test_05_webdav_crud_operations(self):
        file_path = "test_document.txt"
        content = b"MapleDrive Integration Test Content"

        # 1. PUT file
        res_put = make_request(path=file_path, method="PUT", user=TEST_USER, password=TEST_PASS, data=content)
        self.assertIn(res_put.status, (200, 201, 204))

        # 2. GET file
        res_get = make_request(path=file_path, method="GET", user=TEST_USER, password=TEST_PASS)
        self.assertEqual(res_get.status, 200)
        self.assertEqual(res_get.read(), content)

        # 3. DELETE file
        res_del = make_request(path=file_path, method="DELETE", user=TEST_USER, password=TEST_PASS)
        self.assertIn(res_del.status, (200, 204))

        # 4. GET file again should 404
        with self.assertRaises(urllib.error.HTTPError) as cm:
            make_request(path=file_path, method="GET", user=TEST_USER, password=TEST_PASS)
        self.assertEqual(cm.exception.code, 404)

    def test_06_multi_user_data_isolation(self):
        file_u1 = "user1_secret.txt"
        file_u2 = "user2_secret.txt"

        # User 1 uploads file
        make_request(path=file_u1, method="PUT", user=TEST_USER, password=TEST_PASS, data=b"Secret U1")
        # User 2 uploads file
        make_request(path=file_u2, method="PUT", user=TEST_USER_2, password=TEST_PASS_2, data=b"Secret U2")

        # User 2 tries to access User 1's file -> 404
        with self.assertRaises(urllib.error.HTTPError) as cm:
            make_request(path=file_u1, method="GET", user=TEST_USER_2, password=TEST_PASS_2)
        self.assertEqual(cm.exception.code, 404)

        # Clean up
        make_request(path=file_u1, method="DELETE", user=TEST_USER, password=TEST_PASS)
        make_request(path=file_u2, method="DELETE", user=TEST_USER_2, password=TEST_PASS_2)

    def test_07_path_traversal_username_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            make_request(user="../testuser", password=TEST_PASS)
        self.assertEqual(cm.exception.code, 401)

if __name__ == "__main__":
    unittest.main()

