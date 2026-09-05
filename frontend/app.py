import pandas as pd
import streamlit as st

from frontend.api_client import (
    ApiClientError,
    create_expense,
    get_current_user,
    get_expenses,
    import_expenses,
    login_user,
    register_user,
)


st.set_page_config(
    page_title="SpendSense",
    layout="wide",
)


def initialize_session() -> None:
    st.session_state.setdefault("access_token", None)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("authentication_message", None)


def clear_session() -> None:
    st.session_state.access_token = None
    st.session_state.user = None


def show_login() -> None:
    st.subheader("Log in")

    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Log in", width="stretch")

    if not submitted:
        return

    if not email.strip() or not password:
        st.error("Email and password are required.")
        return

    try:
        result = login_user(email.strip(), password)
    except ApiClientError as exc:
        st.error(exc.message)
        return

    st.session_state.access_token = result["access_token"]
    st.session_state.user = result["user"]
    st.session_state.authentication_message = "You are now logged in."
    st.rerun()


def show_registration() -> None:
    st.subheader("Create an account")

    with st.form("registration_form"):
        username = st.text_input("Username", key="registration_username")
        email = st.text_input("Email", key="registration_email")
        password = st.text_input("Password", type="password", key="registration_password")
        confirmation = st.text_input(
            "Confirm password",
            type="password",
            key="registration_confirmation",
        )
        submitted = st.form_submit_button("Create account", width="stretch")

    if not submitted:
        return

    if not username.strip() or not email.strip() or not password:
        st.error("Username, email, and password are required.")
        return

    if password != confirmation:
        st.error("Passwords do not match.")
        return

    try:
        register_user(username.strip(), email.strip(), password)
    except ApiClientError as exc:
        st.error(exc.message)
        return

    st.success("Account created successfully. You can now log in.")


def show_authentication() -> None:
    st.title("SpendSense")
    st.caption("Track, Manage, and make sense of your spending.")

    login_tab, register_tab = st.tabs(["Log in", "Register"])
    with login_tab:
        show_login()
    with register_tab:
        show_registration()


def validate_session() -> bool:
    token = st.session_state.access_token
    if not token:
        return False

    try:
        st.session_state.user = get_current_user(token)
        return True
    except ApiClientError as exc:
        if exc.status_code == 401:
            clear_session()
            st.session_state.authentication_message = exc.message
            return False

        st.error(exc.message)
        st.info("Start the FastAPI server, then refresh this page.")
        st.stop()


def show_expense_form(token: str) -> None:
    st.subheader("Add expense")

    with st.form("expense_form", clear_on_submit=True):
        title = st.text_input("Title")
        description = st.text_input("Description")
        amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f")
        category = st.selectbox(
            "Category",
            ["food", "transport", "housing", "entertainment", "shopping", "health", "other"],
        )
        submitted = st.form_submit_button("Add expense")

    if not submitted:
        return

    if not title.strip() or not description.strip():
        st.error("Title and description are required.")
        return

    try:
        create_expense(
            token,
            title.strip(),
            description.strip(),
            amount,
            category,
        )
    except ApiClientError as exc:
        st.error(exc.message)
        return

    st.success("Expense added.")


def show_csv_import(token: str) -> None:
    st.subheader("Import expenses")
    st.caption(
        "Required columns: date, title, amount. "
        "Optional columns: description, category, transaction_id."
    )
    uploaded_file = st.file_uploader(
        "Upload a CSV file",
        type=["csv"],
        max_upload_size=2,
    )

    if not st.button("Import", disabled=uploaded_file is None):
        return

    try:
        result = import_expenses(
            token,
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "text/csv",
        )
    except ApiClientError as exc:
        st.error(exc.message)
        return

    data = result["data"]
    st.success("Expenses imported successfully.")
    st.write(
        f"Imported: {data['imported']} | "
        f"Duplicates skipped: {data['duplicates']} | "
        f"Failed: {data['failed']}"
    )

    if data["errors"]:
        st.warning("Some rows could not be imported:")
        for error in data["errors"]:
            st.write(f"Row {error['row']}: {error['message']}")


def show_expenses(token: str) -> None:
    st.subheader("Your expenses")

    try:
        expenses = get_expenses(token)
    except ApiClientError as exc:
        st.error(exc.message)
        return

    if not expenses:
        st.info("No expenses found.")
        return

    table = pd.DataFrame(expenses)
    table = table[["title", "amount", "category", "description", "created_at"]]
    table["created_at"] = pd.to_datetime(
        table["created_at"],
        format="ISO8601",
    ).dt.strftime("%Y-%m-%d")
    table = table.rename(
        columns={
            "title": "Title",
            "amount": "Amount",
            "category": "Category",
            "description": "Description",
            "created_at": "Date",
        }
    )
    st.dataframe(table, hide_index=True, width="stretch")


def show_authenticated_app() -> None:
    user = st.session_state.user

    with st.sidebar:
        st.subheader("SpendSense")
        st.write(f"Signed in as **{user['username']}**")
        if st.button("Log out", width="stretch"):
            clear_session()
            st.session_state.authentication_message = "You have been logged out."
            st.rerun()

    st.title("Expenses")
    show_expense_form(st.session_state.access_token)
    show_csv_import(st.session_state.access_token)
    show_expenses(st.session_state.access_token)


initialize_session()

authenticated = validate_session()
message = st.session_state.authentication_message
if message:
    st.info(message)
    st.session_state.authentication_message = None

if authenticated:
    show_authenticated_app()
else:
    show_authentication()

