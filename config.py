"""
config.py
─────────
Loads all configuration values from the .env file.
Every other module imports from here — nothing reads .env directly.
"""

import os
from dotenv import load_dotenv

# Load values from the .env file into environment variables
load_dotenv()


class Config:
    # ── Flask ──────────────────────────────────────────────────────────────
    # SECRET_KEY is used to sign session cookies.
    # If it is missing, we raise an error immediately so the app never starts
    # with an insecure default.
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is not set. Copy .env.example to .env and add a value."
        )

    # ── File uploads ───────────────────────────────────────────────────────
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "static/uploads")

    # Maximum upload size (bytes).  Default = 5 MB.
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))

    # Only these extensions are accepted for complaint photos.
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # ── Session cookie security ────────────────────────────────────────────
    # HttpOnly: JS cannot read the cookie (mitigates XSS cookie theft).
    SESSION_COOKIE_HTTPONLY = True

    # SameSite=Lax: protects against CSRF for most cases.
    SESSION_COOKIE_SAMESITE = "Lax"

    # Secure=True in production (HTTPS only). Set False for local HTTP dev.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"

    # ── MySQL ──────────────────────────────────────────────────────────────
    DB_HOST     = os.environ.get("DB_HOST", "localhost")
    DB_PORT     = int(os.environ.get("DB_PORT", 3306))
    DB_NAME     = os.environ.get("DB_NAME", "smart_waste_db")
    DB_USER     = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
