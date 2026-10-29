import pytest

from src.analyzer import (
    get_category_totals,
    get_month_expenses,
    get_month_summary,
    get_monthly_totals,
)
from src.models import Transaction
from src.transaction_manager import TransactionManager


def add_expense(
    manager,
    user,
    date,
    amount,
    category,
    method="UPI",
    description="",
):
    transaction = Transaction(
        user_id=user["user_id"],
        expense_date=date,
        amount=amount,
        category=category,
        payment_method=method,
        description=description,
    )

    manager.add(user, transaction)


def test_month_summary_calculates_count_total_and_average(
    app_db, users
):
    alice, _ = users
    manager = TransactionManager()

    add_expense(manager, alice, "2026-10-01", 100, "Food")
    add_expense(manager, alice, "2026-10-02", 200, "Food")
    add_expense(manager, alice, "2026-10-03", 300, "Travel")

    summary = get_month_summary(alice, "2026-10")

    assert summary["transactions"] == 3
    assert summary["total"] == pytest.approx(600)
    assert summary["average"] == pytest.approx(200)


def test_month_summary_for_empty_month_is_zero(app_db, users):
    alice, _ = users

    summary = get_month_summary(alice, "2026-08")

    assert summary["transactions"] == 0
    assert summary["total"] == 0
    assert summary["average"] == 0


def test_category_totals_are_month_scoped_and_sorted(
    app_db, users
):
    alice, bob = users
    manager = TransactionManager()

    add_expense(manager, alice, "2026-10-01", 100, "Food")
    add_expense(manager, alice, "2026-10-02", 300, "Food")
    add_expense(manager, alice, "2026-10-03", 150, "Travel")
    add_expense(manager, alice, "2026-09-03", 999, "Shopping")
    add_expense(manager, bob, "2026-10-04", 5000, "Food")

    totals = get_category_totals(alice, "2026-10")

    assert totals.to_dict("records") == [
        {"category": "Food", "total": 400.0},
        {"category": "Travel", "total": 150.0},
    ]


def test_monthly_totals_are_user_scoped_and_chronological(
    app_db, users
):
    alice, bob = users
    manager = TransactionManager()

    add_expense(manager, alice, "2026-09-01", 100, "Food")
    add_expense(manager, alice, "2026-10-01", 200, "Food")
    add_expense(manager, bob, "2026-10-02", 999, "Food")

    totals = get_monthly_totals(alice)

    assert totals.to_dict("records") == [
        {"month": "2026-09", "total": 100.0},
        {"month": "2026-10", "total": 200.0},
    ]


def test_month_expenses_are_largest_first_and_month_scoped(
    app_db, users
):
    alice, _ = users
    manager = TransactionManager()

    add_expense(
        manager, alice, "2026-10-01", 50, "Food",
        description="Snack",
    )
    add_expense(
        manager, alice, "2026-10-02", 500, "Bills",
        description="Electricity",
    )
    add_expense(
        manager, alice, "2026-09-02", 1000, "Shopping",
        description="Old purchase",
    )

    expenses = get_month_expenses(alice, "2026-10")

    assert expenses["amount"].tolist() == [500.0, 50.0]
    assert expenses["description"].tolist() == [
        "Electricity",
        "Snack",
    ]