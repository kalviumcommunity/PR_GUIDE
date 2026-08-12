import os


class Config:
    """Base configuration, populated from environment variables.

    Keep this file free of secrets — real values live in `.env` (see
    `.env.example`) and are loaded via python-dotenv in `run.py`.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://openpulse:openpulse@localhost:5432/openpulse"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET")
    GITHUB_OAUTH_REDIRECT_URI = os.environ.get(
        "GITHUB_OAUTH_REDIRECT_URI", "http://localhost:5000/auth/github/callback"
    )
    GITHUB_API_BASE = "https://api.github.com"
    GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    # We only need to *read* public repo data and identify the user.
    # No write scopes requested.
    GITHUB_OAUTH_SCOPES = "read:user"

    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    TOKEN_ENCRYPTION_KEY = os.environ.get("TOKEN_ENCRYPTION_KEY")

    # Session cookie hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
