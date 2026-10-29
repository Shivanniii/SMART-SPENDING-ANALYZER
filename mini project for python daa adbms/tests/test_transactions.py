import pytest

from src.models import Transaction
from src.transaction_manager import TransactionManager


@pytest.fixture
def manager():
    return TransactionManager()


def make_transaction(
    user_id,
    date,
    amount,
    category,
    method="UPI",
    description="",
):
    return Transaction(
        user_id=user_id,
        expense_date=date,
        amount=amount,
        category=category,
        payment_method=method,
        description=description,
    )


def test_add_and_get_transactions(app_db, users, manager):
    alice, _ = users

    manager.add(
        alice,
        make_transaction(
            alice["user_id"],
            "2026-10-01",
            120,
            "Food",
            description="Lunch",
        ),
    )

    results = manager.get_all(alice)

    assert len(results) == 1
    assert results[0].amount == 120
    assert results[0].category == "Food"
    assert results[0].description == "Lunch"
    assert results[0].user_id == alice["user_id"]
    assert results[0].transaction_id is not None


def test_transactions_are_isolated_between_users(app_db, users, manager):
    alice, bob = users

    manager.add(
        alice,
        make_transaction(alice["user_id"], "2026-10-01", 100, "Food"),
    )
    manager.add(
        bob,
        make_transaction(bob["user_id"], "2026-10-02", 200, "Transport"),
    )

    assert [t.category for t in manager.get_all(alice)] == ["Food"]
    assert [t.category for t in manager.get_all(bob)] == ["Transport"]


def test_search_matches_description_category_and_payment_method(
    app_db, users, manager
):
    alice, _ = users

    manager.add(
        alice,
        make_transaction(
            alice["user_id"], "2026-10-01", 100, "Food", "UPI", "Lunch"
        ),
    )
    manager.add(
        alice,
        make_transaction(
            alice["user_id"], "2026-10-02", 200, "Travel", "Card", "Bus ticket"
        ),
    )

    assert len(manager.search(alice, "LUNCH")) == 1
    assert len(manager.search(alice, "travel")) == 1
    assert len(manager.search(alice, "card")) == 1
    assert len(manager.search(alice, "   ")) == 2
    assert manager.search(alice, "not found") == []


def test_update_changes_owned_transaction(app_db, users, manager):
    alice, _ = users

    manager.add(
        alice,
        make_transaction(
            alice["user_id"], "2026-10-01", 100, "Food", description="Old"
        ),
    )

    transaction = manager.get_all(alice)[0]
    transaction.amount = 250
    transaction.description = "Updated"

    manager.update(alice, transaction)

    updated = manager.get_all(alice)[0]
    assert updated.amount == 250
    assert updated.description == "Updated"


def test_other_user_cannot_update_transaction(app_db, users, manager):
    alice, bob = users

    manager.add(
        alice,
        make_transaction(alice["user_id"], "2026-10-01", 100, "Food"),
    )

    transaction = manager.get_all(alice)[0]
    transaction.amount = 999

    manager.update(bob, transaction)

    assert manager.get_all(alice)[0].amount == 100


def test_delete_only_deletes_owned_transaction(app_db, users, manager):
    alice, bob = users

    manager.add(
        alice,
        make_transaction(alice["user_id"], "2026-10-01", 100, "Food"),
    )
    transaction_id = manager.get_all(alice)[0].transaction_id

    manager.delete(bob, transaction_id)
    assert len(manager.get_all(alice)) == 1

    manager.delete(alice, transaction_id)
    assert manager.get_all(alice) == []


def test_update_requires_transaction_id(app_db, users, manager):
    alice, _ = users

    transaction = make_transaction(
        alice["user_id"], "2026-10-01", 100, "Food"
    )

    with pytest.raises(
        ValueError, match="Transaction ID is required"
    ):
        manager.update(alice, transaction)


def test_merge_sort_by_amount_ascending_and_descending(
    app_db, users, manager
):
    alice, _ = users

    transactions = [
        make_transaction(alice["user_id"], "2026-10-01", 300, "A"),
        make_transaction(alice["user_id"], "2026-10-02", 100, "B"),
        make_transaction(alice["user_id"], "2026-10-03", 200, "C"),
    ]

    ascending = manager.merge_sort(transactions, key="amount")
    descending = manager.merge_sort(
        transactions, key="amount", descending=True
    )

    assert [t.amount for t in ascending] == [100, 200, 300]
    assert [t.amount for t in descending] == [300, 200, 100]


def test_merge_sort_by_date(app_db, users, manager):
    alice, _ = users

    transactions = [
        make_transaction(alice["user_id"], "2026-10-03", 1, "A"),
        make_transaction(alice["user_id"], "2026-10-01", 1, "B"),
        make_transaction(alice["user_id"], "2026-10-02", 1, "C"),
    ]

    sorted_transactions = manager.merge_sort(
        transactions, key="expense_date"
    )

    assert [t.expense_date for t in sorted_transactions] == [
        "2026-10-01",
        "2026-10-02",
        "2026-10-03",
    ]