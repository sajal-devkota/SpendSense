import os
from typing import Any

import requests


API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT = 10


class ApiClientError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _error_message(response: requests.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return f"The server returned an error ({response.status_code})."

    detail = body.get("detail") if isinstance(body, dict) else None
    if isinstance(detail, str):
        return detail

    if isinstance(detail, list):
        messages = [item.get("msg") for item in detail if isinstance(item, dict)]
        messages = [message for message in messages if message]
        if messages:
            return "; ".join(messages)

    message = body.get("message") if isinstance(body, dict) else None
    if isinstance(message, str):
        return message

    return f"The server returned an error ({response.status_code})."


def request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    timeout: int = REQUEST_TIMEOUT,
    **kwargs: Any,
) -> dict[str, Any]:
    headers = dict(kwargs.pop("headers", {}))
    if token:
        headers.update(auth_headers(token))

    try:
        response = requests.request(
            method,
            f"{API_URL}{path}",
            headers=headers,
            timeout=timeout,
            **kwargs,
        )
    except requests.Timeout as exc:
        raise ApiClientError("The request timed out. Please try again.") from exc
    except requests.ConnectionError as exc:
        raise ApiClientError(
            "Could not connect to the SpendSense API. Make sure FastAPI is running."
        ) from exc
    except requests.RequestException as exc:
        raise ApiClientError("The API request failed. Please try again.") from exc

    if response.status_code == 401 and token:
        raise ApiClientError(
            "Your session expired. Please log in again.",
            status_code=401,
        )

    if not response.ok:
        raise ApiClientError(
            _error_message(response),
            status_code=response.status_code,
        )

    if response.status_code == 204 or not response.content:
        return {}

    try:
        return response.json()
    except ValueError as exc:
        raise ApiClientError("The API returned an invalid response.") from exc


def register_user(username: str, email: str, password: str) -> dict[str, Any]:
    return request(
        "POST",
        "/users/",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )


def login_user(email: str, password: str) -> dict[str, Any]:
    return request(
        "POST",
        "/auth/",
        json={"email": email, "password": password},
    )


def get_current_user(token: str) -> dict[str, Any]:
    response = request("GET", "/users/me", token=token)
    return response["data"]["user"]
