from datetime import date

import streamlit as st

from src.analyzer import get_category_totals, get_month_summary
from src.budget_manager import BudgetManager

if "current_user" not in st.session_state:
    st.warning("Please log in from the Home page to manage budgets.")
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

budget_manager = BudgetManager()

st.title("🎯 Monthly Budgets")
st.caption("Set spending limits and track how much remains.")

selected_date = st.date_input(
    "Choose a month",
    value=date.today().replace(day=1),
)
budget_month = selected_date.strftime("%Y-%m")

with st.form("budget_form"):
    st.subheader("Set or update a budget")
    budget_category = st.selectbox(
        "Budget type",
        ["Overall"] + CATEGORIES,
    )
    budget_amount = st.number_input(
        "Monthly limit (₹)",
        min_value=1.0,
        value=5000.0,
        step=500.0,
    )
    save_clicked = st.form_submit_button(
        "Save budget",
        type="primary",
    )

    if save_clicked:
        budget_manager.save(
            current_user,
            budget_month,
            budget_category,
            budget_amount,
        )
        st.success(f"{budget_category} budget saved for {budget_month}.")
        st.rerun()


st.divider()
st.subheader(f"Budget status — {budget_month}")

category_totals = get_category_totals(current_user, budget_month)
summary = get_month_summary(current_user, budget_month)

budget_status = budget_manager.analyze(
    current_user,
    budget_month,
    category_totals,
    summary["total"],
)

if not budget_status:
    st.info("No budgets set for this month yet.")
else:
    for item in budget_status:
        st.markdown(f"### {item['category']}")
        st.progress(item["progress"])

        col1, col2, col3 = st.columns(3)
        col1.metric("Budget", f"₹{item['limit']:,.2f}")
        col2.metric("Spent", f"₹{item['spent']:,.2f}")

        if item["over_budget"]:
            col3.metric(
                "Over budget by",
                f"₹{abs(item['remaining']):,.2f}",
            )
            st.warning(f"{item['category']} budget has been exceeded.")
        else:
            col3.metric("Remaining", f"₹{item['remaining']:,.2f}")

            if item["progress"] >= 0.8:
                st.info(
                    f"You have used at least 80% of the "
                    f"{item['category']} budget."
                )

        if st.button(
            f"Delete {item['category']} budget",
            key=f"delete_budget_{item['id']}",
        ):
            budget_manager.delete(current_user, item["id"])
            st.rerun()

        st.divider()