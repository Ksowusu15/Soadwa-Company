# Soadwa Company Ltd Motors

A production-oriented Flask dealership platform with responsive inventory, admin management, authentication, password reset, PostgreSQL/MySQL support, persistent Cloudinary media, and Render deployment configuration.

## Main features

- Public dealership website and responsive inventory
- Vehicle search, filters, sorting, pagination and comparison
- Vehicle galleries and featured inventory
- Customer messages and test-drive requests
- CSV exports for messages and test drives
- Admin login using username or email
- Case-sensitive username and password behavior
- One-time 15-minute password reset tokens
- Vehicle, team and website-settings management
- Dynamic branding and social links
- PostgreSQL production support
- Cloudinary-ready persistent uploads
- Brevo transactional email API integration
- Flask-Migrate support
- Production health check and security headers

## Local setup

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy the environment template:

```powershell
Copy-Item .env.example .env
```

For PostgreSQL, configure either `DATABASE_URL` or the individual `POSTGRES_*` fields in `.env`.

Example:

```env
APP_ENV=development
SECRET_KEY=generate-a-long-random-secret
DATABASE_URL=postgresql+psycopg://postgres:password@127.0.0.1:5432/soadwa_company
ADMIN_USERNAME=admin
ADMIN_EMAIL=soadwacompany@gmail.com
ADMIN_PASSWORD=choose-a-private-strong-password
```

Initialize a new local database:

```powershell
python create_database.py
```

Run the site:

```powershell
python app.py
```

## Database migrations

Flask-Migrate is included. Once the database is available:

```powershell
flask --app app db init
flask --app app db migrate -m "Initial schema"
flask --app app db upgrade
```

Commit the generated `migrations/` folder. For later model changes:

```powershell
flask --app app db migrate -m "Describe the change"
flask --app app db upgrade
```

## Render deployment

This repository includes `render.yaml`.

Create a Render Web Service from this GitHub repository using:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app
Health Check: /health
```

Configure these environment variables on Render:

```env
APP_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your-private-production-secret
DATABASE_URL=your-postgresql-connection-url
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
BREVO_API_KEY=your-private-brevo-api-key
BREVO_FROM_EMAIL=your-verified-brevo-sender@example.com
BREVO_FROM_NAME=Soadwa Company Ltd
```

### First deployment to a brand-new empty database

Temporarily add:

```env
AUTO_CREATE_DB=1
ADMIN_USERNAME=admin
ADMIN_EMAIL=your-admin-email
ADMIN_PASSWORD=your-private-strong-password
```

Deploy once and confirm the site/admin account works. Then change:

```env
AUTO_CREATE_DB=0
```

Do not leave automatic schema creation enabled long-term. Use migrations after the initial setup.

## Persistent images

Render's local filesystem is not suitable for permanent admin uploads. Configure `CLOUDINARY_URL` so vehicle, team and site images are stored in Cloudinary. Existing demo images committed under `static/uploads/` will continue to display normally.

## Email

Password reset uses the Brevo HTTPS API. Create an API key in Brevo and register/verify the sender email used in `BREVO_FROM_EMAIL`. Keep the API key only in `.env` locally and in your hosting provider's environment variables.

## Security

- Never commit `.env`.
- Use a unique production `SECRET_KEY`.
- Never use the example/default admin password in production.
- Keep `FLASK_DEBUG=0` in production.
- Use HTTPS.
- Back up the production database regularly.
- Rotate any key or password that has been accidentally exposed.


## Neon PostgreSQL + Render

This project is configured to use Neon as the recommended hosted PostgreSQL database for Render.

1. Create a Neon project and database.
2. In Neon, open **Connect** and copy the **pooled** connection string. Neon pooled endpoints contain `-pooler` in the hostname.
3. Keep the SSL query parameter supplied by Neon, normally `?sslmode=require`.
4. In Render, open the web service -> **Environment** and create `DATABASE_URL` with the Neon connection string as the value.
5. Do not commit the Neon URL to GitHub or place it in `.env.example`.
6. The application automatically converts `postgresql://` or `postgres://` to the Psycopg SQLAlchemy driver URL.

Example shape only (not a real credential):

```text
postgresql://USER:PASSWORD@ep-example-pooler.region.aws.neon.tech/neondb?sslmode=require
```

For first-time schema creation, use migrations when possible:

```bash
flask --app app db upgrade
```

If the database is completely empty and no migrations exist yet, you can temporarily set `AUTO_CREATE_DB=1` together with a strong `ADMIN_PASSWORD`, start once, then return `AUTO_CREATE_DB` to `0`.


## Brevo transactional email setup

The password-reset flow uses Brevo's HTTPS transactional email API.

```env
BREVO_API_KEY=your-private-brevo-api-key
BREVO_FROM_EMAIL=your-verified-brevo-sender@example.com
BREVO_FROM_NAME=Soadwa Company Ltd
```

In Brevo, register and verify `BREVO_FROM_EMAIL` as a sender before testing.
Never commit your real API key to GitHub.


### Enquiry email notifications

Set the email that should receive new website enquiries:

```env
BREVO_NOTIFY_EMAIL=your-business-email@example.com
```

If this is not set, the application falls back to the email saved in Website
Settings, then to the first admin email. New enquiries are always saved to the
database even if the email API is temporarily unavailable.
