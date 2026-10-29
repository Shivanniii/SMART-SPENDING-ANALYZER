from src.database import get_connection


class BudgetManager:
    def save(self, current_user, budget_month, category, amount):
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO budgets (user_id, budget_month, category, amount)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (user_id, budget_month, category)
                DO UPDATE SET amount = excluded.amount
                """,
                (
                    current_user["user_id"],
                    budget_month,
                    category,
                    amount,
                ),
            )

    def get_for_month(self, current_user, budget_month):
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT id, user_id, budget_month, category, amount
                FROM budgets
                WHERE user_id = ? AND budget_month = ?
                ORDER BY category
                """,
                (current_user["user_id"], budget_month),
            ).fetchall()

    def delete(self, current_user, budget_id):
        with get_connection() as connection:
            connection.execute(
                """
                DELETE FROM budgets
                WHERE id = ? AND user_id = ?
                """,
                (budget_id, current_user["user_id"]),
            )

    def analyze(
        self,
        current_user,
        budget_month,
        category_totals,
        total_spent,
    ):
        """Calculate budget progress for the logged-in user's budgets."""
        budgets = self.get_for_month(current_user, budget_month)

        if category_totals.empty:
            spending_by_category = {}
        else:
            spending_by_category = dict(
                zip(category_totals["category"], category_totals["total"])
            )

        results = []

        for budget_id, user_id, month, category, limit in budgets:
            limit = float(limit)

            if category == "Overall":
                spent = float(total_spent)
            else:
                spent = float(spending_by_category.get(category, 0.0))

            remaining = limit - spent

            results.append(
                {
                    "id": budget_id,
                    "month": month,
                    "category": category,
                    "limit": limit,
                    "spent": spent,
                    "remaining": remaining,
                    "progress": min(spent / limit, 1.0),
                    "over_budget": spent > limit,
                }
            )

        return results