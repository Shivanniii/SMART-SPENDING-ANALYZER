
from datetime import date

import numpy as np
import pandas as pd
import streamlit as st

from src.analyzer import (
    get_category_totals,
    get_month_expenses,
    get_month_summary,
    get_monthly_totals,
)
from src.budget_manager import BudgetManager
from src.charts import render_category_chart, render_monthly_trend


# Check login
if "current_user" not in st.session_state:
    st.warning("Please log in from the Home page to view your reports.")
    st.stop()

current_user = st.session_state["current_user"]

st.title("📊 Spending Analysis")
st.caption("View your graphs and see what your spending shows.")


# Select month
selected_date = st.date_input(
    "Select a month",
    value=date.today().replace(day=1),
)
selected_month = selected_date.strftime("%Y-%m")


# Fetch data
summary = get_month_summary(current_user, selected_month)
category_totals = get_category_totals(current_user, selected_month)
monthly_totals = get_monthly_totals(current_user)
month_expenses = get_month_expenses(current_user, selected_month)


# Overview
st.subheader(f"Overview — {selected_month}")

col1, col2, col3 = st.columns(3)

col1.metric("Total spent", f"₹{summary['total']:,.2f}")
col2.metric("Number of expenses", summary["transactions"])
col3.metric("Average expense", f"₹{summary['average']:,.2f}")


# Spending graphs
st.divider()
st.subheader("Spending graphs")

chart_col1, chart_col2 = st.columns(2, gap="large")

with chart_col1:
    st.markdown("#### Spending by category")
    render_category_chart(category_totals)

with chart_col2:
    st.markdown("#### Monthly spending trend")
    render_monthly_trend(monthly_totals)


# Spending insights
st.divider()
st.subheader("What your spending shows")

if category_totals.empty:
    st.info("There are no expenses for this month yet.")

else:
    top_category = category_totals.iloc[0]
    total_spent = float(summary["total"])

    top_share = (
        float(top_category["total"]) / total_spent * 100
        if total_spent > 0
        else 0
    )

    st.markdown(
        f"- Your highest-spending category is "
        f"**{top_category['category']}** at "
        f"**₹{top_category['total']:,.2f}** "
        f"({top_share:.1f}% of this month's spending)."
    )

    # Compare with the previous month that has expenses
    if not monthly_totals.empty:
        month_list = monthly_totals["month"].tolist()

        if selected_month in month_list:
            month_index = month_list.index(selected_month)

            if month_index > 0:
                current_total = float(
                    monthly_totals.iloc[month_index]["total"]
                )
                previous_total = float(
                    monthly_totals.iloc[month_index - 1]["total"]
                )

                if previous_total > 0:
                    change = current_total - previous_total
                    percent = abs(change) / previous_total * 100

                    if change > 0:
                        st.markdown(
                            f"- Spending is **{percent:.1f}% higher** "
                            "than the previous month with recorded expenses."
                        )

                    elif change < 0:
                        st.markdown(
                            f"- Spending is **{percent:.1f}% lower** "
                            "than the previous month with recorded expenses."
                        )

                    else:
                        st.markdown(
                            "- Spending is unchanged from the previous "
                            "month with recorded expenses."
                        )


# NumPy statistical analysis
st.divider()
st.subheader("📈 Statistical Spending Insights")

if month_expenses.empty:
    st.info("Add expenses to view statistical spending insights.")

else:
    # Convert Pandas expense column into a NumPy array
    amounts = month_expenses["amount"].to_numpy(dtype=float)

    # Calculate statistics using NumPy
    mean_amount = np.mean(amounts)
    median_amount = np.median(amounts)
    standard_deviation = np.std(amounts)

    stat_col1, stat_col2, stat_col3 = st.columns(3)

    stat_col1.metric(
        "Mean expense",
        f"₹{mean_amount:,.2f}",
    )

    stat_col2.metric(
        "Median expense",
        f"₹{median_amount:,.2f}",
    )

    stat_col3.metric(
        "Standard deviation",
        f"₹{standard_deviation:,.2f}",
    )

    st.caption(
        "Mean is the average expense, median is the middle expense "
        "when sorted, and standard deviation indicates how much "
        "expense amounts vary."
    )

    # Identify unusually high expenses using a simple statistical rule
    threshold = mean_amount + (2 * standard_deviation)

    unusual_expenses = month_expenses[
        month_expenses["amount"] > threshold
    ].copy()

    st.markdown("#### Unusually high expenses")

    if unusual_expenses.empty:
        st.success(
            "No expenses exceeded the statistical threshold this month."
        )

    else:
        st.warning(
            f"{len(unusual_expenses)} expense(s) exceeded "
            f"₹{threshold:,.2f}."
        )

        unusual_display = unusual_expenses[
            ["expense_date", "amount", "category", "description"]
        ].rename(
            columns={
                "expense_date": "Date",
                "amount": "Amount (₹)",
                "category": "Category",
                "description": "Description",
            }
        )

        st.dataframe(
            unusual_display,
            hide_index=True,
            use_container_width=True,
        )


# Budget status
budget_manager = BudgetManager()

budget_status = budget_manager.analyze(
    current_user,
    selected_month,
    category_totals,
    summary["total"],
)

overall_budget = next(
    (
        item for item in budget_status
        if item["category"] == "Overall"
    ),
    None,
)

st.divider()
st.subheader("💰 Budget Status")

if overall_budget is None:
    st.markdown(
        "- No overall budget is set for this month. "
        "Set one on the Budgets page to include budget status here."
    )

elif overall_budget["over_budget"]:
    st.markdown(
        f"- You are **₹{abs(overall_budget['remaining']):,.2f} over** "
        "your overall monthly budget."
    )

else:
    st.markdown(
        f"- You have **₹{overall_budget['remaining']:,.2f} remaining** "
        "from your overall monthly budget."
    )


# Largest expenses
st.divider()
st.subheader("Largest expenses this month")

if month_expenses.empty:
    st.info("No expenses to display.")

else:
    largest_expenses = month_expenses.head(5).copy()

    largest_expenses["expense_date"] = pd.to_datetime(
        largest_expenses["expense_date"]
    ).dt.strftime("%d %b %Y")

    largest_expenses = largest_expenses.rename(
        columns={
            "expense_date": "Date",
            "amount": "Amount (₹)",
            "category": "Category",
            "payment_method": "Payment",
            "description": "Description",
        }
    )

    st.dataframe(
        largest_expenses[
            ["Date", "Amount (₹)", "Category", "Payment", "Description"]
        ],
        hide_index=True,
        use_container_width=True,
    )
