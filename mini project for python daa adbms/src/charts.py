
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


def render_category_chart(category_totals):
    if category_totals.empty:
        st.info("No category spending to chart yet.")
        return

    fig, ax = plt.subplots()

    ax.bar(
        category_totals["category"],
        category_totals["total"],
    )

    ax.set_title("Spending by Category")
    ax.set_xlabel("Category")
    ax.set_ylabel("Amount (₹)")
    ax.tick_params(axis="x", rotation=30)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def render_monthly_trend(monthly_totals):
    if monthly_totals.empty:
        st.info("Add expenses to build your monthly spending trend.")
        return

    chart_data = monthly_totals.copy()
    chart_data["month"] = pd.to_datetime(
        chart_data["month"] + "-01"
    )
    chart_data = chart_data.tail(6)

    fig, ax = plt.subplots()

    ax.plot(
        chart_data["month"],
        chart_data["total"],
        marker="o",
    )

    ax.set_title("Monthly Spending Trend")
    ax.set_xlabel("Month")
    ax.set_ylabel("Amount (₹)")
    fig.autofmt_xdate()

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)