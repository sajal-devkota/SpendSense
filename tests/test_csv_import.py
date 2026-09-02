def csv_file(content: str):
    return {"file": ("expenses.csv", content, "text/csv")}


def test_csv_import_requires_login(client):
    response = client.post(
        "/expenses/import/",
        files=csv_file("date,title,amount\n2026-09-01,Lunch,12.50"),
    )

    assert response.status_code == 401


def test_imports_csv_and_guesses_missing_categories(client, first_user_headers):
    content = (
        "date,title,description,amount,category\n"
        "2026-09-01,Morning coffee,Cafe visit,4.75,\n"
        "09/02/2026,Monthly pass,Train ticket,55.00,Transport\n"
    )

    response = client.post(
        "/expenses/import/",
        headers=first_user_headers,
        files=csv_file(content),
    )
    data = response.json()["data"]

    assert response.status_code == 200
    assert data["imported"] == 2
    assert data["duplicates"] == 0
    assert data["failed"] == 0
    assert data["expenses"][0]["category"] == "food"
    assert data["expenses"][0]["created_at"].startswith("2026-09-01")
    assert data["expenses"][1]["category"] == "transport"


def test_description_is_optional(client, first_user_headers):
    content = "date,title,amount\n2026-09-01,Book,18.99\n"

    response = client.post(
        "/expenses/import/",
        headers=first_user_headers,
        files=csv_file(content),
    )
    expense = response.json()["data"]["expenses"][0]

    assert response.status_code == 200
    assert expense["description"] == "Book"


def test_repeated_csv_rows_are_skipped(client, first_user_headers):
    content = (
        "date,title,description,amount\n"
        "2026-09-01,Lunch,With friends,20.00\n"
        "2026-09-01,Lunch,With friends,20.00\n"
    )

    first = client.post(
        "/expenses/import/",
        headers=first_user_headers,
        files=csv_file(content),
    )
    second = client.post(
        "/expenses/import/",
        headers=first_user_headers,
        files=csv_file(content),
    )

    assert first.json()["data"]["imported"] == 1
    assert first.json()["data"]["duplicates"] == 1
    assert second.json()["data"]["imported"] == 0
    assert second.json()["data"]["duplicates"] == 2


def test_category_change_does_not_bypass_duplicate_detection(client, first_user_headers):
    first_content = "date,title,amount,category\n2026-09-01,Lunch,12.00,food\n"
    second_content = "date,title,amount,category\n2026-09-01,Lunch,12.00,dining\n"

    client.post(
        "/expenses/import/",
        headers=first_user_headers,
        files=csv_file(first_content),
    )
    response = client.post(
        "/expenses/import/",
        headers=first_user_headers,
        files=csv_file(second_content),
    )

    assert response.json()["data"]["imported"] == 0
    assert response.json()["data"]["duplicates"] == 1


def test_transaction_id_can_distinguish_matching_transactions(client, first_user_headers):
    content = (
        "transaction_id,date,title,amount\n"
        "bank-101,2026-09-01,Coffee,4.00\n"
        "bank-102,2026-09-01,Coffee,4.00\n"
    )

    response = client.post(
        "/expenses/import/",
        headers=first_user_headers,
        files=csv_file(content),
    )

    assert response.json()["data"]["imported"] == 2
    assert response.json()["data"]["duplicates"] == 0


def test_duplicate_detection_is_separate_for_each_user(client, first_user_headers,
                                                        second_user_headers):
    content = "date,title,amount\n2026-09-01,Bus ticket,3.00\n"

    first = client.post(
        "/expenses/import/",
        headers=first_user_headers,
        files=csv_file(content),
    )
    second = client.post(
        "/expenses/import/",
        headers=second_user_headers,
        files=csv_file(content),
    )

    assert first.json()["data"]["imported"] == 1
    assert second.json()["data"]["imported"] == 1


def test_invalid_rows_are_reported_without_blocking_valid_rows(client, first_user_headers):
    content = (
        "date,title,amount\n"
        "2026-09-01,Groceries,42.25\n"
        "not-a-date,Taxi,10.00\n"
        "2026-09-03,Movie,-5.00\n"
    )

    response = client.post(
        "/expenses/import/",
        headers=first_user_headers,
        files=csv_file(content),
    )
    data = response.json()["data"]

    assert response.status_code == 200
    assert data["imported"] == 1
    assert data["failed"] == 2
    assert data["errors"][0]["row"] == 3
    assert data["errors"][1]["row"] == 4


def test_missing_required_columns_returns_422(client, first_user_headers):
    response = client.post(
        "/expenses/import/",
        headers=first_user_headers,
        files=csv_file("title,amount\nLunch,12.00"),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Missing required columns: date"


def test_invalid_utf8_returns_422(client, first_user_headers):
    response = client.post(
        "/expenses/import/",
        headers=first_user_headers,
        files={"file": ("expenses.csv", b"\xff\xfe", "text/csv")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "CSV file must use UTF-8 encoding"


def test_malformed_csv_returns_422_instead_of_server_error(client, first_user_headers):
    content = 'date,title,amount\n2026-09-01,"unfinished,12.00\n'

    response = client.post(
        "/expenses/import/",
        headers=first_user_headers,
        files=csv_file(content),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "CSV file could not be read"


def test_file_larger_than_two_mb_is_rejected(client, first_user_headers):
    response = client.post(
        "/expenses/import/",
        headers=first_user_headers,
        files={"file": ("expenses.csv", b"x" * (2 * 1024 * 1024 + 1), "text/csv")},
    )

    assert response.status_code == 413


def test_imported_expenses_are_visible_only_to_their_owner(client, first_user_headers,
                                                           second_user_headers):
    content = "date,title,amount\n2026-09-01,Private purchase,7.00\n"
    imported = client.post(
        "/expenses/import/",
        headers=first_user_headers,
        files=csv_file(content),
    )
    expense_id = imported.json()["data"]["expenses"][0]["id"]

    owner_response = client.get(f"/expenses/{expense_id}", headers=first_user_headers)
    other_response = client.get(f"/expenses/{expense_id}", headers=second_user_headers)

    assert owner_response.status_code == 200
    assert other_response.status_code == 404


def test_imported_expense_is_included_in_monthly_budget(client, first_user_headers):
    client.post(
        "/budgets/",
        headers=first_user_headers,
        json={"category": "food", "month": "2026-09", "limit_amount": 100},
    )
    client.post(
        "/expenses/import/",
        headers=first_user_headers,
        files=csv_file("date,title,amount\n2026-09-01,Lunch,25.00\n"),
    )

    response = client.get("/budgets/?month=2026-09", headers=first_user_headers)
    budget = response.json()["data"]["budgets"][0]

    assert budget["spent"] == 25
    assert budget["remaining"] == 75
