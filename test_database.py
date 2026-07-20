"""Verify that Flask-SQLAlchemy can connect to the configured MySQL database."""

import sys

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import app
from models import db

with app.app_context():
    try:
        db.session.execute(text("SELECT 1"))
        print("MySQL connection successful.")
    except SQLAlchemyError as error:
        print("MySQL connection failed.")
        print(error)
        sys.exit(1)
