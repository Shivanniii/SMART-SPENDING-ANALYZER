import pytest

from src.auth import (
    HASH_ITERATIONS,
    _hash_password,
    _verify_password,
    authenticate_user,
    create_user,
)
from src.database import get_connection


def test_create_user_and_authenticate(app_db):
    create_user("shivi", "SecurePass123")

    user = authenticate_user("shivi", "SecurePass123")

    assert user is not None
    assert user["username"] == "shivi"
    assert isinstance(user["user_id"], int)


def test_password_is_hashed_not_stored_as_plain_text(app_db):
    create_user("shivi", "SecurePass123")

    with get_connection() as connection:
        saved_hash = connection.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            ("shivi",),
        ).fetchone()[0]

    assert saved_hash != "SecurePass123"
    assert saved_hash.startswith("pbkdf2_sha256$")
    assert str(HASH_ITERATIONS) in saved_hash
    assert _verify_password("SecurePass123", saved_hash)
    assert not _verify_password("WrongPass123", saved_hash)


def test_password_hash_uses_a_new_salt_each_time():
    first = _hash_password("SecurePass123")
    second = _hash_password("SecurePass123")

    assert first != second
    assert _verify_password("SecurePass123", first)
    assert _verify_password("SecurePass123", second)


@pytest.mark.parametrize(
    ("username", "password", "message"),
    [
        (
            "ab",
            "SecurePass123",
            "Username must contain at least 3 characters.",
        ),
        (
            "alice",
            "short",
            "Password must contain at least 8 characters.",
        ),
        (
            "   ",
            "SecurePass123",
            "Username must contain at least 3 characters.",
        ),
    ],
)
def test_create_user_validates_input(app_db, username, password, message):
    with pytest.raises(ValueError, match=message):
        create_user(username, password)


def test_duplicate_username_is_rejected_case_insensitively(app_db):
    create_user("Alice", "SecurePass123")

    with pytest.raises(ValueError, match="already in use"):
        create_user("alice", "AnotherPass123")


def test_authentication_rejects_wrong_password_and_unknown_user(app_db):
    create_user("alice", "SecurePass123")

    assert authenticate_user("alice", "IncorrectPass123") is None
    assert authenticate_user("unknown", "SecurePass123") is None


def test_authentication_is_case_insensitive_for_username(app_db):
    create_user("Alice", "SecurePass123")

    user = authenticate_user("ALICE", "SecurePass123")

    assert user is not None
    assert user["username"] == "Alice"


def test_malformed_saved_hash_does_not_authenticate():
    assert not _verify_password("anything", "not-a-valid-hash")