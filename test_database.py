"""Verify that SQLAlchemy can connect to the configured database."""

import sys

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import app
from models import db

with app.app_context():
    try:
        db.session.execute(text("SELECT 1"))
        print("Database connection successful.")
    except SQLAlchemyError as error:
        print("Database connection failed.")
        print(error)
        sys.exit(1)
