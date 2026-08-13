#!/usr/bin/env python3
import sys
import json
import os
import hashlib
import secrets

DATA_DIR = os.environ.get("DATA_DIR", "/var/lib/maple-drive")
USERS_FILE = os.path.join(DATA_DIR, "config/users.json")
USERS_DIR = os.path.join(DATA_DIR, "users")

def verify_token(token: str, stored_hash: str) -> bool:
    try:
        algo, salt_hex, key_hex = stored_hash.split(":")
        if algo != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        key = hashlib.scrypt(token.encode(), salt=salt, n=16384, r=8, p=1)
        return secrets.compare_digest(key, expected_key)
    except Exception:
        return False

def main():
    try:
        input_data = json.load(sys.stdin)
        if not isinstance(input_data, dict):
            sys.exit(1)

        username = input_data.get("user")
        password = input_data.get("pass")

        # Type checking: ensure both username and password are non-empty strings
        if not isinstance(username, str) or not isinstance(password, str):
            sys.exit(1)

        username = username.strip()
        if not username or not password or not os.path.exists(USERS_FILE):
            sys.exit(1)

        # Path traversal check: ensure username contains no path separator or parent dir tokens
        if "/" in username or "\\" in username or ".." in username:
            sys.exit(1)

        with open(USERS_FILE, "r") as f:
            data = json.load(f)

        user_data = data.get("users", {}).get(username)
        if not isinstance(user_data, dict):
            sys.exit(1)

        stored_hash = user_data.get("password")
        if isinstance(stored_hash, str) and verify_token(password, stored_hash):
            base_dir = os.path.realpath(USERS_DIR)
            user_path = os.path.realpath(os.path.join(base_dir, username))

            # Canonical path defense: verify user_path is strictly within USERS_DIR
            if not user_path.startswith(base_dir + os.sep):
                sys.exit(1)

            os.makedirs(user_path, exist_ok=True)

            # Return isolated jail root back to rclone
            print(json.dumps({
                "type": "local",
                "_root": user_path
            }))
            sys.exit(0)
    except Exception:
        pass

    sys.exit(1)

if __name__ == "__main__":
    main()
