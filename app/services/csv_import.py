import csv
import hashlib
import io
from datetime import datetime, time, timezone
from decimal import Decimal, InvalidOperation


MAX_CSV_SIZE = 2 * 1024 * 1024
MAX_CSV_ROWS = 1000
REQUIRED_COLUMNS = {"date", "title", "amount"}

CATEGORY_KEYWORDS = {
    "food": ("grocery", "restaurant", "lunch", "dinner", "coffee", "cafe"),
    "transport": ("uber", "lyft", "taxi", "bus", "train", "fuel", "gas"),
    "housing": ("rent", "mortgage", "utility", "electricity", "internet"),
    "entertainment": ("movie", "netflix", "spotify", "game"),
    "shopping": ("amazon", "clothing", "clothes", "mall"),
    "health": ("pharmacy", "doctor", "hospital", "medicine"),
}


def read_csv(content: bytes) -> list[tuple[int, dict[str, str]]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV file must use UTF-8 encoding") from exc

    try:
        reader = csv.DictReader(io.StringIO(text), strict=True)
        if not reader.fieldnames:
            raise ValueError("CSV file is missing a header row")

        headers = [header.strip().lower() for header in reader.fieldnames if header]
        missing = REQUIRED_COLUMNS - set(headers)
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
        if len(headers) != len(set(headers)):
            raise ValueError("CSV file contains duplicate column names")

        rows = []
        for row_number, original_row in enumerate(reader, start=2):
            if None in original_row:
                raise ValueError(f"Row {row_number} has more values than columns")
            row = {
                str(key).strip().lower(): (value or "").strip()
                for key, value in original_row.items()
                if key is not None
            }
            if not any(row.values()):
                continue
            if len(rows) >= MAX_CSV_ROWS:
                raise ValueError(f"CSV file can contain at most {MAX_CSV_ROWS} rows")
            rows.append((row_number, row))
    except csv.Error as exc:
        raise ValueError("CSV file could not be read") from exc

    return rows


def prepare_expense(row: dict[str, str]) -> dict:
    title = row.get("title", "").strip()
    if not title:
        raise ValueError("title is required")
    if len(title) > 50:
        raise ValueError("title must be 50 characters or fewer")

    description = row.get("description", "").strip() or title
    if len(description) > 100:
        raise ValueError("description must be 100 characters or fewer")

    amount = parse_amount(row.get("amount", ""))
    created_at = parse_date(row.get("date", ""))

    category = row.get("category", "").strip().lower()
    if not category:
        category = guess_category(title, description)
    if len(category) > 50:
        raise ValueError("category must be 50 characters or fewer")

    expense = {
        "title": title,
        "description": description,
        "amount": amount,
        "category": category,
        "show": True,
        "created_at": created_at,
    }
    expense["import_hash"] = make_import_hash(expense, row.get("transaction_id", ""))
    return expense


def parse_amount(value: str) -> Decimal:
    cleaned = value.strip().replace("$", "").replace(",", "")
    try:
        amount = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError("amount must be a valid number") from exc

    if not amount.is_finite() or amount <= 0:
        raise ValueError("amount must be greater than zero")
    if amount.as_tuple().exponent < -2:
        raise ValueError("amount can have at most 2 decimal places")
    if amount > Decimal("9999999999.99"):
        raise ValueError("amount is too large")
    return amount.quantize(Decimal("0.01"))


def parse_date(value: str) -> datetime:
    for date_format in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            parsed = datetime.strptime(value.strip(), date_format).date()
            return datetime.combine(parsed, time.min, tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError("date must use YYYY-MM-DD, MM/DD/YYYY, or MM/DD/YY")


def guess_category(title: str, description: str) -> str:
    text = f"{title} {description}".lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "other"


def make_import_hash(expense: dict, transaction_id: str = "") -> str:
    transaction_id = transaction_id.strip().lower()
    if len(transaction_id) > 100:
        raise ValueError("transaction_id must be 100 characters or fewer")

    if transaction_id:
        fields = ("transaction_id", transaction_id)
    else:
        fields = (
            "transaction",
            expense["created_at"].date().isoformat(),
            expense["title"].strip().lower(),
            expense["description"].strip().lower(),
            format(expense["amount"], ".2f"),
        )
    return hashlib.sha256("|".join(fields).encode("utf-8")).hexdigest()
