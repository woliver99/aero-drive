#!/usr/bin/env python3
import sys
import json
import os
import hashlib
import secrets
import getpass

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

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return f"scrypt:{salt.hex()}:{key.hex()}"

def print_usage(prog):
    print(f"Usage: {prog} <command> [args...]")
    print("\nUser Commands:")
    print(f"  {prog} user add <username>")
    print(f"  {prog} user password <username>")
    print(f"  {prog} user remove <username>")
    print(f"  {prog} user list")

def prompt_password(username: str) -> str:
    try:
        entered = getpass.getpass(f"Enter password for '{username}' (leave blank to auto-generate): ").strip()
    except (EOFError, KeyboardInterrupt):
        entered = ""
    if entered:
        return entered
    return secrets.token_urlsafe(18)

def main():
    prog = os.path.basename(sys.argv[0])
    if len(sys.argv) < 3:
        print_usage(prog)
        sys.exit(1)

    category = sys.argv[1]
    action = sys.argv[2]
    data = load_data()

    if category == "user":
        if action == "add":
            if len(sys.argv) < 4:
                print(f"Usage: {prog} user add <username>")
                sys.exit(1)
            username = sys.argv[3]
            if username in data["users"]:
                print(f"User '{username}' already exists.")
                return

            password = prompt_password(username)
            pwd_hash = hash_password(password)

            data["users"][username] = {
                "enabled": True,
                "password": pwd_hash
            }
            save_data(data)

            print(f"\nUser '{username}' created successfully!")
            print(f"PASSWORD: {password}\n")

        elif action in ("password", "set-password", "passwd"):
            if len(sys.argv) < 4:
                print(f"Usage: {prog} user password <username>")
                sys.exit(1)
            username = sys.argv[3]
            if username not in data["users"]:
                print(f"User '{username}' does not exist.")
                return

            password = prompt_password(username)
            pwd_hash = hash_password(password)

            data["users"][username]["password"] = pwd_hash
            save_data(data)

            print(f"\nPassword updated for user '{username}'!")
            print(f"NEW PASSWORD: {password}\n")

        elif action in ("remove", "delete"):
            if len(sys.argv) < 4:
                print(f"Usage: {prog} user remove <username>")
                sys.exit(1)
            username = sys.argv[3]
            if username not in data["users"]:
                print(f"User '{username}' does not exist.")
                return
            del data["users"][username]
            save_data(data)
            print(f"User '{username}' removed.")

        elif action == "list":
            if not data["users"]:
                print("No users found.")
                return
            print("Users:")
            for username, info in data["users"].items():
                status = "enabled" if info.get("enabled", True) else "disabled"
                print(f"  - {username} ({status})")
        else:
            print(f"Unknown user command: {action}")
            print_usage(prog)
            sys.exit(1)

    else:
        print(f"Unknown command category: {category}")
        print_usage(prog)
        sys.exit(1)

if __name__ == "__main__":
    main()

