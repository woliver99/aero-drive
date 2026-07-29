#!/usr/bin/env python3
import sys
import json
import os
import hashlib
import secrets
from datetime import date

DATA_DIR = os.environ.get("AERODRIVE_DATA_DIR", "/var/lib/aerodrive")
USERS_FILE = os.path.join(DATA_DIR, "config/users.json")

def load_data():
    if not os.path.exists(USERS_FILE):
        return {"users": {}}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def hash_token(token: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(token.encode(), salt=salt, n=16384, r=8, p=1)
    return f"scrypt:{salt.hex()}:{key.hex()}"

def main():
    prog = os.path.basename(sys.argv[0])
    if len(sys.argv) < 2:
        print(f"Usage: {prog} [add-user|create-token|revoke-token|list-tokens] ...")
        sys.exit(1)

    cmd = sys.argv[1]
    data = load_data()

    if cmd == "add-user":
        if len(sys.argv) < 3:
            print(f"Usage: {prog} add-user <username>")
            sys.exit(1)
        username = sys.argv[2]
        if username in data["users"]:
            print(f"User '{username}' already exists.")
            return
        data["users"][username] = {"enabled": True, "tokens": []}
        save_data(data)
        print(f"User '{username}' created.")

    elif cmd == "create-token":
        if len(sys.argv) < 3:
            print(f"Usage: {prog} create-token <username> [label]")
            sys.exit(1)
        username = sys.argv[2]
        label = sys.argv[3] if len(sys.argv) > 3 else "default"
        if username not in data["users"]:
            print(f"User '{username}' does not exist.")
            return

        raw_token = "tok_" + secrets.token_urlsafe(16)
        token_entry = {
            "label": label,
            "hash": hash_token(raw_token),
            "created_at": str(date.today())
        }
        data["users"][username]["tokens"].append(token_entry)
        save_data(data)

        print(f"\nUser: {username} | Label: {label}")
        print(f"TOKEN: {raw_token}\n")

    elif cmd == "revoke-token":
        if len(sys.argv) < 4:
            print(f"Usage: {prog} revoke-token <username> <label>")
            sys.exit(1)
        username, label = sys.argv[2], sys.argv[3]
        if username in data["users"]:
            tokens = data["users"][username]["tokens"]
            data["users"][username]["tokens"] = [t for t in tokens if t["label"] != label]
            save_data(data)
            print(f"Revoked token '{label}' for '{username}'.")

    elif cmd == "list-tokens":
        if len(sys.argv) < 3:
            print(f"Usage: {prog} list-tokens <username>")
            sys.exit(1)
        username = sys.argv[2]
        if username in data["users"]:
            print(f"Tokens for {username}:")
            for t in data["users"][username]["tokens"]:
                print(f"  - Label: {t['label']} | Created: {t['created_at']}")
    else:
        print(f"Unknown command: {cmd}")
        print(f"Usage: {prog} [add-user|create-token|revoke-token|list-tokens] ...")
        sys.exit(1)

if __name__ == "__main__":
    main()
