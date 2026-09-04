from frontend import api_client


class FakeResponse:
    def __init__(self, status_code=200, body=None, content=b"response"):
        self.status_code = status_code
        self.body = body or {}
        self.content = content
        self.ok = 200 <= status_code < 400

    def json(self):
        return self.body


def test_login_uses_the_auth_endpoint(monkeypatch):
    recorded = {}

    def fake_request(method, url, **kwargs):
        recorded.update(method=method, url=url, kwargs=kwargs)
        return FakeResponse(
            body={"access_token": "token", "user": {"id": 1, "username": "first-user"}}
        )

    monkeypatch.setattr(api_client.requests, "request", fake_request)

    response = api_client.login_user("first@example.com", "password123")

    assert recorded["method"] == "POST"
    assert recorded["url"] == f"{api_client.API_URL}/auth/"
    assert recorded["kwargs"]["json"] == {
        "email": "first@example.com",
        "password": "password123",
    }
    assert response["access_token"] == "token"


def test_registration_sends_the_expected_fields(monkeypatch):
    recorded = {}

    def fake_request(method, url, **kwargs):
        recorded.update(method=method, url=url, kwargs=kwargs)
        return FakeResponse(status_code=201, body={"status": "success"})

    monkeypatch.setattr(api_client.requests, "request", fake_request)

    api_client.register_user("new-user", "new@example.com", "password123")

    assert recorded["url"] == f"{api_client.API_URL}/users/"
    assert recorded["kwargs"]["json"]["username"] == "new-user"


def test_current_user_request_includes_the_bearer_token(monkeypatch):
    recorded = {}

    def fake_request(method, url, **kwargs):
        recorded.update(method=method, url=url, kwargs=kwargs)
        return FakeResponse(body={"data": {"user": {"id": 1, "username": "first-user"}}})

    monkeypatch.setattr(api_client.requests, "request", fake_request)

    user = api_client.get_current_user("jwt-token")

    assert recorded["kwargs"]["headers"] == {"Authorization": "Bearer jwt-token"}
    assert user["username"] == "first-user"

