def expense_body(title="Lunch"):
    return {
        "title": title,
        "description": "Lunch with a friend",
        "amount": 18.75,
        "show": True,
    }


def test_expenses_require_a_token(client):
    response = client.get("/expenses/")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_user_only_sees_their_own_expenses(client, first_user_headers):
    response = client.get("/expenses/", headers=first_user_headers)

    assert response.status_code == 200
    expenses = response.json()["data"]["expenses"]
    assert [expense["id"] for expense in expenses] == [1]
    assert expenses[0]["user_id"] == 1


def test_second_user_sees_a_different_expense(client, second_user_headers):
    response = client.get("/expenses/", headers=second_user_headers)

    assert response.status_code == 200
    assert [expense["id"] for expense in response.json()["data"]["expenses"]] == [2]


def test_create_expense_assigns_the_authenticated_user(client, first_user_headers):
    response = client.post(
        "/expenses/",
        headers=first_user_headers,
        json=expense_body(),
    )

    assert response.status_code == 201
    assert response.json()["data"]["expense"]["user_id"] == 1


def test_search_only_returns_the_current_users_expenses(client, first_user_headers):
    own_response = client.get(
        "/expenses/search/?title=beans",
        headers=first_user_headers,
    )
    other_response = client.get(
        "/expenses/search/?title=rent",
        headers=first_user_headers,
    )

    assert own_response.status_code == 200
    assert [item["id"] for item in own_response.json()["data"]["expenses"]] == [1]
    assert other_response.status_code == 200
    assert other_response.json()["data"]["expenses"] == []


def test_user_cannot_read_another_users_expense(client, first_user_headers):
    response = client.get("/expenses/2", headers=first_user_headers)

    assert response.status_code == 404


def test_user_cannot_update_another_users_expense(client, first_user_headers):
    response = client.put(
        "/expenses/2",
        headers=first_user_headers,
        json=expense_body("Changed"),
    )

    assert response.status_code == 404


def test_user_cannot_delete_another_users_expense(client, first_user_headers):
    response = client.delete("/expenses/2", headers=first_user_headers)

    assert response.status_code == 404


def test_user_can_update_their_own_expense(client, first_user_headers):
    response = client.put(
        "/expenses/1",
        headers=first_user_headers,
        json=expense_body("Updated lunch"),
    )

    assert response.status_code == 200
    assert response.json()["data"]["expense"]["title"] == "Updated lunch"


def test_user_can_delete_their_own_expense(client, first_user_headers):
    response = client.delete("/expenses/1", headers=first_user_headers)

    assert response.status_code == 200
    assert client.get("/expenses/1", headers=first_user_headers).status_code == 404


def test_create_expense_rejects_unrelated_json_fields(client, first_user_headers):
    response = client.post(
        "/expenses/",
        headers=first_user_headers,
        json={"firstName": "Sajal", "lastName": "Devkota", "city": "DC", "age": 19},
    )

    assert response.status_code == 422
    missing_fields = {error["loc"][-1] for error in response.json()["detail"]}
    assert missing_fields == {"title", "description", "amount"}


def test_expense_id_must_be_an_integer(client, first_user_headers):
    response = client.get("/expenses/not-an-id", headers=first_user_headers)

    assert response.status_code == 422


def test_expense_amount_must_be_positive(client, first_user_headers):
    response = client.post(
        "/expenses/",
        headers=first_user_headers,
        json=expense_body() | {"amount": 0},
    )

    assert response.status_code == 422


def test_expense_category_is_normalized(client, first_user_headers):
    response = client.post(
        "/expenses/",
        headers=first_user_headers,
        json=expense_body() | {"category": "  Food  "},
    )

    assert response.status_code == 201
    assert response.json()["data"]["expense"]["category"] == "food"
