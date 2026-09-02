TEST_PASSWORD = "password123"


def test_new_user_can_register(client):
    response = client.post(
        "/users/",
        json={
            "username": "new-user",
            "email": "new@example.com",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["user"]["email"] == "new@example.com"


def test_duplicate_email_is_rejected(client):
    response = client.post(
        "/users/",
        json={
            "username": "different-name",
            "email": "first@example.com",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 400


def test_login_returns_an_access_token(client):
    response = client.post(
        "/auth/",
        json={"email": "first@example.com", "password": TEST_PASSWORD},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_invalid_login_is_rejected(client):
    response = client.post(
        "/auth/",
        json={"email": "first@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_user_can_view_their_own_profile(client, first_user_headers):
    response = client.get("/users/me", headers=first_user_headers)

    assert response.status_code == 200
    assert response.json()["data"]["user"]["email"] == "first@example.com"


def test_profile_requires_authentication(client):
    response = client.get("/users/me")

    assert response.status_code == 401


def test_arbitrary_user_profiles_are_not_public(client, first_user_headers):
    response = client.get("/users/2", headers=first_user_headers)

    assert response.status_code == 404


def test_user_can_update_their_own_profile(client, first_user_headers):
    response = client.put(
        "/users/me",
        headers=first_user_headers,
        json={"username": "updated-user"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["user"]["username"] == "updated-user"


def test_deleting_account_invalidates_its_token(client, first_user_headers):
    response = client.delete("/users/me", headers=first_user_headers)

    assert response.status_code == 200
    assert client.get("/users/me", headers=first_user_headers).status_code == 401
