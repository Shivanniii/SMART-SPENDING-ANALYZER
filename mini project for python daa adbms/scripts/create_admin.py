from getpass import getpass
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from src.auth import create_user
from src.database import initialize_database


def main():
    initialize_database()

    print("Create the first administrator account.")
    username = input("Admin username: ").strip()
    password = getpass("Admin password (minimum 8 characters): ")
    password_again = getpass("Enter the password again: ")

    if password != password_again:
        print("The passwords do not match.")
        return

    try:
        create_user(username, password, role="admin")
    except ValueError as error:
        print(f"Could not create admin account: {error}")
        return

    print(f"Admin account '{username}' created.")


if __name__ == "__main__":
    main()