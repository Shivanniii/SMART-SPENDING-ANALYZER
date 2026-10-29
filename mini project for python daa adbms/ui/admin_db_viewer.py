import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from src.auth import authenticate_user
from src.database import get_connection, initialize_database


TABLE_QUERIES = {
    "Users": """
        SELECT id, username, role, created_at
        FROM users
        ORDER BY id
    """,
    "Expenses": """
        SELECT expenses.id,
               users.username,
               expenses.expense_date,
               expenses.amount,
               expenses.category,
               expenses.payment_method,
               expenses.description
        FROM expenses
        LEFT JOIN users ON users.id = expenses.user_id
        ORDER BY expenses.expense_date DESC, expenses.id DESC
    """,
    "Budgets": """
        SELECT budgets.id,
               users.username,
               budgets.budget_month,
               budgets.category,
               budgets.amount
        FROM budgets
        LEFT JOIN users ON users.id = budgets.user_id
        ORDER BY budgets.budget_month DESC, users.username
    """,
}


class AdminDatabaseViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Spending Analyzer — Admin Database Viewer")
        self.root.geometry("1050x650")
        self.root.minsize(800, 500)

        self.login_frame = ttk.Frame(root, padding=24)
        self.login_frame.pack(fill="both", expand=True)

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self.show_login()

    def show_login(self):
        ttk.Label(
            self.login_frame,
            text="Admin verification",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(20, 8))

        ttk.Label(
            self.login_frame,
            text="Log in with an administrator account to view database records.",
        ).pack(pady=(0, 20))

        form = ttk.Frame(self.login_frame)
        form.pack()

        ttk.Label(form, text="Username").grid(
            row=0, column=0, sticky="w", padx=8, pady=8
        )
        username_entry = ttk.Entry(
            form,
            textvariable=self.username_var,
            width=32,
        )
        username_entry.grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(form, text="Password").grid(
            row=1, column=0, sticky="w", padx=8, pady=8
        )
        password_entry = ttk.Entry(
            form,
            textvariable=self.password_var,
            show="•",
            width=32,
        )
        password_entry.grid(row=1, column=1, padx=8, pady=8)

        ttk.Button(
            form,
            text="Verify admin login",
            command=self.verify_admin,
        ).grid(row=2, column=1, sticky="e", padx=8, pady=16)

        password_entry.bind("<Return>", lambda _event: self.verify_admin())
        username_entry.focus_set()

    def verify_admin(self):
        user = authenticate_user(
            self.username_var.get(),
            self.password_var.get(),
        )

        if user is None:
            messagebox.showerror(
                "Login failed",
                "The username or password is incorrect.",
            )
            return

        if user["role"] != "admin":
            messagebox.showerror(
                "Access denied",
                "Only an administrator can view database records.",
            )
            return

        self.password_var.set("")
        self.show_database()

    def show_database(self):
        self.login_frame.destroy()

        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        header = ttk.Frame(container)
        header.pack(fill="x", pady=(0, 10))

        ttk.Label(
            header,
            text="Database records",
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")

        ttk.Button(
            header,
            text="Refresh",
            command=self.refresh_all,
        ).pack(side="right")

        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill="both", expand=True)

        self.tables = {}

        for table_name in TABLE_QUERIES:
            frame = ttk.Frame(self.notebook, padding=8)
            self.notebook.add(frame, text=table_name)
            self.tables[table_name] = frame

        self.refresh_all()

    def refresh_all(self):
        for table_name, query in TABLE_QUERIES.items():
            frame = self.tables[table_name]

            for child in frame.winfo_children():
                child.destroy()

            with get_connection() as connection:
                cursor = connection.execute(query)
                column_names = [description[0] for description in cursor.description]
                rows = cursor.fetchall()

            if not rows:
                ttk.Label(frame, text=f"No {table_name.lower()} records found.").pack(
                    anchor="w",
                    padx=10,
                    pady=10,
                )
                continue

            table_frame = ttk.Frame(frame)
            table_frame.pack(fill="both", expand=True)

            tree = ttk.Treeview(
                table_frame,
                columns=column_names,
                show="headings",
            )

            vertical_scroll = ttk.Scrollbar(
                table_frame,
                orient="vertical",
                command=tree.yview,
            )
            horizontal_scroll = ttk.Scrollbar(
                table_frame,
                orient="horizontal",
                command=tree.xview,
            )

            tree.configure(
                yscrollcommand=vertical_scroll.set,
                xscrollcommand=horizontal_scroll.set,
            )

            tree.grid(row=0, column=0, sticky="nsew")
            vertical_scroll.grid(row=0, column=1, sticky="ns")
            horizontal_scroll.grid(row=1, column=0, sticky="ew")

            table_frame.rowconfigure(0, weight=1)
            table_frame.columnconfigure(0, weight=1)

            for column in column_names:
                tree.heading(column, text=column.replace("_", " ").title())
                tree.column(column, width=150, minwidth=100, anchor="w")

            for row in rows:
                tree.insert("", "end", values=row)


def main():
    initialize_database()

    root = tk.Tk()
    AdminDatabaseViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()