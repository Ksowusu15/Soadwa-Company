# Soadwa Company Ltd Motors — MySQL Edition

A full-stack luxury car dealership platform built with Flask, SQLAlchemy, Flask-Login, Flask-WTF, Jinja2, vanilla JavaScript, responsive CSS and MySQL.

## Main features

- Public dealership website and responsive inventory
- Vehicle search, filters, sorting and pagination
- Vehicle galleries, favorites and comparisons
- Customer messages and test-drive requests
- CSV exports for messages and test drives
- Secure admin login using username or email
- Password reset by email
- Vehicle, team and website-settings management
- Dynamic company branding and social links
- Responsive admin dashboard

## 1. Install MySQL

Install MySQL Server and remember the root password selected during installation. Make sure the MySQL service is running.

## 2. Create and activate the virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
## 3. Install the Python packages

```powershell
pip install -r requirements.txt
```

## 4. Create your environment file

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Open `.env` and enter your actual MySQL password:

```env
SECRET_KEY=replace-with-a-long-random-secret
ADMIN_PASSWORD=ChangeMe123!

MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=elite_motors
MYSQL_USER=root
MYSQL_PASSWORD=your_actual_mysql_password
```

Do not commit `.env` to GitHub.

## 5. Create the MySQL database

```powershell
python create_database.py
```

Expected result:

```text
MySQL database 'elite_motors' is ready.
```

## 6. Run the website

```powershell
python app.py
```

The application creates its tables automatically the first time it connects successfully.

Open:

```text
http://127.0.0.1:5000
```

Default administrator account on a new database:

```text
Username: admin
Password: ChangeMe123!
```

Change this password after signing in. You can also change the initial password in `.env` before the first run.

## Test the database connection

```powershell
python test_database.py
```

## Important migration note

This MySQL version creates a new database. Data from an older SQLite database is not copied automatically. Existing vehicles, settings, messages, test-drive requests and admin accounts must be migrated separately if they need to be retained.

## Using a complete database URL

You may set `DATABASE_URL` instead of the individual `MYSQL_*` values:

```env
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/elite_motors?charset=utf8mb4
```

The individual `MYSQL_*` fields are safer for passwords containing characters such as `@`, `#`, `/` or `:` because the project builds the SQLAlchemy URL correctly.

## Production notes

Use a strong `SECRET_KEY`, HTTPS, a production WSGI server, database backups, a restricted MySQL user rather than root, and environment variables for all secrets.


## Authentication behavior

- Sign in using either the administrator username or email address.
- Usernames are case-sensitive even when MySQL uses a case-insensitive collation.
- Email matching is case-insensitive.
- Passwords are always case-sensitive and securely hashed.
- Password-reset links expire after 15 minutes and can only be used once.
- Requesting a new reset link invalidates older unused links.

When upgrading an existing MySQL installation, start the app once. SQLAlchemy's
`db.create_all()` will create the new `password_reset_token` table automatically.

## Soadwa Motors V2 notes

This package consolidates the project improvements into one MySQL-first release:

- Username or email administrator sign-in
- Case-sensitive usernames and passwords; case-insensitive email login
- Database-backed, one-time password reset tokens with 15-minute expiry
- Gmail/SMTP support for ports 465 (SSL) and 587 (STARTTLS)
- Responsive home, inventory, vehicle overview, compare, team, contact, and admin pages
- Full-vehicle image presentation using `object-fit: contain`
- CSV export for messages and test-drive requests
- Dynamic company name, logo, social links, SEO, and SMTP settings
- Gunicorn/Koyeb-ready production configuration

### Local setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python create_database.py
python app.py
```

Generate a secret key with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

### Production start command

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app
```

### Important upload-storage note

Local files under `static/uploads` may not persist on serverless/free hosts after a redeploy. Use Cloudinary, S3, or another persistent object-storage provider before relying on production image uploads.

## Complete dependency installation

This release includes a fully pinned `requirements.txt`, including the
`cryptography` package needed by many modern MySQL installations that use
`caching_sha2_password` authentication.

Create a fresh virtual environment and install everything with:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Verify the installation:

```powershell
python -c "import flask, pymysql, cryptography; print('Dependencies installed successfully')"
```

## Railway deployment

1. Push this project to a private GitHub repository.
2. In Railway, create a project from the GitHub repository.
3. Add a Railway MySQL service.
4. Add the required application variables from `.env.example`.
5. Set `DATABASE_URL` to a SQLAlchemy-compatible MySQL URL beginning with `mysql+pymysql://`.
6. Attach a Railway Volume at `/app/static/uploads` so uploaded cars, logos, and team images persist across deployments.
7. Generate a public Railway domain and test `/admin/login`.

Recommended production variables:

```env
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=generate-a-new-random-value
ADMIN_PASSWORD=choose-a-strong-initial-password
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:PORT/DATABASE?charset=utf8mb4
```

Generate a secret key locally with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```
