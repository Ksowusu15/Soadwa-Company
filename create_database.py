"""Initialize the configured database schema for local development or first setup."""

from app import app
from models import Admin, WebsiteSettings, db
import os


with app.app_context():
    db.create_all()

    settings = WebsiteSettings.query.first()
    if settings is None:
        db.session.add(WebsiteSettings(company_name="Soadwa Company Ltd"))

    if Admin.query.first() is None:
        password = os.getenv("ADMIN_PASSWORD", "").strip()
        if not password:
            raise RuntimeError(
                "ADMIN_PASSWORD must be set before creating the first admin account."
            )

        admin = Admin(
            username=os.getenv("ADMIN_USERNAME", "admin").strip(),
            email=os.getenv("ADMIN_EMAIL", "soadwacompany@gmail.com").strip(),
        )
        admin.set_password(password)
        db.session.add(admin)

    db.session.commit()
    print("Database schema and initial settings are ready.")
