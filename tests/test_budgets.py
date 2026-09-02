from datetime import datetime, timezone

from app.models.expense import Expense


def budget_body(category="food", month=None, limit_amount=100):
    return {
        "category": category,
        "month": month or datetime.now(timezone.utc).strftime("%Y-%m"),
        "limit_amount": limit_amount,
    }


def test_budgets_require_a_token(client):
    response = client.get("/budgets/")

    assert response.status_code == 401


def test_user_can_create_a_monthly_budget(client, first_user_headers):
    response = client.post(
        "/budgets/",
        headers=first_user_headers,
        json=budget_body("Food", limit_amount=50),
    )

    assert response.status_code == 201
    budget = response.json()["data"]["budget"]
    assert budget["category"] == "food"
    assert budget["limit_amount"] == 50


def test_duplicate_budget_is_rejected(client, first_user_headers):
    client.post("/budgets/", headers=first_user_headers, json=budget_body())
    response = client.post("/budgets/", headers=first_user_headers, json=budget_body())

    assert response.status_code == 400


def test_users_can_have_separate_budgets(client, first_user_headers, second_user_headers):
    first = client.post("/budgets/", headers=first_user_headers, json=budget_body())
    second = client.post("/budgets/", headers=second_user_headers, json=budget_body())
    first_user_budgets = client.get("/budgets/", headers=first_user_headers)

    assert first.status_code == 201
    assert second.status_code == 201
    budgets = first_user_budgets.json()["data"]["budgets"]
    assert len(budgets) == 1
    assert budgets[0]["id"] == first.json()["data"]["budget"]["id"]


def test_budget_progress_only_uses_current_users_expenses(client, first_user_headers,
                                                          second_user_headers):
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    client.post(
        "/expenses/",
        headers=first_user_headers,
        json={"title": "Lunch", "description": "Cafe", "amount": 85,
              "category": "food", "show": True},
    )
    client.post(
        "/expenses/",
        headers=second_user_headers,
        json={"title": "Dinner", "description": "Restaurant", "amount": 500,
              "category": "food", "show": True},
    )
    client.post(
        "/budgets/",
        headers=first_user_headers,
        json=budget_body("food", month, 100),
    )

    response = client.get(f"/budgets/?month={month}", headers=first_user_headers)

    assert response.status_code == 200
    budget = response.json()["data"]["budgets"][0]
    assert budget["spent"] == 85
    assert budget["remaining"] == 15
    assert budget["percentage_used"] == 85
    assert budget["warning"] == "Budget almost reached"


def test_budget_shows_when_limit_is_exceeded(client, first_user_headers):
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    client.post(
        "/expenses/",
        headers=first_user_headers,
        json={"title": "Groceries", "description": "Weekly shop", "amount": 120,
              "category": "food", "show": True},
    )
    client.post(
        "/budgets/",
        headers=first_user_headers,
        json=budget_body("food", month, 100),
    )

    response = client.get(f"/budgets/?month={month}", headers=first_user_headers)
    budget = response.json()["data"]["budgets"][0]

    assert budget["remaining"] == -20
    assert budget["warning"] == "Budget exceeded"


def test_user_cannot_update_another_users_budget(client, first_user_headers,
                                                  second_user_headers):
    created = client.post(
        "/budgets/",
        headers=second_user_headers,
        json=budget_body(),
    )
    budget_id = created.json()["data"]["budget"]["id"]

    response = client.put(
        f"/budgets/{budget_id}",
        headers=first_user_headers,
        json={"limit_amount": 200},
    )

    assert response.status_code == 404


def test_user_can_update_and_delete_their_budget(client, first_user_headers):
    created = client.post(
        "/budgets/",
        headers=first_user_headers,
        json=budget_body(),
    )
    budget_id = created.json()["data"]["budget"]["id"]

    updated = client.put(
        f"/budgets/{budget_id}",
        headers=first_user_headers,
        json={"limit_amount": 250},
    )
    deleted = client.delete(f"/budgets/{budget_id}", headers=first_user_headers)

    assert updated.status_code == 200
    assert updated.json()["data"]["budget"]["limit_amount"] == 250
    assert deleted.status_code == 200


def test_invalid_budget_month_is_rejected(client, first_user_headers):
    response = client.post(
        "/budgets/",
        headers=first_user_headers,
        json=budget_body(month="2026-13"),
    )

    assert response.status_code == 422


def test_budget_limit_must_be_positive(client, first_user_headers):
    response = client.post(
        "/budgets/",
        headers=first_user_headers,
        json=budget_body(limit_amount=0),
    )

    assert response.status_code == 422


def test_blank_budget_category_is_rejected(client, first_user_headers):
    response = client.post(
        "/budgets/",
        headers=first_user_headers,
        json=budget_body(category="   "),
    )

    assert response.status_code == 422
