import subprocess
import sys
from pathlib import Path

import streamlit as st

from src.auth import create_user

if "current_user" not in st.session_state:
    st.warning("Please log in from the Home page.")
    st.stop()

current_user = st.session_state["current_user"]

if current_user["role"] != "admin":
    st.error("This page is available to administrators only.")
    st.stop()


PROJECT_DIR = Path(__file__).resolve().parents[1]
VIEWER_PATH = PROJECT_DIR / "ui" / "admin_db_viewer.py"

st.title("🔐 Admin")
st.caption("Manage app users and open the database viewer.")

st.subheader("Create a user account")

with st.form("create_user_form", clear_on_submit=True):
    username = st.text_input("New username")
    password = st.text_input("Temporary password", type="password")
    password_again = st.text_input("Confirm password", type="password")

    create_clicked = st.form_submit_button(
        "Create user",
        type="primary",
    )

    if create_clicked:
        if password != password_again:
            st.error("The passwords do not match.")
        else:
            try:
                create_user(username, password, role="user")
                st.success(f"User account '{username}' created.")
            except ValueError as error:
                st.error(str(error))


st.divider()
st.subheader("Database viewer")

st.write(
    "The Tkinter viewer opens as a separate desktop window and asks "
    "you to confirm your admin login."
)

if st.button("Open Tkinter database viewer"):
    if not VIEWER_PATH.exists():
        st.error("The database viewer file has not been added yet.")
    else:
        subprocess.Popen(
            [sys.executable, str(VIEWER_PATH)],
            cwd=str(PROJECT_DIR),
        )
        st.success("The database viewer has been opened.")