import pandas as pd

from src.budget_manager import BudgetManager


def test_save_and_get_budget_for_month(app_db, users):
    alice, _ = users
    manager = BudgetManager()

    manager.save(alice, "2026-10", "Food", 2000)

    budgets = manager.get_for_month(alice, "2026-10")

    assert len(budgets) == 1
    assert budgets[0][2] == "2026-10"
    assert budgets[0][3] == "Food"
    assert budgets[0][4] == 2000


def test_saving_same_budget_updates_amount(app_db, users):
    alice, _ = users
    manager = BudgetManager()

    manager.save(alice, "2026-10", "Food", 2000)
    manager.save(alice, "2026-10", "Food", 2500)

    budgets = manager.get_for_month(alice, "2026-10")

    assert len(budgets) == 1
    assert budgets[0][4] == 2500


def test_budgets_are_isolated_between_users_and_months(app_db, users):
    alice, bob = users
    manager = BudgetManager()

    manager.save(alice, "2026-10", "Food", 1000)
    manager.save(bob, "2026-10", "Food", 2000)
    manager.save(alice, "2026-09", "Food", 3000)

    alice_october = manager.get_for_month(alice, "2026-10")
    bob_october = manager.get_for_month(bob, "2026-10")
    alice_september = manager.get_for_month(alice, "2026-09")

    assert len(alice_october) == 1
    assert alice_october[0][4] == 1000

    assert len(bob_october) == 1
    assert bob_october[0][4] == 2000

    assert len(alice_september) == 1
    assert alice_september[0][4] == 3000


def test_delete_only_deletes_owned_budget(app_db, users):
    alice, bob = users
    manager = BudgetManager()

    manager.save(alice, "2026-10", "Food", 1000)
    budget_id = manager.get_for_month(alice, "2026-10")[0][0]

    manager.delete(bob, budget_id)
    assert len(manager.get_for_month(alice, "2026-10")) == 1

    manager.delete(alice, budget_id)
    assert manager.get_for_month(alice, "2026-10") == []


def test_analyze_category_and_overall_budget_progress(app_db, users):
    alice, _ = users
    manager = BudgetManager()

    manager.save(alice, "2026-10", "Food", 1000)
    manager.save(alice, "2026-10", "Overall", 1500)

    category_totals = pd.DataFrame(
        [
            {"category": "Food", "total": 1200.0},
            {"category": "Transport", "total": 100.0},
        ]
    )

    results = manager.analyze(
        alice,
        "2026-10",
        category_totals,
        1300,
    )

    by_category = {
        item["category"]: item
        for item in results
    }

    assert by_category["Food"]["spent"] == 1200
    assert by_category["Food"]["remaining"] == -200
    assert by_category["Food"]["progress"] == 1.0
    assert by_category["Food"]["over_budget"] is True

    assert by_category["Overall"]["spent"] == 1300
    assert by_category["Overall"]["remaining"] == 200
    assert by_category["Overall"]["over_budget"] is False


def test_analyze_empty_category_totals(app_db, users):
    alice, _ = users
    manager = BudgetManager()

    manager.save(alice, "2026-10", "Food", 1000)

    empty_totals = pd.DataFrame(
        columns=["category", "total"]
    )

    results = manager.analyze(
        alice,
        "2026-10",
        empty_totals,
        0,
    )

    assert results[0]["spent"] == 0
    assert results[0]["remaining"] == 1000
    assert results[0]["progress"] == 0
    assert results[0]["over_budget"] is False