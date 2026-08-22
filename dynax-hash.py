#!/usr/bin/env python3
#Author: DynamindOP

import os
import sys
import json
import base64
import hashlib
import secrets
import getpass
from datetime import datetime


APP_NAME = "DYNAX HASHING"
VERSION = "1.0"

DB_FILE = "hash_db.lst"

ALGORITHM = "PBKDF2-HMAC-SHA256"
ITERATIONS = 600_000
SALT_SIZE = 32


# ============================================================
# COLORS
# ============================================================

RESET = "\033[0m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
GRAY = "\033[90m"


# ============================================================
# UI
# ============================================================

def clear_screen():
    os.system(
        "cls" if os.name == "nt" else "clear"
    )


def banner():
    print(
        f"""
{CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                    DYNAX HASHING                             ║
║                                                              ║
║              Secure Hash Storage Utility                     ║
║                                                              ║
║                     Version {VERSION:<20}       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{RESET}
"""
    )


def section(title):

    print(
        f"""
{CYAN}┌──────────────────────────────────────────────────────────────┐
│ {title:<60} │
└──────────────────────────────────────────────────────────────┘{RESET}
"""
    )


def success(message):
    print(
        f"{GREEN}✓ {message}{RESET}"
    )


def error(message):
    print(
        f"{RED}✗ {message}{RESET}"
    )


def info(message):
    print(
        f"{GRAY}• {message}{RESET}"
    )


# ============================================================
# DATABASE
# ============================================================

def create_database():

    if os.path.exists(DB_FILE):
        return False

    with open(
        DB_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write("")

    return True


def load_records():

    create_database()

    records = []

    try:

        with open(
            DB_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                try:

                    records.append(
                        json.loads(line)
                    )

                except json.JSONDecodeError:
                    continue

    except OSError as exc:

        error(
            f"Unable to read database: {exc}"
        )

    return records


def append_record(record):

    try:

        with open(
            DB_FILE,
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                json.dumps(
                    record,
                    separators=(",", ":")
                )
            )

            file.write("\n")

        return True

    except OSError as exc:

        error(
            f"Unable to write database: {exc}"
        )

        return False


# ============================================================
# HASHING
# ============================================================

def generate_hash(password):

    salt = secrets.token_bytes(
        SALT_SIZE
    )

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS
    )

    return {
        "algorithm": ALGORITHM,
        "iterations": ITERATIONS,
        "salt": base64.b64encode(
            salt
        ).decode("ascii"),
        "hash": base64.b64encode(
            derived_key
        ).decode("ascii")
    }


def verify_hash(
    password,
    record
):

    try:

        salt = base64.b64decode(
            record["salt"]
        )

        expected = base64.b64decode(
            record["hash"]
        )

        iterations = int(
            record["iterations"]
        )

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )

        return secrets.compare_digest(
            actual,
            expected
        )

    except (
        KeyError,
        ValueError,
        TypeError
    ):

        return False


# ============================================================
# CREATE HASH
# ============================================================

def create_hash():

    section(
        "CREATE NEW HASH"
    )

    username = input(
        "Identifier / username: "
    ).strip()

    if not username:

        error(
            "Identifier cannot be empty."
        )

        return

    password = getpass.getpass(
        "Password: "
    )

    if not password:

        error(
            "Password cannot be empty."
        )

        return

    confirmation = getpass.getpass(
        "Confirm password: "
    )

    if password != confirmation:

        error(
            "Passwords do not match."
        )

        return

    hash_data = generate_hash(
        password
    )

    record = {
        "id": secrets.token_hex(8),
        "identifier": username,
        "created": datetime.now().isoformat(
            timespec="seconds"
        ),
        **hash_data
    }

    if append_record(record):

        success(
            "Hash generated successfully."
        )

        print()

        print(
            f"Identifier : {username}"
        )

        print(
            f"Algorithm  : {ALGORITHM}"
        )

        print(
            f"Iterations : {ITERATIONS:,}"
        )

        print(
            f"Record ID  : {record['id']}"
        )

        print()

        info(
            f"Stored in {os.path.abspath(DB_FILE)}"
        )


# ============================================================
# VERIFY
# ============================================================

def verify_password():

    section(
        "VERIFY PASSWORD"
    )

    records = load_records()

    if not records:

        info(
            "No hashes are stored yet."
        )

        return

    identifier = input(
        "Identifier / username: "
    ).strip()

    matching = [
        record
        for record in records
        if record.get(
            "identifier"
        ) == identifier
    ]

    if not matching:

        error(
            "No matching identifier found."
        )

        return

    password = getpass.getpass(
        "Password: "
    )

    for record in matching:

        if verify_hash(
            password,
            record
        ):

            success(
                "PASSWORD VERIFIED."
            )

            return

    error(
        "PASSWORD DOES NOT MATCH."
    )


# ============================================================
# LIST RECORDS
# ============================================================

def list_records():

    section(
        "HASH DATABASE"
    )

    records = load_records()

    if not records:

        info(
            "Database is empty."
        )

        return

    print(
        f"{CYAN}"
        f"{'ID':<18}"
        f"{'IDENTIFIER':<25}"
        f"{'ALGORITHM':<28}"
        f"{'CREATED':<22}"
        f"{RESET}"
    )

    print(
        "-" * 93
    )

    for record in records:

        print(
            f"{record.get('id', ''):<18}"
            f"{record.get('identifier', ''):<25}"
            f"{record.get('algorithm', ''):<28}"
            f"{record.get('created', ''):<22}"
        )

    print()

    info(
        "Passwords themselves are never displayed."
    )


# ============================================================
# SHOW HASH
# ============================================================

def show_hash():

    section(
        "SHOW STORED HASH"
    )

    records = load_records()

    if not records:

        info(
            "Database is empty."
        )

        return

    identifier = input(
        "Identifier / username: "
    ).strip()

    matching = [
        record
        for record in records
        if record.get(
            "identifier"
        ) == identifier
    ]

    if not matching:

        error(
            "Identifier not found."
        )

        return

    for index, record in enumerate(
        matching,
        start=1
    ):

        print()

        print(
            f"{YELLOW}Record #{index}{RESET}"
        )

        print(
            f"ID         : {record['id']}"
        )

        print(
            f"Algorithm  : {record['algorithm']}"
        )

        print(
            f"Iterations : {record['iterations']}"
        )

        print(
            f"Salt       : {record['salt']}"
        )

        print(
            f"Hash       : {record['hash']}"
        )


# ============================================================
# DELETE RECORD
# ============================================================

def delete_record():

    section(
        "DELETE RECORD"
    )

    records = load_records()

    if not records:

        info(
            "Database is empty."
        )

        return

    identifier = input(
        "Identifier / username: "
    ).strip()

    matching = [
        record
        for record in records
        if record.get(
            "identifier"
        ) == identifier
    ]

    if not matching:

        error(
            "Identifier not found."
        )

        return

    print()

    for index, record in enumerate(
        matching,
        start=1
    ):

        print(
            f"[{index}] "
            f"{record.get('id')} "
            f"{record.get('created')}"
        )

    choice = input(
        "\nSelect record number: "
    ).strip()

    try:

        index = int(choice) - 1

        selected = matching[index]

    except (
        ValueError,
        IndexError
    ):

        error(
            "Invalid selection."
        )

        return

    confirm = input(
        "Delete this record? [y/N]: "
    ).strip().lower()

    if confirm != "y":

        info(
            "Deletion cancelled."
        )

        return

    records.remove(
        selected
    )

    try:

        with open(
            DB_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            for record in records:

                file.write(
                    json.dumps(
                        record,
                        separators=(",", ":")
                    )
                    + "\n"
                )

        success(
            "Record deleted."
        )

    except OSError as exc:

        error(
            f"Unable to update database: {exc}"
        )


# ============================================================
# DATABASE INFO
# ============================================================

def database_info():

    section(
        "DATABASE INFORMATION"
    )

    records = load_records()

    print(
        f"Database : {os.path.abspath(DB_FILE)}"
    )

    print(
        f"Records  : {len(records)}"
    )

    print(
        f"Algorithm: {ALGORITHM}"
    )

    print(
        f"Rounds   : {ITERATIONS:,}"
    )

    if os.path.exists(DB_FILE):

        size = os.path.getsize(
            DB_FILE
        )

        print(
            f"Size     : {size:,} bytes"
        )


# ============================================================
# HELP
# ============================================================

def help_menu():

    section(
        "COMMANDS"
    )

    print(
        """
[1] Create Hash
    Generate and store a new password hash.

[2] Verify Password
    Verify a password against a stored hash.

[3] List Records
    Show stored identifiers without exposing passwords.

[4] Show Hash
    Display the stored hash information.

[5] Delete Record
    Delete a selected database record.

[6] Database Info
    Display database information.

[7] Help
    Show this menu.

[8] Exit
    Exit DYNAX HASHING.
"""
    )


# ============================================================
# FIRST RUN
# ============================================================

def first_run():

    created = create_database()

    if created:

        print(
            f"{GREEN}"
            "✓ hash_db.lst created successfully."
            f"{RESET}"
        )

        print()

        info(
            "This database stores password hashes, "
            "not plaintext passwords."
        )

        input(
            "\nPress ENTER to continue..."
        )


# ============================================================
# MAIN MENU
# ============================================================

def main():

    clear_screen()

    banner()

    first_run()

    while True:

        print(
            f"""
{CYAN}┌──────────────────────────────────────────────────────────────┐
│                         MAIN MENU                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  [1] Create Hash                                             │
│  [2] Verify Password                                         │
│  [3] List Records                                            │
│  [4] Show Hash                                               │
│  [5] Delete Record                                           │
│  [6] Database Info                                           │
│  [7] Help                                                    │
│  [8] Exit                                                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘{RESET}
"""
        )

        choice = input(
            f"{CYAN}DYNAX ❯ {RESET}"
        ).strip()

        if choice == "1":

            create_hash()

        elif choice == "2":

            verify_password()

        elif choice == "3":

            list_records()

        elif choice == "4":

            show_hash()

        elif choice == "5":

            delete_record()

        elif choice == "6":

            database_info()

        elif choice == "7":

            help_menu()

        elif choice == "8":

            print()
            success(
                "DYNAX HASHING closed."
            )

            break

        else:

            error(
                "Invalid option."
            )

        print()

        input(
            "Press ENTER to return to menu..."
        )

        clear_screen()

        banner()


# ============================================================
# COMMAND-LINE
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            "\n\n"
            f"{YELLOW}"
            "DYNAX HASHING interrupted."
            f"{RESET}"
        )

        sys.exit(0)
