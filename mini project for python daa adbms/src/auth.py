import hashlib
import hmac
import secrets

from src.database import get_connection


HASH_NAME = "sha256"
HASH_ITERATIONS = 310_000
SALT_BYTES = 16


def _hash_password(password):
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        HASH_NAME,
        password.encode("utf-8"),
        salt,
        HASH_ITERATIONS,
    )

    return (
        f"pbkdf2_{HASH_NAME}$"
        f"{HASH_ITERATIONS}$"
        f"{salt.hex()}$"
        f"{digest.hex()}"
    )


def _verify_password(password, saved_hash):
    try:
        algorithm, iterations_text, salt_hex, digest_hex = saved_hash.split("$")
        if algorithm != f"pbkdf2_{HASH_NAME}":
            return False

        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_hex)
        expected_digest = bytes.fromhex(digest_hex)

        actual_digest = hashlib.pbkdf2_hmac(
            HASH_NAME,
            password.encode("utf-8"),
            salt,
            iterations,
        )

        return hmac.compare_digest(actual_digest, expected_digest)
    except (ValueError, TypeError):
        return False


def create_user(username, password, role="user"):
    """Create a user with a hashed password. Role must be admin or user."""
    username = username.strip()

    if len(username) < 3:
        raise ValueError("Username must contain at least 3 characters.")

    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")

    if role not in {"admin", "user"}:
        raise ValueError("Role must be 'admin' or 'user'.")

    password_hash = _hash_password(password)

    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
                """,
                (username, password_hash, role),
            )
    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            raise ValueError("That username is already in use.") from error
        raise


def authenticate_user(username, password):
    """Return the user's ID, username, and role if the login is valid."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, username, password_hash, role
            FROM users
            WHERE username = ? COLLATE NOCASE
            """,
            (username.strip(),),
        ).fetchone()

    if row is None or not _verify_password(password, row[2]):
        return None

    return {
        "user_id": row[0],
        "username": row[1],
        "role": row[3],
    }

def admin_exists():
    with get_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()

    return row is not None