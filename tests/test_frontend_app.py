from pathlib import Path

from streamlit.testing.v1 import AppTest

from frontend import api_client


APP_FILE = Path(__file__).parents[1] / "frontend" / "app.py"


def load_app():
    return AppTest.from_file(str(APP_FILE)).run()


def test_login_stores_the_token_and_logout_clears_it(monkeypatch):
    user = {"id": 1, "username": "first-user", "email": "first@example.com"}
    monkeypatch.setattr(
        api_client,
        "login_user",
        lambda email, password: {"access_token": "jwt-token", "user": user},
    )
    monkeypatch.setattr(api_client, "get_current_user", lambda token: user)

    app = load_app()
    app.text_input[0].input("first@example.com")
    app.text_input[1].input("password123")
    app.button[0].click().run()

    assert not list(app.exception)
    assert app.session_state["access_token"] == "jwt-token"
    assert app.session_state["user"]["username"] == "first-user"
    assert app.button[0].label == "Log out"

    app.button[0].click().run()

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
    app.run()

    assert not list(app.exception)
    assert app.session_state["access_token"] is None
    assert app.session_state["user"] is None
    assert app.info[0].value == "Your session expired. Please log in again."
    assert [tab.label for tab in app.tabs] == ["Log in", "Register"]
