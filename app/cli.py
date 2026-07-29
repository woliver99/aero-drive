#!/usr/bin/env python3
import sys
import json
import os
import hashlib
import secrets

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
    print(f"Usage: {prog} <category> <action> [args...]")
    print("\nUser Commands:")
    print(f"  {prog} user add <username>")
    print(f"  {prog} user remove <username>")
    print(f"  {prog} user list")
    print("\nPassword Commands:")
    print(f"  {prog} password add <username> <password> [note]")
    print(f"  {prog} password remove <username> <note>")
    print(f"  {prog} password list <username>")

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
            data["users"][username] = {"enabled": True, "passwords": {}}
            save_data(data)
            print(f"User '{username}' created.")

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

    elif category == "password":
        if action == "add":
            if len(sys.argv) < 5:
                print(f"Usage: {prog} password add <username> <password> [note]")
                sys.exit(1)
            username = sys.argv[3]
            password = sys.argv[4]
            note = sys.argv[5] if len(sys.argv) > 5 else "default"

            if username not in data["users"]:
                print(f"User '{username}' does not exist.")
                return

            if "passwords" not in data["users"][username] or not isinstance(data["users"][username]["passwords"], dict):
                data["users"][username]["passwords"] = {}

            pwd_hash = hash_password(password)
            data["users"][username]["passwords"][pwd_hash] = note
            save_data(data)
            print(f"Password added for user '{username}' (Note: {note}).")

        elif action in ("remove", "delete", "revoke"):
            if len(sys.argv) < 5:
                print(f"Usage: {prog} password remove <username> <note>")
                sys.exit(1)
            username = sys.argv[3]
            target_note = sys.argv[4]

            if username not in data["users"]:
                print(f"User '{username}' does not exist.")
                return

            passwords = data["users"][username].get("passwords", {})
            if isinstance(passwords, dict):
                to_delete = [h for h, note in passwords.items() if note == target_note or h == target_note]
                if not to_delete:
                    print(f"No password matching note '{target_note}' found for '{username}'.")
                    return
                for h in to_delete:
                    del passwords[h]
                save_data(data)
                print(f"Removed password '{target_note}' for '{username}'.")
            else:
                print(f"No passwords found for '{username}'.")

        elif action == "list":
            if len(sys.argv) < 4:
                print(f"Usage: {prog} password list <username>")
                sys.exit(1)
            username = sys.argv[3]
            if username not in data["users"]:
                print(f"User '{username}' does not exist.")
                return
            passwords = data["users"][username].get("passwords", {})
            if isinstance(passwords, dict) and passwords:
                print(f"Passwords for {username}:")
                for pwd_hash, note in passwords.items():
                    print(f"  - Note: {note}")
            else:
                print(f"No passwords set for {username}.")
        else:
            print(f"Unknown password command: {action}")
            print_usage(prog)
            sys.exit(1)

    else:
        print(f"Unknown category: {category}")
        print_usage(prog)
        sys.exit(1)

if __name__ == "__main__":
    main()

