"""
Input validation helpers for file uploads, data integrity, and form inputs.
"""

import re
from datetime import datetime
from typing import Optional
import pandas as pd
from utils.constants import REQUIRED_INVOICE_COLUMNS


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_date(date_str: str, fmt: str = "%Y-%m-%d") -> bool:
    """Validate date string format."""
    try:
        datetime.strptime(str(date_str), fmt)
        return True
    except (ValueError, TypeError):
        return False


def validate_amount(amount) -> bool:
    """Validate that amount is a positive number."""
    try:
        return float(amount) >= 0
    except (ValueError, TypeError):
        return False


def validate_invoice_dataframe(df: pd.DataFrame) -> dict:
    """
    Validate an uploaded invoice DataFrame.
    Returns dict with 'valid' bool and 'errors' list.
    """
    errors = []

    # Check required columns
    df_columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    missing = [col for col in REQUIRED_INVOICE_COLUMNS if col not in df_columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return {"valid": False, "errors": errors}

    # Standardize column names
    df.columns = df_columns

    # Check for empty rows
    if df.empty:
        errors.append("The uploaded file contains no data rows.")
        return {"valid": False, "errors": errors}

    # Validate each row
    row_errors = []
    for idx, row in df.iterrows():
        row_num = idx + 2  # Account for header row + 0-index

        if pd.isna(row.get("invoice_number")) or str(row["invoice_number"]).strip() == "":
            row_errors.append(f"Row {row_num}: Invoice number is empty")

        if pd.isna(row.get("company_name")) or str(row["company_name"]).strip() == "":
            row_errors.append(f"Row {row_num}: Company name is empty")

        if not validate_amount(row.get("amount")):
            row_errors.append(f"Row {row_num}: Invalid amount '{row.get('amount')}'")

        if row.get("contact_email") and not pd.isna(row.get("contact_email")):
            if not validate_email(str(row["contact_email"]).strip()):
                row_errors.append(f"Row {row_num}: Invalid email '{row['contact_email']}'")

    if row_errors:
        errors.extend(row_errors[:20])  # Limit to first 20 row errors
        if len(row_errors) > 20:
            errors.append(f"... and {len(row_errors) - 20} more row errors")

    return {"valid": len(errors) == 0, "errors": errors}


def validate_phone(phone: str) -> bool:
    """Validate phone number (basic)."""
    if not phone:
        return True  # Phone is optional
    cleaned = re.sub(r'[\s\-\(\)\+]', '', str(phone))
    return cleaned.isdigit() and 7 <= len(cleaned) <= 15


def sanitize_string(value: Optional[str]) -> str:
    """Sanitize string input."""
    if value is None:
        return ""
    return str(value).strip()
