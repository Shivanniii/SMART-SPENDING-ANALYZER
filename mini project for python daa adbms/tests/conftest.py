import pytest

import src.database as database


@pytest.fixture
def app_db(tmp_path, monkeypatch):
    """Use a temporary database instead of the real spending database."""
    test_db = tmp_path / "test_spending.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    database.initialize_database()
    return test_db


@pytest.fixture
def users(app_db):
    """Create two users to test user-specific data access."""
    from src.auth import create_user, authenticate_user

    create_user("alice", "AlicePass123")
    create_user("bob", "BobPass123")

    alice = authenticate_user("alice", "AlicePass123")
    bob = authenticate_user("bob", "BobPass123")

    assert alice is not None
    assert bob is not None

    return alice, bob