def test_main_api_workflow(client):
    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["message"] == "SpendSense API is running"

    registered = client.post(
        "/users/",
        json={
            "username": "workflow-user",
            "email": "workflow@example.com",
            "password": "password123",
        },
    )
    assert registered.status_code == 201

    logged_in = client.post(
        "/auth/",
        json={"email": "workflow@example.com", "password": "password123"},
    )
    assert logged_in.status_code == 200
    headers = {"Authorization": f"Bearer {logged_in.json()['access_token']}"}

    profile = client.get("/users/me", headers=headers)
    assert profile.status_code == 200

    budget = client.post(
        "/budgets/",
        headers=headers,
        json={"category": "food", "month": "2026-09", "limit_amount": 200},
    )
    assert budget.status_code == 201

    csv_content = (
        "date,title,description,amount\n"
        "2026-09-01,Lunch,With friends,24.50\n"
    )
    imported = client.post(
        "/expenses/import/",
        headers=headers,
        files={"file": ("expenses.csv", csv_content, "text/csv")},
    )
    assert imported.status_code == 200
    assert imported.json()["data"]["imported"] == 1

    expenses = client.get("/expenses/", headers=headers)
    assert expenses.status_code == 200
    assert len(expenses.json()["data"]["expenses"]) == 1

    budgets = client.get("/budgets/?month=2026-09", headers=headers)
    assert budgets.status_code == 200
    assert budgets.json()["data"]["budgets"][0]["spent"] == 24.5


def test_openapi_describes_csv_as_a_file_upload(client):
    schema = client.get("/openapi.json").json()
    request_body = schema["paths"]["/expenses/import/"]["post"]["requestBody"]

    assert "multipart/form-data" in request_body["content"]
