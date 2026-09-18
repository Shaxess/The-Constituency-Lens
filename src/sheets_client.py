import os
import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

from config import INTERNAL_ONLY_FIELDS

load_dotenv()


def get_client():
    creds_path = os.getenv("GOOGLE_CREDS_PATH", "src/credentials.json")
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    client = gspread.authorize(creds)
    print(f"Auth OK with {creds_path}")
    return client


def get_sheet(client, tab_name="raw_posts"):
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise ValueError("GOOGLE_SHEET_ID missing in .env")
    sh = client.open_by_key(sheet_id)
    try:
        worksheet = sh.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        available = [ws.title for ws in sh.worksheets()]
        raise ValueError(
            f"Tab '{tab_name}' not found in '{sh.title}'. "
            f"Available tabs: {available}"
        )
    print(f"Sheet OK: {sh.title} -> tab '{worksheet.title}'")
    return worksheet


def get_raw_data(sheet):
    """
    INTERNAL USE ONLY. Returns every column, including author/link.
    Never call this from app.py's public-facing views or from any
    function that feeds the dashboard, exports, or paid reports.
    Use for verification/debugging only.
    """
    records = sheet.get_all_records()
    print(f"Raw data pulled: {len(records)} rows (includes internal-only fields)")
    return records


def get_public_safe_data(sheet):
    """
    Safe to use anywhere downstream: dashboard, aggregation, exports,
    paid reports. Strips INTERNAL_ONLY_FIELDS from every row before
    returning, so author/link can never leak into anything public-facing.
    """
    raw_records = sheet.get_all_records()
    safe_records = [
        {k: v for k, v in row.items() if k not in INTERNAL_ONLY_FIELDS}
        for row in raw_records
    ]
    print(f"Public-safe data ready: {len(safe_records)} rows "
          f"(stripped: {', '.join(INTERNAL_ONLY_FIELDS)})")
    return safe_records


if __name__ == "__main__":
    c = get_client()
    s = get_sheet(c)
    print("Connected successfully!")

    safe = get_public_safe_data(s)
    if safe:
        print("Sample public-safe row keys:", list(safe[0].keys()))
        assert not any(f in safe[0] for f in INTERNAL_ONLY_FIELDS), \
            "Leak detected: internal-only field present in public-safe data"
        print("Leak check passed — no internal-only fields present.")