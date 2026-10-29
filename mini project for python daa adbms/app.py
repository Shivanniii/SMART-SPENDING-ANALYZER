
import subprocess
import sys
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st

from src.analyzer import (
    get_category_totals,
    get_month_summary,
    get_monthly_totals,
)
from src.auth import authenticate_user, create_user
from src.budget_manager import BudgetManager
from src.charts import render_category_chart, render_monthly_trend
from src.database import initialize_database
from src.transaction_manager import TransactionManager


# --------------------------------------------------
# APPLICATION SETUP
# --------------------------------------------------

st.set_page_config(
    page_title="Smart Spending Analyzer",
    page_icon="💸",
    layout="wide",
)

# Initialize the existing database.
# This does not delete existing database records.
initialize_database()

PROJECT_DIR = Path(__file__).resolve().parent


# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 8% 0%, #eeeaff 0, transparent 28%),
            #F7F7FB;
    }

    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #ECEAF4;
        padding: 18px 20px;
        border-radius: 18px;
        box-shadow: 0 8px 24px rgba(42, 35, 80, 0.05);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# LOGIN AND REGISTRATION
# --------------------------------------------------

def render_login():
    st.title("💸 Smart Spending Analyzer")

    st.caption(
        "Sign in or create your account to manage your personal spending."
    )

    login_tab, signup_tab = st.tabs(
        ["Log in", "Create account"]
    )

    # LOGIN
    with login_tab:
        with st.form("login_form"):
            login_username = st.text_input(
                "Username",
                key="login_username",
            )

            login_password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )

            login_clicked = st.form_submit_button(
                "Log in",
                type="primary",
                use_container_width=True,
            )

        if login_clicked:
            user = authenticate_user(
                login_username,
                login_password,
            )

            if user is None:
                st.error("Username or password is incorrect.")

            else:
                st.session_state["current_user"] = user
                st.rerun()

    # REGISTRATION
    with signup_tab:
        with st.form("signup_form"):
            signup_username = st.text_input(
                "Choose a username",
                key="signup_username",
            )

            signup_password = st.text_input(
                "Create a password",
                type="password",
                key="signup_password",
            )

            confirm_password = st.text_input(
                "Confirm password",
                type="password",
                key="signup_confirm_password",
            )

            signup_clicked = st.form_submit_button(
                "Create account",
                type="primary",
                use_container_width=True,
            )

        if signup_clicked:
            if signup_password != confirm_password:
                st.error("The passwords do not match.")

            else:
                try:
                    create_user(
                        signup_username,
                        signup_password,
                    )

                    st.success(
                        "Account created successfully! "
                        "Open the Log in tab to sign in."
                    )

                except ValueError as error:
                    st.error(str(error))


# --------------------------------------------------
# LAUNCH TKINTER DESKTOP TOOLS
# --------------------------------------------------

def launch_desktop_tool(tool_name, current_user):
    """Open a separate desktop window for the logged-in user."""

    tool_file = PROJECT_DIR / "ui" / "desktop_tools.py"

    if not tool_file.exists():
        st.error(
            "Desktop tools file was not found: "
            "ui/desktop_tools.py"
        )
        return

    try:
        subprocess.Popen(
            [
                sys.executable,
                str(tool_file),
                tool_name,
                str(current_user["user_id"]),
                str(current_user["username"]),
            ],
            cwd=str(PROJECT_DIR),
        )

        st.toast("Desktop tool opened.")

    except Exception as error:
        st.error(f"Could not open desktop tool: {error}")


# --------------------------------------------------
# SIDEBAR DESKTOP TOOLS
# --------------------------------------------------

def render_desktop_tools(current_user):
    with st.sidebar.expander(
        "🖥️ Desktop Tools",
        expanded=False,
    ):
        st.caption("Open a separate desktop window.")

        if st.button(
            "🧾 Quick Expense Entry",
            use_container_width=True,
        ):
            launch_desktop_tool("expense", current_user)

        if st.button(
            "📋 Transaction Manager",
            use_container_width=True,
        ):
            launch_desktop_tool("transactions", current_user)

        if st.button(
            "🎯 Budget Planner",
            use_container_width=True,
        ):
            launch_desktop_tool("budgets", current_user)

        if st.button(
            "📊 Financial Report Viewer",
            use_container_width=True,
        ):
            launch_desktop_tool("reports", current_user)

        if st.button(
            "🗂️ Personal Data Viewer",
            use_container_width=True,
        ):
            launch_desktop_tool("data", current_user)


# --------------------------------------------------
# HOME DASHBOARD
# --------------------------------------------------

def render_home():
    current_user = st.session_state["current_user"]

    today = date.today()
    current_month = today.strftime("%Y-%m")

    st.title(f"Hello, {current_user['username']} 👋")
    st.caption("Here’s your personal spending overview.")

    summary = get_month_summary(
        current_user,
        current_month,
    )

    category_totals = get_category_totals(
        current_user,
        current_month,
    )

    # SUMMARY CARDS
    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "Spent this month",
        f"₹{summary['total']:,.2f}",
    )

    metric2.metric(
        "Transactions",
        summary["transactions"],
    )

    metric3.metric(
        "Average expense",
        f"₹{summary['average']:,.2f}",
    )

    # CATEGORY CHART AND BUDGET OVERVIEW
    if category_totals.empty:
        st.info(
            "No expenses recorded this month yet. "
            "Open Transactions in the sidebar to add your first expense."
        )

    else:
        st.divider()

        top_category = category_totals.iloc[0]
        total_spent = float(summary["total"])

        top_share = (
            float(top_category["total"]) / total_spent * 100
            if total_spent > 0
            else 0
        )

        st.markdown(
            f"Your highest-spending category is "
            f"**{top_category['category']}** at "
            f"**₹{top_category['total']:,.2f}** "
            f"({top_share:.1f}% of this month's spending)."
        )

        chart_column, budget_column = st.columns(
            [1.4, 1],
            gap="large",
        )

        with chart_column:
            st.markdown("#### Spending by category")
            render_category_chart(category_totals)

        with budget_column:
            st.markdown("#### Overall budget")

            budget_manager = BudgetManager()

            budget_status = budget_manager.analyze(
                current_user,
                current_month,
                category_totals,
                total_spent,
            )

            overall_budget = next(
                (
                    item
                    for item in budget_status
                    if item["category"] == "Overall"
                ),
                None,
            )

            if overall_budget is None:
                st.info(
                    "You haven’t set an overall budget for this month."
                )

            else:
                st.progress(overall_budget["progress"])

                st.write(
                    f"Monthly limit: "
                    f"₹{overall_budget['limit']:,.2f}"
                )

                if overall_budget["over_budget"]:
                    st.warning(
                        f"₹{abs(overall_budget['remaining']):,.2f} "
                        f"over budget."
                    )
                else:
                    st.success(
                        f"₹{overall_budget['remaining']:,.2f} "
                        f"remaining."
                    )

    # MONTHLY SPENDING TREND
    st.divider()
    st.subheader("Monthly spending trend")

    monthly_totals = get_monthly_totals(current_user)
    render_monthly_trend(monthly_totals)

    # RECENT TRANSACTIONS
    st.divider()
    st.subheader("Recent transactions")

    transactions = TransactionManager().get_all(current_user)

    if not transactions:
        st.caption("Your recent expenses will appear here.")

    else:
        recent_rows = [
            {
                "Date": transaction.expense_date,
                "Amount (₹)": transaction.amount,
                "Category": transaction.category,
                "Payment": transaction.payment_method,
                "Description": transaction.description,
            }
            for transaction in transactions[:5]
        ]

        recent_table = pd.DataFrame(recent_rows)

        recent_table["Date"] = pd.to_datetime(
            recent_table["Date"]
        ).dt.strftime("%d %b %Y")

        st.dataframe(
            recent_table,
            use_container_width=True,
            hide_index=True,
        )


# --------------------------------------------------
# APPLICATION ENTRY POINT
# --------------------------------------------------

# Show login if no user is logged in.
if "current_user" not in st.session_state:
    render_login()
    st.stop()


# Get the logged-in user.
current_user = st.session_state["current_user"]


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.success(
    f"Signed in as {current_user['username']}"
)

# REFRESH CURRENT PAGE BUTTON
if st.sidebar.button(
    "🔄 Refresh Page",
    use_container_width=True,
    help="Reload the current page's data.",
):
    st.rerun()

# Desktop utilities
render_desktop_tools(current_user)

st.sidebar.divider()

# LOGOUT
if st.sidebar.button(
    "🚪 Log out",
    use_container_width=True,
):
    st.session_state.pop("current_user", None)
    st.rerun()


# --------------------------------------------------
# NAVIGATION
# --------------------------------------------------

pages = [
    st.Page(
        render_home,
        title="Home",
        icon="🏠",
        default=True,
    ),
    st.Page(
        "pages/1_Transactions.py",
        title="Transactions",
        icon="🧾",
    ),
    st.Page(
        "pages/2_Budgets.py",
        title="Budgets",
        icon="🎯",
    ),
    st.Page(
        "pages/3_Reports.py",
        title="Reports",
        icon="📊",
    ),
]

navigation = st.navigation(pages)
navigation.run()
