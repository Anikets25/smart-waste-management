"""
utils/helpers.py
────────────────
Reusable helpers shared across all three portals (citizen, admin, staff).
"""

import os
import uuid
import string
import random
from datetime import datetime

import mysql.connector
from werkzeug.utils import secure_filename

from config import Config


# ── Database ───────────────────────────────────────────────────────────────

def get_db_connection():
    """Opens and returns a new MySQL connection (use cursor(dictionary=True) for dict rows)."""
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        autocommit=False,
    )


# ── ID generators ──────────────────────────────────────────────────────────

def generate_complaint_id():
    """Returns WMS-YYYYMMDD-XXXXXX  (36^6 ≈ 2 billion combos/day)."""
    date_part   = datetime.now().strftime("%Y%m%d")
    chars       = string.ascii_uppercase + string.digits
    random_part = "".join(random.choices(chars, k=6))
    return f"WMS-{date_part}-{random_part}"


def generate_employee_id():
    """Returns STAFF-XXXXXXXX for new staff members."""
    chars = string.ascii_uppercase + string.digits
    return "STAFF-" + "".join(random.choices(chars, k=6))


# ── File uploads ───────────────────────────────────────────────────────────

def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    )


def save_uploaded_file(file_storage, subfolder: str = "") -> str | None:
    """
    Validates and saves an uploaded file.
    subfolder: optional sub-directory inside UPLOAD_FOLDER (e.g. 'after').
    Returns relative path like 'uploads/after/<uuid>.jpg' or None on failure.
    """
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        return None

    original    = secure_filename(file_storage.filename)
    extension   = original.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{extension}"

    if subfolder:
        folder = os.path.join(Config.UPLOAD_FOLDER, subfolder)
        os.makedirs(folder, exist_ok=True)
        save_path   = os.path.join(folder, unique_name)
        return_path = f"uploads/{subfolder}/{unique_name}"
    else:
        save_path   = os.path.join(Config.UPLOAD_FOLDER, unique_name)
        return_path = f"uploads/{unique_name}"

    file_storage.save(save_path)
    return return_path


# ── Green points ───────────────────────────────────────────────────────────

GREEN_POINTS_PER_COMPLAINT = 10   # awarded when complaint is marked Resolved


def award_green_points(conn, citizen_id: int, complaint_db_id: int, points: int, reason: str):
    """
    Credits `points` to a citizen and logs the transaction.
    Uses the passed-in connection so it participates in the caller's transaction.
    """
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE citizens SET green_points = green_points + %s WHERE id = %s",
        (points, citizen_id),
    )
    cursor.execute(
        "INSERT INTO green_points_log (citizen_id, complaint_id, points, reason) VALUES (%s,%s,%s,%s)",
        (citizen_id, complaint_db_id, points, reason),
    )
    cursor.execute(
        "UPDATE complaints SET green_points_awarded = %s WHERE id = %s",
        (points, complaint_db_id),
    )
    cursor.close()


# ── Formatting ─────────────────────────────────────────────────────────────

STATUS_INFO = {
    "Submitted":    {"label": "Submitted",    "color": "secondary"},
    "Under Review": {"label": "Under Review", "color": "warning"},
    "In Progress":  {"label": "In Progress",  "color": "info"},
    "Resolved":     {"label": "Resolved",     "color": "success"},
}

CATEGORY_ICONS = {
    "Plastic":   "🧴",
    "Wet Waste": "🗑️",
    "Dry Waste": "📦",
    "Other":     "♻️",
}


def get_status_info(status: str) -> dict:
    return STATUS_INFO.get(status, {"label": status, "color": "secondary"})


def format_datetime(dt) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%d %b %Y, %I:%M %p")
