from datetime import date

import pandas as pd
import streamlit as st

from src.models import Transaction
from src.transaction_manager import TransactionManager

if "current_user" not in st.session_state:
    st.warning("Please log in from the Home page to view your transactions.")
    st.stop()

current_user = st.session_state["current_user"]

CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Entertainment",
    "Health",
    "Education",
    "Other",
]

PAYMENT_METHODS = [
    "UPI",
    "Cash",
    "Card",
    "Bank transfer",
    "Other",
]

manager = TransactionManager()

st.title("🧾 Transactions")
st.caption("Add, search, sort, edit, and delete your expenses.")


# ---------- Add a transaction ----------
with st.expander("＋ Add a transaction", expanded=True):
    with st.form("add_transaction_form", clear_on_submit=True):
        expense_date = st.date_input("Date", value=date.today())
        amount = st.number_input(
            "Amount (₹)",
            min_value=0.01,
            value=100.00,
            step=50.00,
        )
        category = st.selectbox("Category", CATEGORIES)
        payment_method = st.selectbox("Payment method", PAYMENT_METHODS)
        description = st.text_input(
            "Description",
            placeholder="Example: Lunch with friends",
        )

        add_clicked = st.form_submit_button(
            "Save transaction",
            type="primary",
        )

        if add_clicked:
            transaction = Transaction(
                user_id=current_user["user_id"],
                expense_date=expense_date.isoformat(),
                amount=amount,
                category=category,
                payment_method=payment_method,
                description=description,
            )
            manager.add(current_user, transaction)
            st.success("Transaction saved.")
            st.rerun()


# ---------- Search, filter, and sort ----------
st.divider()
st.subheader("Your transactions")

all_transactions = manager.get_all(current_user)

if not all_transactions:
    st.info("No transactions yet. Add one using the form above.")
    st.stop()

search_col, category_col, payment_col = st.columns([2, 1, 1])

with search_col:
    search_text = st.text_input(
        "Search",
        placeholder="Description, category, or payment method",
    )

with category_col:
    selected_category = st.selectbox(
        "Category",
        ["All categories"] + CATEGORIES,
    )

with payment_col:
    selected_payment = st.selectbox(
        "Payment method",
        ["All methods"] + PAYMENT_METHODS,
    )

sort_choice = st.selectbox(
    "Sort transactions",
    [
        "Newest first",
        "Oldest first",
        "Amount: high to low",
        "Amount: low to high",
    ],
)

transactions = manager.search(current_user, search_text)

if selected_category != "All categories":
    transactions = [
        item for item in transactions
        if item.category == selected_category
    ]

if selected_payment != "All methods":
    transactions = [
        item for item in transactions
        if item.payment_method == selected_payment
    ]

if sort_choice == "Newest first":
    transactions = manager.merge_sort(
        transactions,
        key="expense_date",
        descending=True,
    )
elif sort_choice == "Oldest first":
    transactions = manager.merge_sort(
        transactions,
        key="expense_date",
    )
elif sort_choice == "Amount: high to low":
    transactions = manager.merge_sort(
        transactions,
        key="amount",
        descending=True,
    )
else:
    transactions = manager.merge_sort(
        transactions,
        key="amount",
    )


# ---------- Display transactions ----------
if transactions:
    table_rows = [
        {
            "Date": item.expense_date,
            "Amount (₹)": item.amount,
            "Category": item.category,
            "Payment": item.payment_method,
            "Description": item.description,
        }
        for item in transactions
    ]

    transaction_table = pd.DataFrame(table_rows)
    transaction_table["Date"] = pd.to_datetime(
        transaction_table["Date"]
    ).dt.strftime("%d %b %Y")

    st.dataframe(
        transaction_table,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No transactions match your search and filters.")


# ---------- Edit or delete ----------
st.divider()
st.subheader("Edit or delete a transaction")

if not transactions:
    st.caption("No matching transactions are available.")
else:
    transaction_options = {
        item.transaction_id: (
            f"#{item.transaction_id} · {item.expense_date} · "
            f"{item.category} · ₹{item.amount:.2f}"
        )
        for item in transactions
    }

    selected_id = st.selectbox(
        "Choose a transaction",
        options=list(transaction_options.keys()),
        format_func=lambda item_id: transaction_options[item_id],
    )

    selected_transaction = next(
        item for item in transactions
        if item.transaction_id == selected_id
    )

    with st.form("edit_transaction_form"):
        edited_date = st.date_input(
            "Edit date",
            value=date.fromisoformat(selected_transaction.expense_date),
        )
        edited_amount = st.number_input(
            "Edit amount (₹)",
            min_value=0.01,
            value=float(selected_transaction.amount),
            step=50.00,
        )
        edited_category = st.selectbox(
            "Edit category",
            CATEGORIES,
            index=CATEGORIES.index(selected_transaction.category),
        )

        payment_index = (
            PAYMENT_METHODS.index(selected_transaction.payment_method)
            if selected_transaction.payment_method in PAYMENT_METHODS
            else 0
        )
        edited_payment = st.selectbox(
            "Edit payment method",
            PAYMENT_METHODS,
            index=payment_index,
        )
        edited_description = st.text_input(
            "Edit description",
            value=selected_transaction.description,
        )

        update_clicked = st.form_submit_button(
            "Save changes",
            type="primary",
        )

        if update_clicked:
            updated_transaction = Transaction(
                transaction_id=selected_id,
                user_id=current_user["user_id"],
                expense_date=edited_date.isoformat(),
                amount=edited_amount,
                category=edited_category,
                payment_method=edited_payment,
                description=edited_description,
            )
            manager.update(current_user, updated_transaction)
            st.success("Transaction updated.")
            st.rerun()

    confirm_delete = st.checkbox(
        f"Confirm deletion of transaction #{selected_id}"
    )

    if st.button("Delete selected transaction"):
        if confirm_delete:
            manager.delete(current_user, selected_id)
            st.success("Transaction deleted.")
            st.rerun()
        else:
            st.warning("Tick the confirmation box before deleting.")