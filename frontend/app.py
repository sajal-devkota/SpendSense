from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from frontend.api_client import (
    ApiClientError,
    create_budget,
    create_expense,
    delete_budget,
    delete_expense,
    get_budgets,
    get_current_user,
    get_expenses,
    import_expenses,
    login_user,
    register_user,
    update_budget,
    update_expense,
)


EXPENSE_CATEGORIES = [
    "food",
    "transport",
    "housing",
    "entertainment",
    "shopping",
    "health",
    "other",
]

MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


st.set_page_config(
    page_title="SpendSense",
    layout="wide",
)


def category_input(label: str, key: str, current: str | None = None) -> str:
    selected = st.selectbox(
        label,
        EXPENSE_CATEGORIES,
        index=(
            EXPENSE_CATEGORIES.index(current)
            if current in EXPENSE_CATEGORIES
            else EXPENSE_CATEGORIES.index("other")
        ),
        format_func=str.title,
        key=f"{key}_choice",
    )
    custom = st.text_input(
        "Custom category (optional)",
        value=current if current and current not in EXPENSE_CATEGORIES else "",
        max_chars=50,
        key=f"{key}_custom",
    )
    return custom.strip().lower() or selected


def initialize_session() -> None:
    st.session_state.setdefault("access_token", None)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("authentication_message", None)
    st.session_state.setdefault("expense_message", None)
    st.session_state.setdefault("budget_message", None)
    st.session_state.setdefault("import_result", None)


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
        amount = st.number_input("Amount (USD)", min_value=0.01, step=0.01, format="%.2f")
        category = category_input("Category", "new_expense_category")
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

    st.session_state.expense_message = "Expense added."
    st.rerun()


def show_expense_actions(token: str, expenses: list[dict]) -> None:
    st.subheader("Edit or delete expense")

    expenses_by_id = {expense["id"]: expense for expense in expenses}
    selected_id = st.selectbox(
        "Select an expense",
        list(expenses_by_id),
        format_func=lambda expense_id: expenses_by_id[expense_id]["title"],
    )
    selected = expenses_by_id[selected_id]

    with st.form(f"edit_expense_{selected_id}"):
        title = st.text_input("Title", value=selected["title"], key=f"edit_title_{selected_id}")
        description = st.text_input(
            "Description",
            value=selected["description"],
            key=f"edit_description_{selected_id}",
        )
        amount = st.number_input(
            "Amount (USD)",
            min_value=0.01,
            value=float(selected["amount"]),
            step=0.01,
            format="%.2f",
            key=f"edit_amount_{selected_id}",
        )
        category = category_input(
            "Category",
            f"edit_category_{selected_id}",
            current=selected["category"],
        )
        update_submitted = st.form_submit_button("Update expense")

    if update_submitted:
        if not title.strip() or not description.strip():
            st.error("Title and description are required.")
            return

        try:
            update_expense(
                token,
                selected_id,
                title.strip(),
                description.strip(),
                amount,
                category,
                selected["show"],
            )
        except ApiClientError as exc:
            st.error(exc.message)
            return

        st.session_state.expense_message = "Expense updated."
        st.rerun()

    st.warning("Deleting an expense cannot be undone.")
    if st.button("Delete expense", key=f"delete_expense_{selected_id}"):
        try:
            delete_expense(token, selected_id)
        except ApiClientError as exc:
            st.error(exc.message)
            return

        st.session_state.expense_message = "Expense deleted."
        st.rerun()


def show_csv_import(token: str) -> None:
    st.subheader("Import expenses")
    st.caption(
        "Required columns: date, title, amount. "
        "Optional columns: description, category, transaction_id."
    )

    previous_result = st.session_state.import_result
    if previous_result:
        st.success("Expenses imported successfully.")
        st.write(
            f"Imported: {previous_result['imported']} | "
            f"Duplicates skipped: {previous_result['duplicates']} | "
            f"Failed: {previous_result['failed']}"
        )
        if previous_result["errors"]:
            st.warning("Some rows could not be imported:")
            for error in previous_result["errors"]:
                st.write(f"Row {error['row']}: {error['message']}")
        st.session_state.import_result = None

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

    st.session_state.import_result = result["data"]
    st.rerun()


def show_spending_summary(expenses: list[dict]) -> None:
    chart_data = pd.DataFrame(expenses)
    chart_data["amount"] = pd.to_numeric(chart_data["amount"], errors="coerce")
    chart_data["created_at"] = pd.to_datetime(
        chart_data["created_at"],
        format="ISO8601",
        errors="coerce",
    )
    chart_data = chart_data.dropna(subset=["amount"])

    st.subheader("Spending overview")
    total = chart_data["amount"].sum()
    count = len(chart_data)
    average = total / count if count else 0

    total_column, count_column, average_column = st.columns(3)
    total_column.metric("Total spending", f"${total:,.2f}")
    count_column.metric("Expenses", count)
    average_column.metric("Average expense", f"${average:,.2f}")

    category_totals = (
        chart_data.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )
    category_totals["category"] = category_totals["category"].str.title()

    category_chart = px.bar(
        category_totals,
        x="category",
        y="amount",
        labels={"category": "Category", "amount": "Amount"},
        title="Spending by category",
    )
    category_chart.update_layout(showlegend=False)
    category_chart.update_yaxes(tickprefix="$")

    dated_expenses = chart_data.dropna(subset=["created_at"]).copy()
    dated_expenses["month"] = dated_expenses["created_at"].dt.strftime("%Y-%m")
    current_year = date.today().year
    year_months = pd.DataFrame(
        {
            "month": [f"{current_year}-{month:02d}" for month in range(1, 13)],
            "month_label": [name[:3] for name in MONTH_NAMES],
        }
    )
    monthly_totals = dated_expenses[
        dated_expenses["created_at"].dt.year == current_year
    ].groupby("month", as_index=False)["amount"].sum()
    monthly_totals = year_months.merge(monthly_totals, on="month", how="left")
    monthly_totals["amount"] = monthly_totals["amount"].fillna(0)

    monthly_chart = px.line(
        monthly_totals,
        x="month_label",
        y="amount",
        markers=True,
        labels={"month_label": "Month", "amount": "Amount"},
        title=f"Monthly spending ({current_year})",
    )
    monthly_chart.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=year_months["month_label"].tolist(),
    )
    monthly_chart.update_yaxes(tickprefix="$", rangemode="tozero")

    category_column, monthly_column = st.columns(2)
    category_column.plotly_chart(category_chart, width="stretch")
    monthly_column.plotly_chart(monthly_chart, width="stretch")


def show_expenses(token: str, expenses: list[dict]) -> None:
    st.subheader("Your expenses")

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
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "Amount": st.column_config.NumberColumn(format="$%.2f"),
        },
    )
    show_expense_actions(token, expenses)


def show_budget_progress(budgets: list[dict]) -> None:
    if not budgets:
        st.info("No budgets found for this month.")
        return

    for budget in budgets:
        percentage_used = float(budget["percentage_used"])
        progress_value = min(max(percentage_used / 100, 0.0), 1.0)

        with st.container(border=True):
            st.write(f"**{budget['category'].title()}**")
            limit_column, spent_column, remaining_column = st.columns(3)
            limit_column.metric("Limit", f"${budget['limit_amount']:,.2f}")
            spent_column.metric("Spent", f"${budget['spent']:,.2f}")
            remaining_column.metric("Remaining", f"${budget['remaining']:,.2f}")
            st.progress(progress_value, text=f"{percentage_used:.0f}% used")

            if budget["warning"]:
                st.warning(budget["warning"])


def show_budget_actions(token: str, budgets: list[dict]) -> None:
    if not budgets:
        return

    st.subheader("Edit or delete budget")
    budgets_by_id = {budget["id"]: budget for budget in budgets}
    selected_id = st.selectbox(
        "Select a budget",
        list(budgets_by_id),
        format_func=lambda budget_id: budgets_by_id[budget_id]["category"].title(),
    )
    selected = budgets_by_id[selected_id]

    with st.form(f"edit_budget_{selected_id}"):
        limit_amount = st.number_input(
            "Budget limit (USD)",
            min_value=0.01,
            value=float(selected["limit_amount"]),
            step=1.0,
            format="%.2f",
            key=f"budget_limit_{selected_id}",
        )
        update_submitted = st.form_submit_button("Update budget")

    if update_submitted:
        try:
            update_budget(token, selected_id, limit_amount)
        except ApiClientError as exc:
            st.error(exc.message)
            return

        st.session_state.budget_message = "Budget updated."
        st.rerun()

    st.warning("Deleting a budget cannot be undone.")
    if st.button("Delete budget", key=f"delete_budget_{selected_id}"):
        try:
            delete_budget(token, selected_id)
        except ApiClientError as exc:
            st.error(exc.message)
            return

        st.session_state.budget_message = "Budget deleted."
        st.rerun()


def create_budget_and_refresh(
    token: str,
    category: str,
    selected_month: str,
    limit_amount: float,
) -> None:
    try:
        create_budget(token, category, selected_month, limit_amount)
    except ApiClientError as exc:
        st.error(exc.message)
        return

    st.session_state.budget_message = "Budget created."
    st.rerun()


def show_budget_summary(
    token: str,
    expenses: list[dict],
    budgets: list[dict],
    selected_month: str,
) -> None:
    budget_categories = {budget["category"] for budget in budgets}
    monthly_expenses = [
        expense
        for expense in expenses
        if str(expense["created_at"])[:7] == selected_month
    ]
    unallocated = [
        expense
        for expense in monthly_expenses
        if expense["category"] not in budget_categories
    ]

    total_spending = sum(float(expense["amount"]) for expense in monthly_expenses)
    unallocated_spending = sum(float(expense["amount"]) for expense in unallocated)

    total_column, unallocated_column = st.columns(2)
    total_column.metric("Total expenses", f"${total_spending:,.2f}")
    unallocated_column.metric("Not allocated", f"${unallocated_spending:,.2f}")

    if unallocated:
        st.write("**Expenses without an allocated budget**")
        table = pd.DataFrame(unallocated)[["title", "category", "amount"]]
        table = table.rename(
            columns={"title": "Title", "category": "Category", "amount": "Amount"}
        )
        st.dataframe(
            table,
            hide_index=True,
            width="stretch",
            column_config={
                "Amount": st.column_config.NumberColumn(format="$%.2f"),
            },
        )

        unallocated_categories = sorted(
            {expense["category"] for expense in unallocated}
        )
        with st.form(f"allocate_budget_{selected_month}"):
            category = st.selectbox(
                "Category to budget",
                unallocated_categories,
                format_func=str.title,
            )
            limit_amount = st.number_input(
                "Budget limit (USD)",
                min_value=0.01,
                step=1.0,
                format="%.2f",
            )
            allocate_submitted = st.form_submit_button("Add budget limit")

        if allocate_submitted:
            create_budget_and_refresh(
                token,
                category,
                selected_month,
                limit_amount,
            )
    elif monthly_expenses:
        st.success("All expenses are covered by a budget.")


def show_budgets(token: str, expenses: list[dict]) -> None:
    st.subheader("Monthly budgets")

    today = date.today()
    month_column, year_column = st.columns(2)
    month_number = month_column.selectbox(
        "Month",
        range(1, 13),
        index=today.month - 1,
        format_func=lambda month: MONTH_NAMES[month - 1],
    )
    year = year_column.number_input(
        "Year",
        min_value=2000,
        max_value=2100,
        value=today.year,
        step=1,
    )
    selected_month = f"{int(year):04d}-{month_number:02d}"

    message = st.session_state.budget_message
    if message:
        st.success(message)
        st.session_state.budget_message = None

    with st.form("create_budget_form", clear_on_submit=True):
        category = category_input("Budget category", "new_budget_category")
        limit_amount = st.number_input(
            "Limit amount (USD)",
            min_value=0.01,
            step=1.0,
            format="%.2f",
        )
        create_submitted = st.form_submit_button("Create budget")

    if create_submitted:
        create_budget_and_refresh(token, category, selected_month, limit_amount)

    try:
        budgets = get_budgets(token, selected_month)
    except ApiClientError as exc:
        st.error(exc.message)
        return

    show_budget_summary(token, expenses, budgets, selected_month)
    show_budget_progress(budgets)
    show_budget_actions(token, budgets)


def show_authenticated_app() -> None:
    user = st.session_state.user
    token = st.session_state.access_token

    with st.sidebar:
        st.subheader("SpendSense")
        st.write(f"Signed in as **{user['username']}**")
        if st.button("Log out", width="stretch"):
            clear_session()
            st.session_state.authentication_message = "You have been logged out."
            st.rerun()
        page = st.radio(
            "Navigation",
            ["Overview", "Expenses", "Budgets", "Import CSV"],
        )

    st.title("SpendSense")
    if page == "Import CSV":
        show_csv_import(token)
        return

    try:
        expenses = get_expenses(token)
    except ApiClientError as exc:
        st.error(exc.message)
        return

    if page == "Overview":
        if expenses:
            show_spending_summary(expenses)
        else:
            st.info("No expenses found.")
    elif page == "Expenses":
        expense_message = st.session_state.expense_message
        if expense_message:
            st.success(expense_message)
            st.session_state.expense_message = None

        show_expense_form(token)
        show_expenses(token, expenses)
    elif page == "Budgets":
        show_budgets(token, expenses)


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

