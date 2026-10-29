
"""Tkinter desktop utilities for Smart Spending Analyzer.

Run through app.py, which passes the logged-in user's ID and username.
"""
import sys
import csv
import sqlite3
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import messagebox, ttk, filedialog

PROJECT_DIR = Path(__file__).resolve().parents[1]

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.database import get_connection, initialize_database


CATEGORIES = [
    "Food", "Transport", "Shopping", "Bills",
    "Entertainment", "Health", "Education", "Other",
]

PAYMENT_METHODS = [
    "UPI", "Cash", "Card", "Net Banking", "Other",
]


class DesktopTool:
    def __init__(self, root, tool, user_id, username):
        self.root = root
        self.tool = tool
        self.user_id = int(user_id)
        self.username = username

        self.root.title(
            f"Smart Spending Analyzer — {self.tool_title(tool)}"
        )
        self.root.geometry("900x600")
        self.root.minsize(700, 480)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 18, "bold")
        )
        style.configure("Treeview", rowheight=26)
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold")
        )

        header = ttk.Frame(root, padding=(18, 16, 18, 8))
        header.pack(fill="x")

        ttk.Label(
            header,
            text=self.tool_title(tool),
            style="Title.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            header,
            text=(
                f"Signed in as {username} · "
                "Only your account's records are shown"
            )
        ).pack(anchor="w", pady=(4, 0))

        self.body = ttk.Frame(root, padding=18)
        self.body.pack(fill="both", expand=True)

        tool_screens = {
            "expense": self.show_expense_entry,
            "transactions": self.show_transactions,
            "budgets": self.show_budgets,
            "reports": self.show_reports,
            "data": self.show_personal_data,
        }

        tool_screens[tool]()

    @staticmethod
    def tool_title(tool):
        titles = {
            "expense": "Quick Expense Entry",
            "transactions": "Transaction Manager",
            "budgets": "Budget Planner",
            "reports": "Financial Report Viewer",
            "data": "Personal Data Viewer",
        }
        return titles.get(tool, "Desktop Tool")

    def fetch_all(self, query, params=()):
        with get_connection() as conn:
            return conn.execute(query, params).fetchall()

    # --------------------------------------------------
    # 1. QUICK EXPENSE ENTRY
    # --------------------------------------------------

    def show_expense_entry(self):
        ttk.Label(
            self.body,
            text="Record a new expense",
            font=("Segoe UI", 12, "bold")
        ).grid(
            row=0, column=0, columnspan=2,
            sticky="w", pady=(0, 12)
        )

        self.exp_date = tk.StringVar(
            value=date.today().isoformat()
        )
        self.exp_amount = tk.StringVar()
        self.exp_category = tk.StringVar(
            value=CATEGORIES[0]
        )
        self.exp_payment = tk.StringVar(
            value=PAYMENT_METHODS[0]
        )
        self.exp_description = tk.StringVar()

        fields = [
            (
                "Date (YYYY-MM-DD)",
                ttk.Entry(
                    self.body,
                    textvariable=self.exp_date,
                    width=35
                )
            ),
            (
                "Amount (₹)",
                ttk.Entry(
                    self.body,
                    textvariable=self.exp_amount,
                    width=35
                )
            ),
            (
                "Category",
                ttk.Combobox(
                    self.body,
                    textvariable=self.exp_category,
                    values=CATEGORIES,
                    state="readonly",
                    width=32
                )
            ),
            (
                "Payment method",
                ttk.Combobox(
                    self.body,
                    textvariable=self.exp_payment,
                    values=PAYMENT_METHODS,
                    state="readonly",
                    width=32
                )
            ),
            (
                "Description",
                ttk.Entry(
                    self.body,
                    textvariable=self.exp_description,
                    width=35
                )
            ),
        ]

        for row, (label, widget) in enumerate(fields, start=1):
            ttk.Label(
                self.body,
                text=label
            ).grid(
                row=row, column=0, sticky="w",
                pady=7, padx=(0, 20)
            )

            widget.grid(
                row=row, column=1,
                sticky="w", pady=7
            )

        ttk.Button(
            self.body,
            text="Save expense",
            command=self.save_expense
        ).grid(row=6, column=1, sticky="w", pady=18)

        self.body.columnconfigure(1, weight=1)

    def save_expense(self):
        try:
            expense_date = date.fromisoformat(
                self.exp_date.get().strip()
            )
            amount = float(self.exp_amount.get())

            if amount <= 0:
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "Invalid details",
                "Enter a valid date (YYYY-MM-DD) and "
                "an amount greater than zero."
            )
            return

        try:
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO expenses
                    (
                        user_id, expense_date, amount,
                        category, payment_method, description
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.user_id,
                        expense_date.isoformat(),
                        amount,
                        self.exp_category.get(),
                        self.exp_payment.get(),
                        self.exp_description.get().strip(),
                    ),
                )

            messagebox.showinfo(
                "Saved",
                "Expense added to your account."
            )
            self.exp_amount.set("")
            self.exp_description.set("")

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database error", str(error)
            )

    # --------------------------------------------------
    # SHARED TABLE HELPER
    # --------------------------------------------------

    def build_tree(
        self, parent, columns, headings, rows, widths=None
    ):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, pady=(10, 0))

        tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        vertical_scroll = ttk.Scrollbar(
            frame, orient="vertical", command=tree.yview
        )
        horizontal_scroll = ttk.Scrollbar(
            frame, orient="horizontal", command=tree.xview
        )

        tree.configure(
            yscrollcommand=vertical_scroll.set,
            xscrollcommand=horizontal_scroll.set
        )

        tree.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        for index, column in enumerate(columns):
            tree.heading(column, text=headings[index])
            width = widths[index] if widths else 130
            tree.column(
                column, width=width, minwidth=80, anchor="w"
            )

        for row in rows:
            tree.insert("", "end", values=row)

        return tree

    # --------------------------------------------------
    # 2. TRANSACTION MANAGER
    # --------------------------------------------------

    def show_transactions(self):
        top = ttk.Frame(self.body)
        top.pack(fill="x")

        ttk.Label(
            top,
            text="Search description, category, or payment method:"
        ).pack(side="left")

        self.search_var = tk.StringVar()

        ttk.Entry(
            top,
            textvariable=self.search_var,
            width=28
        ).pack(side="left", padx=8)

        ttk.Button(
            top,
            text="Search",
            command=self.refresh_transactions
        ).pack(side="left")

        ttk.Button(
            top,
            text="Show all",
            command=self.show_all_transactions
        ).pack(side="left", padx=6)

        ttk.Button(
            top,
            text="Delete selected",
            command=self.delete_transaction
        ).pack(side="right")

        self.transaction_area = ttk.Frame(self.body)
        self.transaction_area.pack(fill="both", expand=True)

        self.refresh_transactions()

    def show_all_transactions(self):
        self.search_var.set("")
        self.refresh_transactions()

    def refresh_transactions(self):
        for child in self.transaction_area.winfo_children():
            child.destroy()

        search = self.search_var.get().strip().lower()

        rows = self.fetch_all(
            """
            SELECT
                id, expense_date, amount, category,
                payment_method, COALESCE(description, '')
            FROM expenses
            WHERE user_id = ?
            ORDER BY expense_date DESC, id DESC
            """,
            (self.user_id,)
        )

        if search:
            rows = [
                row for row in rows
                if search in str(row[3]).lower()
                or search in str(row[4]).lower()
                or search in str(row[5]).lower()
            ]

        display_rows = [
            (
                row[0],
                row[1],
                f"₹{row[2]:,.2f}",
                row[3],
                row[4],
                row[5]
            )
            for row in rows
        ]

        self.transaction_tree = self.build_tree(
            self.transaction_area,
            (
                "id", "date", "amount",
                "category", "payment", "description"
            ),
            (
                "ID", "Date", "Amount",
                "Category", "Payment", "Description"
            ),
            display_rows,
            (55, 105, 110, 120, 120, 250)
        )

        if not display_rows:
            ttk.Label(
                self.transaction_area,
                text="No matching transactions found."
            ).pack(anchor="w", pady=8)

    def delete_transaction(self):
        selected = self.transaction_tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select a transaction",
                "Select a row first."
            )
            return

        values = self.transaction_tree.item(
            selected[0], "values"
        )
        transaction_id = int(values[0])

        confirmed = messagebox.askyesno(
            "Confirm deletion",
            "Delete this transaction from your account?"
        )

        if not confirmed:
            return

        with get_connection() as conn:
            conn.execute(
                """
                DELETE FROM expenses
                WHERE id = ? AND user_id = ?
                """,
                (transaction_id, self.user_id)
            )

        self.refresh_transactions()
        messagebox.showinfo("Deleted", "Transaction deleted.")

    # --------------------------------------------------
    # 3. BUDGET PLANNER
    # --------------------------------------------------

    def show_budgets(self):
        self.budget_month = tk.StringVar(
            value=date.today().strftime("%Y-%m")
        )
        self.budget_category = tk.StringVar(value="Overall")
        self.budget_amount = tk.StringVar(value="5000")

        form = ttk.LabelFrame(
            self.body,
            text="Set or update a monthly budget",
            padding=12
        )
        form.pack(fill="x")

        ttk.Label(
            form, text="Month (YYYY-MM)"
        ).grid(row=0, column=0, sticky="w", padx=5, pady=6)

        ttk.Entry(
            form,
            textvariable=self.budget_month,
            width=18
        ).grid(row=0, column=1, padx=5, pady=6)

        ttk.Label(
            form, text="Category"
        ).grid(row=0, column=2, sticky="w", padx=5, pady=6)

        ttk.Combobox(
            form,
            textvariable=self.budget_category,
            values=["Overall"] + CATEGORIES,
            state="readonly",
            width=18
        ).grid(row=0, column=3, padx=5, pady=6)

        ttk.Label(
            form, text="Limit (₹)"
        ).grid(row=1, column=0, sticky="w", padx=5, pady=6)

        ttk.Entry(
            form,
            textvariable=self.budget_amount,
            width=18
        ).grid(row=1, column=1, padx=5, pady=6)

        ttk.Button(
            form,
            text="Save budget",
            command=self.save_budget
        ).grid(row=1, column=3, sticky="e", padx=5, pady=6)

        ttk.Button(
            self.body,
            text="Refresh budget list",
            command=self.refresh_budgets
        ).pack(anchor="e", pady=(10, 0))

        self.budget_area = ttk.Frame(self.body)
        self.budget_area.pack(fill="both", expand=True)

        self.refresh_budgets()

    def save_budget(self):
        month = self.budget_month.get().strip()

        try:
            if (
                len(month) != 7
                or month[4] != "-"
                or not (1 <= int(month[5:7]) <= 12)
                or int(month[:4]) < 1900
            ):
                raise ValueError

            amount = float(self.budget_amount.get())

            if amount <= 0:
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "Invalid budget",
                "Enter month as YYYY-MM and a limit greater than zero."
            )
            return

        try:
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO budgets
                        (user_id, budget_month, category, amount)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, budget_month, category)
                    DO UPDATE SET amount = excluded.amount
                    """,
                    (
                        self.user_id,
                        month,
                        self.budget_category.get(),
                        amount
                    )
                )

            self.refresh_budgets()
            messagebox.showinfo("Saved", "Budget saved.")

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database error",
                "Could not save budget. Check that the existing "
                "budgets table supports this budget format.\n\n"
                + str(error)
            )

    def refresh_budgets(self):
        for child in self.budget_area.winfo_children():
            child.destroy()

        month = self.budget_month.get().strip()

        rows = self.fetch_all(
            """
            SELECT id, budget_month, category, amount
            FROM budgets
            WHERE user_id = ? AND budget_month = ?
            ORDER BY category
            """,
            (self.user_id, month)
        )

        display_rows = [
            (
                row[0],
                row[1],
                row[2],
                f"₹{row[3]:,.2f}"
            )
            for row in rows
        ]

        self.budget_tree = self.build_tree(
            self.budget_area,
            ("id", "month", "category", "amount"),
            ("ID", "Month", "Category", "Limit"),
            display_rows,
            (60, 120, 180, 150)
        )

        ttk.Button(
            self.budget_area,
            text="Delete selected budget",
            command=self.delete_budget
        ).pack(anchor="e", pady=8)

    def delete_budget(self):
        selected = self.budget_tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select a budget",
                "Select a budget row first."
            )
            return

        values = self.budget_tree.item(
            selected[0], "values"
        )
        budget_id = int(values[0])

        confirmed = messagebox.askyesno(
            "Confirm deletion",
            "Delete this budget?"
        )

        if not confirmed:
            return

        with get_connection() as conn:
            conn.execute(
                """
                DELETE FROM budgets
                WHERE id = ? AND user_id = ?
                """,
                (budget_id, self.user_id)
            )

        self.refresh_budgets()

    # --------------------------------------------------
    # 4. FINANCIAL REPORT VIEWER
    # --------------------------------------------------

    def show_reports(self):
        controls = ttk.Frame(self.body)
        controls.pack(fill="x")

        ttk.Label(
            controls, text="Month (YYYY-MM):"
        ).pack(side="left")

        self.report_month = tk.StringVar(
            value=date.today().strftime("%Y-%m")
        )

        ttk.Entry(
            controls,
            textvariable=self.report_month,
            width=14
        ).pack(side="left", padx=8)

        ttk.Button(
            controls,
            text="Generate report",
            command=self.generate_report
        ).pack(side="left")

        self.report_text = tk.Text(
            self.body,
            height=18,
            wrap="word",
            font=("Consolas", 11)
        )
        self.report_text.pack(
            fill="both", expand=True, pady=12
        )

        self.generate_report()

    def generate_report(self):
        month = self.report_month.get().strip()

        try:
            if (
                len(month) != 7
                or month[4] != "-"
                or not (1 <= int(month[5:7]) <= 12)
                or int(month[:4]) < 1900
            ):
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid month",
                "Enter month as YYYY-MM."
            )
            return

        summary = self.fetch_all(
            """
            SELECT
                COUNT(*),
                COALESCE(SUM(amount), 0),
                COALESCE(AVG(amount), 0)
            FROM expenses
            WHERE user_id = ?
              AND substr(expense_date, 1, 7) = ?
            """,
            (self.user_id, month)
        )[0]

        categories = self.fetch_all(
            """
            SELECT category, SUM(amount)
            FROM expenses
            WHERE user_id = ?
              AND substr(expense_date, 1, 7) = ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
            """,
            (self.user_id, month)
        )

        self.report_text.delete("1.0", "end")

        self.report_text.insert(
            "end",
            f"FINANCIAL REPORT — {month}\n"
        )
        self.report_text.insert("end", "=" * 45 + "\n\n")

        self.report_text.insert(
            "end",
            f"Transactions: {summary[0]}\n"
            f"Total spent: ₹{summary[1]:,.2f}\n"
            f"Average expense: ₹{summary[2]:,.2f}\n\n"
        )

        self.report_text.insert(
            "end",
            "SPENDING BY CATEGORY\n" + "-" * 45 + "\n"
        )

        if not categories:
            self.report_text.insert(
                "end",
                "No expenses recorded for this month.\n"
            )
        else:
            for category, total in categories:
                self.report_text.insert(
                    "end",
                    f"{category:<22} ₹{total:>12,.2f}\n"
                )

            highest = categories[0]

            self.report_text.insert(
                "end",
                f"\nHighest spending category: {highest[0]} "
                f"(₹{highest[1]:,.2f})\n"
            )

    # --------------------------------------------------
    # 5. PERSONAL DATA VIEWER
    # --------------------------------------------------

    def show_personal_data(self):
        ttk.Label(
            self.body,
            text="Your saved expenses and budgets",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")

        buttons = ttk.Frame(self.body)
        buttons.pack(fill="x", pady=6)

        ttk.Button(
            buttons,
            text="Refresh",
            command=self.refresh_personal_data
        ).pack(side="right")

        ttk.Button(
            buttons,
            text="Export my expenses to CSV",
            command=self.export_expenses
        ).pack(side="right", padx=6)

        self.personal_area = ttk.Frame(self.body)
        self.personal_area.pack(fill="both", expand=True)

        self.refresh_personal_data()

    def refresh_personal_data(self):
        for child in self.personal_area.winfo_children():
            child.destroy()

        expenses = self.fetch_all(
            """
            SELECT
                id, expense_date, amount, category,
                payment_method, COALESCE(description, '')
            FROM expenses
            WHERE user_id = ?
            ORDER BY expense_date DESC, id DESC
            """,
            (self.user_id,)
        )

        budgets = self.fetch_all(
            """
            SELECT budget_month, category, amount
            FROM budgets
            WHERE user_id = ?
            ORDER BY budget_month DESC, category
            """,
            (self.user_id,)
        )

        ttk.Label(
            self.personal_area,
            text=(
                f"Expense records: {len(expenses)}  |  "
                f"Budget records: {len(budgets)}"
            )
        ).pack(anchor="w", pady=(0, 8))

        tabs = ttk.Notebook(self.personal_area)
        tabs.pack(fill="both", expand=True)

        expense_frame = ttk.Frame(tabs, padding=6)
        budget_frame = ttk.Frame(tabs, padding=6)

        tabs.add(expense_frame, text="My Expenses")
        tabs.add(budget_frame, text="My Budgets")

        self.build_tree(
            expense_frame,
            (
                "id", "date", "amount",
                "category", "payment", "description"
            ),
            (
                "ID", "Date", "Amount",
                "Category", "Payment", "Description"
            ),
            [
                (
                    row[0], row[1], f"₹{row[2]:,.2f}",
                    row[3], row[4], row[5]
                )
                for row in expenses
            ],
            (50, 105, 110, 120, 120, 250)
        )

        self.build_tree(
            budget_frame,
            ("month", "category", "amount"),
            ("Month", "Category", "Limit"),
            [
                (row[0], row[1], f"₹{row[2]:,.2f}")
                for row in budgets
            ],
            (130, 180, 150)
        )

    def export_expenses(self):
        path = filedialog.asksaveasfilename(
            title="Export your expenses",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="my_expenses.csv"
        )

        if not path:
            return

        rows = self.fetch_all(
            """
            SELECT
                expense_date, amount, category,
                payment_method, COALESCE(description, '')
            FROM expenses
            WHERE user_id = ?
            ORDER BY expense_date DESC, id DESC
            """,
            (self.user_id,)
        )

        try:
            with open(
                path, "w", newline="", encoding="utf-8-sig"
            ) as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Date", "Amount", "Category",
                    "Payment Method", "Description"
                ])
                writer.writerows(rows)

            messagebox.showinfo(
                "Export complete",
                f"Your expenses were exported to:\n{path}"
            )

        except OSError as error:
            messagebox.showerror(
                "Export failed", str(error)
            )


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: python ui/desktop_tools.py "
            "TOOL USER_ID USERNAME"
        )
        raise SystemExit(2)

    tool = sys.argv[1]
    user_id = sys.argv[2]
    username = sys.argv[3]

    allowed_tools = {
        "expense",
        "transactions",
        "budgets",
        "reports",
        "data"
    }

    if tool not in allowed_tools:
        raise SystemExit("Unknown desktop tool.")

    initialize_database()

    root = tk.Tk()
    DesktopTool(root, tool, user_id, username)
    root.mainloop()


if __name__ == "__main__":
    main()
