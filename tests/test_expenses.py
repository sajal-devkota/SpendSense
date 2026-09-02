from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.core.jwt_helper import create_access_token
from app.main import app
from app.models.expense import Expense
from app.models.user import User


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with testing_session() as db:
        db.add(
            User(
                id=1,
                username="test-user",
                email="test@example.com",
                password="not-used-by-these-tests",
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )
        db.add(
            Expense(
                id=1,
                title="Coffee beans",
                description="Groceries",
                amount=12.5,
                show=True,
            )
        )
        db.commit()

    def override_get_db():
        with testing_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def authorization_header():
    token = create_access_token({"user_id": 1, "email": "test@example.com"})
    return {"Authorization": f"Bearer {token}"}


def test_expenses_require_a_token(client):
    response = client.get("/expenses/")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_pasted_bearer_token_returns_expenses(client, authorization_header):
    response = client.get("/expenses/", headers=authorization_header)

    assert response.status_code == 200
    assert response.json()["data"]["expenses"][0]["title"] == "Coffee beans"


def test_search_is_not_mistaken_for_an_integer_id(client, authorization_header):
    response = client.get(
        "/expenses/search/?title=beans",
        headers=authorization_header,
    )

    assert response.status_code == 200
    assert [item["title"] for item in response.json()["data"]["expenses"]] == [
        "Coffee beans"
    ]


def test_create_expense_rejects_unrelated_json_fields(client, authorization_header):
    response = client.post(
        "/expenses/",
        headers=authorization_header,
        json={"firstName": "Sajal", "lastName": "Devkota", "city": "DC", "age": 19},
    )

    assert response.status_code == 422
    missing_fields = {error["loc"][-1] for error in response.json()["detail"]}
    assert missing_fields == {"title", "description", "amount"}


def test_create_expense_accepts_the_expense_json_body(client, authorization_header):
    response = client.post(
        "/expenses/",
        headers=authorization_header,
        json={
            "title": "Lunch",
            "description": "Lunch with a friend",
            "amount": 18.75,
            "show": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["expense"]["title"] == "Lunch"


def test_expense_id_must_be_an_integer(client, authorization_header):
    response = client.get("/expenses/not-an-id", headers=authorization_header)

    assert response.status_code == 422
