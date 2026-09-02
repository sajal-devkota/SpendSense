# SpendSense

A personal finance application built with FastAPI, SQL, and Python.

## Run the API

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
fastapi dev app/main.py
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation.

## Log in and retrieve expenses

1. Send `POST http://127.0.0.1:8000/auth/` with a JSON body:

   ```json
   {
     "email": "your-email@example.com",
     "password": "your-password"
   }
   ```

2. Copy only the value of `access_token` from the response.
3. In Requestly, send `GET http://127.0.0.1:8000/expenses/` and set the
   authorization type to **Bearer Token**. Paste the token into its token field.

Use **GET**, not POST, when you only want to view the saved expenses. A GET
request does not need a JSON body.

The equivalent header is:

```text
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Do not paste the token into the URL's `expense_id` field. That field accepts only
an integer, such as `GET /expenses/2`.

To create an expense, use `POST /expenses/` with authorization and this JSON body:

```json
{
  "title": "Coffee",
  "description": "Coffee with friends",
  "amount": 4.5,
  "show": true
}
```

Fields such as `firstName`, `lastName`, `city`, and `age` are not expense fields
and will correctly produce a `422 Unprocessable Entity` response.

Search uses `GET /expenses/search/?title=your-search-text`.

## Tests

```powershell
pytest -q
```
