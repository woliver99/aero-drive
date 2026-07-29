#!/usr/bin/env python3
import sys
import json
import os
import hashlib
import secrets

DATA_DIR = os.environ.get("AERODRIVE_DATA_DIR", "/var/lib/aerodrive")
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
        username = input_data.get("user")
        password = input_data.get("pass")

        if not username or not password or not os.path.exists(USERS_FILE):
            sys.exit(1)

        with open(USERS_FILE, "r") as f:
            data = json.load(f)

        user_data = data.get("users", {}).get(username)
        if not user_data or not user_data.get("enabled", True):
            sys.exit(1)

        for token_entry in user_data.get("tokens", []):
            if verify_token(password, token_entry.get("hash", "")):
                user_path = os.path.join(USERS_DIR, username)
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
