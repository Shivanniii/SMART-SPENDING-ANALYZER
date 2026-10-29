from src.database import get_connection
from src.models import Transaction


class TransactionManager:
    def add(self, current_user, transaction):
        """Save a transaction under the logged-in user's account."""
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO expenses
                    (user_id, expense_date, amount, category,
                     payment_method, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    current_user["user_id"],
                    transaction.expense_date,
                    transaction.amount,
                    transaction.category,
                    transaction.payment_method,
                    transaction.description.strip(),
                ),
            )

    def get_all(self, current_user):
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, user_id, expense_date, amount, category,
                       payment_method, description
                FROM expenses
                WHERE user_id = ?
                ORDER BY expense_date DESC, id DESC
                """,
                (current_user["user_id"],),
            ).fetchall()

        return [
            Transaction(
                transaction_id=row[0],
                user_id=row[1],
                expense_date=row[2],
                amount=row[3],
                category=row[4],
                payment_method=row[5],
                description=row[6] or "",
            )
            for row in rows
        ]

    def update(self, current_user, transaction):
        if transaction.transaction_id is None:
            raise ValueError("Transaction ID is required for an update.")

        with get_connection() as connection:
            connection.execute(
                """
                UPDATE expenses
                SET expense_date = ?,
                    amount = ?,
                    category = ?,
                    payment_method = ?,
                    description = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    transaction.expense_date,
                    transaction.amount,
                    transaction.category,
                    transaction.payment_method,
                    transaction.description.strip(),
                    transaction.transaction_id,
                    current_user["user_id"],
                ),
            )

    def delete(self, current_user, transaction_id):
        with get_connection() as connection:
            connection.execute(
                """
                DELETE FROM expenses
                WHERE id = ? AND user_id = ?
                """,
                (transaction_id, current_user["user_id"]),
            )

    def search(self, current_user, text=""):
        """Linear search through the user's transactions: O(n)."""
        query = text.strip().lower()
        transactions = self.get_all(current_user)

        if not query:
            return transactions

        return [
            transaction
            for transaction in transactions
            if query in transaction.description.lower()
            or query in transaction.category.lower()
            or query in transaction.payment_method.lower()
        ]

    @staticmethod
    def merge_sort(transactions, key="expense_date", descending=False):
        """Merge sort: O(n log n) time and O(n) additional space."""
        if len(transactions) <= 1:
            return transactions

        middle = len(transactions) // 2
        left = TransactionManager.merge_sort(
            transactions[:middle], key, descending
        )
        right = TransactionManager.merge_sort(
            transactions[middle:], key, descending
        )

        result = []
        left_index = 0
        right_index = 0

        while left_index < len(left) and right_index < len(right):
            left_value = getattr(left[left_index], key)
            right_value = getattr(right[right_index], key)

            take_left = (
                left_value >= right_value
                if descending
                else left_value <= right_value
            )

            if take_left:
                result.append(left[left_index])
                left_index += 1
            else:
                result.append(right[right_index])
                right_index += 1

        result.extend(left[left_index:])
        result.extend(right[right_index:])
        return result