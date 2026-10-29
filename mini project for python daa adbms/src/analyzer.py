import pandas as pd
import numpy as np
from src.database import get_connection


def get_category_totals(current_user, budget_month):
    with get_connection() as connection:
        return pd.read_sql_query(
            """
            SELECT category, SUM(amount) AS total
            FROM expenses
            WHERE user_id = ?
              AND substr(expense_date, 1, 7) = ?
            GROUP BY category
            ORDER BY total DESC
            """,
            connection,
            params=(current_user["user_id"], budget_month),
        )


def get_monthly_totals(current_user):
    with get_connection() as connection:
        return pd.read_sql_query(
            """
            SELECT substr(expense_date, 1, 7) AS month,
                   SUM(amount) AS total
            FROM expenses
            WHERE user_id = ?
            GROUP BY month
            ORDER BY month
            """,
            connection,
            params=(current_user["user_id"],),
        )


def get_month_summary(current_user, budget_month):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*),
                   COALESCE(SUM(amount), 0),
                   COALESCE(AVG(amount), 0)
            FROM expenses
            WHERE user_id = ?
              AND substr(expense_date, 1, 7) = ?
            """,
            (current_user["user_id"], budget_month),
        ).fetchone()

    return {
        "transactions": row[0],
        "total": row[1],
        "average": row[2],
    }


def get_month_expenses(current_user, budget_month):
    with get_connection() as connection:
        return pd.read_sql_query(
            """
            SELECT expense_date, amount, category, payment_method, description
            FROM expenses
            WHERE user_id = ?
              AND substr(expense_date, 1, 7) = ?
            ORDER BY amount DESC
            """,
            connection,
            params=(current_user["user_id"], budget_month),
        )

def get_spending_insights(month_expenses):
    if month_expenses.empty:
        return None

    amounts = month_expenses["amount"].to_numpy(dtype=float)

    average = np.mean(amounts)
    median = np.median(amounts)
    standard_deviation = np.std(amounts)

    unusual_expenses = month_expenses[
        month_expenses["amount"] > average + 2 * standard_deviation
    ]

    return {
        "average": average,
        "median": median,
        "standard_deviation": standard_deviation,
        "unusual_expenses": unusual_expenses,
    }