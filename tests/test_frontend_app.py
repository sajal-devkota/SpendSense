from pathlib import Path

from streamlit.testing.v1 import AppTest

from frontend import api_client


APP_FILE = Path(__file__).parents[1] / "frontend" / "app.py"


def load_app():
    return AppTest.from_file(str(APP_FILE)).run(timeout=10)


def test_login_stores_the_token_and_logout_clears_it(monkeypatch):
    user = {"id": 1, "username": "first-user", "email": "first@example.com"}
    expense = {
        "id": 1,
        "user_id": 1,
        "title": "Lunch",
        "description": "Lunch with friends",
        "amount": 12.5,
        "category": "food",
        "show": True,
        "created_at": "2026-09-05T12:00:00",
    }
    monkeypatch.setattr(
        api_client,
        "login_user",
        lambda email, password: {"access_token": "jwt-token", "user": user},
    )
    monkeypatch.setattr(api_client, "get_current_user", lambda token: user)
    monkeypatch.setattr(api_client, "get_expenses", lambda token: [expense])

    app = load_app()
    app.text_input[0].input("first@example.com")
    app.text_input[1].input("password123")
    app.button[0].click().run()

    assert not list(app.exception)
    assert app.session_state["access_token"] == "jwt-token"
    assert app.session_state["user"]["username"] == "first-user"
    logout_button = next(button for button in app.button if button.label == "Log out")

    logout_button.click().run()

    assert app.session_state["access_token"] is None
    assert app.session_state["user"] is None
    assert [tab.label for tab in app.tabs] == ["Log in", "Register"]


def test_registration_checks_that_passwords_match(monkeypatch):
    called = False

    def fake_registration(username, email, password):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(api_client, "register_user", fake_registration)

    app = load_app()
    app.text_input[2].input("new-user")
    app.text_input[3].input("new@example.com")
    app.text_input[4].input("password123")
    app.text_input[5].input("different-password")
    app.button[1].click().run()

    assert not called
    assert app.error[0].value == "Passwords do not match."


def test_expired_token_returns_the_user_to_login(monkeypatch):
    def expired_token(token):
        raise api_client.ApiClientError(
            "Your session expired. Please log in again.",
            status_code=401,
        )

    monkeypatch.setattr(api_client, "get_current_user", expired_token)

    app = AppTest.from_file(str(APP_FILE))
    app.session_state["access_token"] = "expired-token"
    app.session_state["user"] = {"username": "first-user"}
    app.run(timeout=10)

    assert not list(app.exception)
    assert app.session_state["access_token"] is None
    assert app.session_state["user"] is None
    assert app.info[0].value == "Your session expired. Please log in again."
    assert [tab.label for tab in app.tabs] == ["Log in", "Register"]


def test_duplicate_budget_error_does_not_hide_existing_budgets(monkeypatch):
    user = {"id": 1, "username": "first-user", "email": "first@example.com"}
    budget = {
        "id": 1,
        "category": "food",
        "month": "2026-09",
        "limit_amount": 100.0,
        "spent": 25.0,
        "remaining": 75.0,
        "percentage_used": 25.0,
        "warning": None,
    }
    budget_requests = 0

    def duplicate_budget(*args):
        raise api_client.ApiClientError(
            "Budget already exists for this category and month",
            status_code=400,
        )

    def get_existing_budget(token, month):
        nonlocal budget_requests
        budget_requests += 1
        return [budget]

    monkeypatch.setattr(api_client, "get_current_user", lambda token: user)
    monkeypatch.setattr(api_client, "get_expenses", lambda token: [])
    monkeypatch.setattr(api_client, "create_budget", duplicate_budget)
    monkeypatch.setattr(api_client, "get_budgets", get_existing_budget)

    app = AppTest.from_file(str(APP_FILE))
    app.session_state["access_token"] = "jwt-token"
    app.session_state["user"] = user
    app.run(timeout=10)
    app.radio[0].set_value("Budgets").run(timeout=10)

    create_button = next(button for button in app.button if button.label == "Create budget")
    create_button.click().run(timeout=10)

    assert not list(app.exception)
    assert budget_requests == 2
    assert app.error[0].value == "Budget already exists for this category and month"


def test_custom_expense_category_is_sent_to_the_api(monkeypatch):
    user = {"id": 1, "username": "first-user", "email": "first@example.com"}
    created = {}

    def record_expense(token, title, description, amount, category):
        created.update(
            title=title,
            description=description,
            amount=amount,
            category=category,
        )
        return {"status": "success"}

    monkeypatch.setattr(api_client, "get_current_user", lambda token: user)
    monkeypatch.setattr(api_client, "get_expenses", lambda token: [])
    monkeypatch.setattr(api_client, "create_expense", record_expense)

    app = AppTest.from_file(str(APP_FILE))
    app.session_state["access_token"] = "jwt-token"
    app.session_state["user"] = user
    app.run(timeout=10)
    app.radio[0].set_value("Expenses").run(timeout=10)

    custom_category = next(
        text_input
        for text_input in app.text_input
        if text_input.label == "Custom category (optional)"
    )
    custom_category.input("Education").run(timeout=10)
    custom_category = next(
        text_input
        for text_input in app.text_input
        if text_input.label == "Custom category (optional)"
    )
    assert custom_category.value == "Education"

    title = next(text_input for text_input in app.text_input if text_input.label == "Title")
    description = next(
        text_input for text_input in app.text_input if text_input.label == "Description"
    )
    title.input("Course").run(timeout=10)
    description = next(
        text_input for text_input in app.text_input if text_input.label == "Description"
    )
    description.input("Online course").run(timeout=10)
    custom_category = next(
        text_input
        for text_input in app.text_input
        if text_input.label == "Custom category (optional)"
    )
    assert custom_category.value == "Education"

    add_button = next(button for button in app.button if button.label == "Add expense")
    add_button.click().run(timeout=10)

    assert not list(app.exception)
    assert created["category"] == "education"
    assert app.radio[0].value == "Expenses"
