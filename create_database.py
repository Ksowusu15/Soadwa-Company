"""Create the MySQL database used by the dealership application."""

import os
import sys

import pymysql
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("MYSQL_HOST", "127.0.0.1")
port = int(os.getenv("MYSQL_PORT", "3306"))
user = os.getenv("MYSQL_USER", "root")
password = os.getenv("MYSQL_PASSWORD", "")
database = os.getenv("MYSQL_DATABASE", "soadwa_company")

try:
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        charset="utf8mb4",
        autocommit=True,
    )

    with connection.cursor() as cursor:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{database}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )

    connection.close()
    print(f"MySQL database '{database}' is ready.")
except pymysql.MySQLError as error:
    print("Unable to create the MySQL database.")
    print(f"MySQL error: {error}")
    print("Check that MySQL is running and your .env credentials are correct.")
    sys.exit(1)
