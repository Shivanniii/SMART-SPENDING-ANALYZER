# Smart Spending Analyzer
A Python expense-tracking and analysis app built with Streamlit, SQLite, Pandas, NumPy, and Matplotlib. Tkinter is used for the separate administrator database viewer.

## Features
- User and administrator login
- Personal expense entry, search, sorting, editing, and deletion
- Monthly and category budgets
- Spending charts and written analysis
- Administrator account creation
- Administrator database viewer

## Setup
Open a terminal in the project folder and run:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt

Create the first administrator account:
py scripts\create_admin.py
Start the app:
py -m streamlit run app.py
Account roles
- User: Manages their own transactions, budgets, and reports.
- Admin: Uses the apps admin page to create user accounts and open the Tkinter database viewer.
Passwords are stored as hashes. The Tkinter viewer asks the administrator to log in again before displaying database records.
Project folders
- src/ contains database, authentication, data, and analysis logic.
- pages/ contains the Streamlit pages.
- ui/ contains the Tkinter administrator viewer.
- scripts/ contains setup utilities.
- docs/ contains database and algorithm documentation.
- data/ is where the SQLite database is created.

### `docs/database_design.md`

```markdown
# Database Design

The app stores data in a local SQLite database at `data/spending.db`.

## Tables

### users

| Column | Purpose |
|---|---|
| `id` | Unique user ID |
| `username` | Unique login name |
| `password_hash` | Salted PBKDF2 password hash |
| `role` | `admin` or `user` |
| `created_at` | Account creation time |

### expenses

| Column | Purpose |
|---|---|
| `id` | Unique transaction ID |
| `user_id` | Owner of the transaction; references `users.id` |
| `expense_date` | Date of the expense |
| `amount` | Positive expense amount |
| `category` | Expense category |
| `payment_method` | Cash, UPI, card, or another method |
| `description` | Optional transaction note |

### budgets

| Column | Purpose |
|---|---|
| `id` | Unique budget ID |
| `user_id` | Owner of the budget; references `users.id` |
| `budget_month` | Month in `YYYY-MM` format |
| `category` | Category name or `Overall` |
| `amount` | Positive budget limit |

A unique constraint on `(user_id, budget_month, category)` allows one budget per user, month, and category. Saving that budget again updates its limit.

## Relationships

- One user can have many expenses.
- One user can have many budgets.
- Deleting a user deletes their associated expenses and budgets.

The Streamlit pages filter user records by the logged-in users ID. The administrator viewer queries all records and omits password hashes.
docs/daa_algorithms.md
# DAA Algorithms

## Linear search

The transaction search checks each of the logged-in users transactions for a match in the description, category, or payment method.

- **Best case:** O(1), if the first transaction matches.
- **Worst case:** O(n), if the match is last or there is no match.
- **Space:** O(n) for the returned matching list.

Here, `n` is the number of that users transactions.

## Merge sort

Transactions can be sorted by date or amount using the merge sort implementation in `TransactionManager`.

- **Best, average, and worst case:** O(n log n).
- **Additional space:** O(n).

The implementation divides the list into smaller lists, sorts each half recursively, and merges the sorted halves.

## Category totals and ranking

The analyzer groups transactions by category and sums their amounts. SQLite performs the `GROUP BY` aggregation and orders the results by total spending.

For `n` transactions and `k` categories, aggregation processes the transaction records and ranking orders the category totals. The exact work is handled by SQLite and may depend on its query plan and indexes.

## Monthly summaries

SQL queries calculate the transaction count, total spending, and average expense for a selected month. The date filter uses the `YYYY-MM` prefix of each stored expense date.