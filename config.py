import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _normalize_database_url(value: str) -> str:
    """Normalize provider URLs for SQLAlchemy 2.x drivers."""
    value = (value or "").strip()
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    if value.startswith("mysql://"):
        return value.replace("mysql://", "mysql+pymysql://", 1)
    return value


def build_database_uri():
    """Use Neon/hosted DATABASE_URL in production, with PostgreSQL as the preferred fallback."""
    # Preferred production path: Neon or another hosted PostgreSQL provider.
    # Neon connection strings typically include sslmode=require and may use a
    # pooled endpoint whose hostname contains -pooler.
    explicit_url = _normalize_database_url(os.getenv("DATABASE_URL", ""))
    if explicit_url:
        return explicit_url

    db_engine = os.getenv("DB_ENGINE", "postgresql").strip().lower()

    if db_engine == "mysql":
        return URL.create(
            drivername="mysql+pymysql",
            username=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            database=os.getenv("MYSQL_DATABASE", "soadwa_company"),
            query={"charset": "utf8mb4"},
        )

    return URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "soadwa_company"),
    )


class Config:
    APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
    SECRET_KEY = os.getenv("SECRET_KEY") or (
        "development-only-secret" if APP_ENV != "production" else None
    )

    SQLALCHEMY_DATABASE_URI = build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    MAX_CONTENT_LENGTH = 20 * 1024 * 1024
    UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = APP_ENV == "production"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = APP_ENV == "production"
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # Admin sessions expire after 10 minutes of inactivity. The remember
    # cookie uses the same rolling window so it cannot silently restore an
    # expired admin session after the inactivity timeout.
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=10)
    SESSION_REFRESH_EACH_REQUEST = True
    REMEMBER_COOKIE_DURATION = timedelta(minutes=10)
    REMEMBER_COOKIE_REFRESH_EACH_REQUEST = True

    PREFERRED_URL_SCHEME = "https" if APP_ENV == "production" else "http"
