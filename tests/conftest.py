import os
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


os.environ.setdefault("SECRET_KEY", "test-only-secret-key-not-for-production")

from app.core.db import Base, get_db
from app.core.jwt_helper import create_access_token
from app.core.security import hash_password
from app.main import app
from app.models.expense import Expense
from app.models.user import User


TEST_PASSWORD = "password123"
TEST_PASSWORD_HASH = hash_password(TEST_PASSWORD)


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
        db.add_all(
            [
                User(
                    id=1,
                    username="first-user",
                    email="first@example.com",
                    password=TEST_PASSWORD_HASH,
                    created_at=datetime.now(timezone.utc),
                ),
                User(
                    id=2,
                    username="second-user",
                    email="second@example.com",
                    password=TEST_PASSWORD_HASH,
                    created_at=datetime.now(timezone.utc),
                ),
            ]
        )
        db.add_all(
            [
                Expense(
                    id=1,
                    user_id=1,
                    title="Coffee beans",
                    description="Groceries",
                    amount=12.5,
                    show=True,
                ),
                Expense(
                    id=2,
                    user_id=2,
                    title="Apartment rent",
                    description="Housing",
                    amount=900,
                    show=True,
                ),
            ]
        )
        db.commit()

    def override_get_db():
        with testing_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def first_user_headers():
    token = create_access_token({"user_id": 1, "email": "first@example.com"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def second_user_headers():
    token = create_access_token({"user_id": 2, "email": "second@example.com"})
    return {"Authorization": f"Bearer {token}"}
