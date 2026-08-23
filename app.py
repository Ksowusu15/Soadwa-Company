import os
from datetime import datetime

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import LoginManager, current_user, logout_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from models import Admin, WebsiteSettings, db

login_manager = LoginManager()
login_manager.login_view = "admin.login"
login_manager.login_message_category = "warning"
csrf = CSRFProtect()
migrate = Migrate()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Admin, int(user_id))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be configured in production.")

    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
    )

    for folder in ("cars", "site", "team"):
        os.makedirs(
            os.path.join(app.config["UPLOAD_FOLDER"], folder),
            exist_ok=True,
        )

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    from routes import admin_bp, main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.before_request
    def enforce_admin_inactivity_timeout():
        """Log authenticated admins out after 10 minutes without activity."""
        if not current_user.is_authenticated:
            return None

        # Only admin activity participates in the admin inactivity timer.
        if not request.path.startswith("/admin"):
            return None

        now = datetime.now().timestamp()
        last_activity = session.get("admin_last_activity")
        timeout_seconds = int(app.config["PERMANENT_SESSION_LIFETIME"].total_seconds())

        if last_activity and now - float(last_activity) > timeout_seconds:
            logout_user()
            session.clear()
            flash("Your admin session expired after 10 minutes of inactivity.", "warning")
            return redirect(url_for("admin.login"))

        session.permanent = True
        session["admin_last_activity"] = now
        return None

    def media_url(path):
        if not path:
            return ""
        if path.startswith(("http://", "https://")):
            return path
        return url_for("static", filename=path)

    @app.context_processor
    def inject_settings():
        settings = WebsiteSettings.query.first()
        return {
            "site_settings": settings,
            "media_url": media_url,
        }

    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    @app.after_request
    def apply_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        if app.config.get("APP_ENV") == "production":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(_error):
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    # Use only for first-time deployment of a brand-new database.
    if os.getenv("AUTO_CREATE_DB", "0") == "1":
        with app.app_context():
            db.create_all()

            settings = WebsiteSettings.query.first()
            if settings is None:
                db.session.add(
                    WebsiteSettings(
                        company_name="Soadwa Company Ltd",
                        primary_color="#c1121f",
                        secondary_color="#111111",
                    )
                )
            elif not (settings.company_name or "").strip():
                settings.company_name = "Soadwa Company Ltd"

            if Admin.query.first() is None:
                initial_password = os.getenv("ADMIN_PASSWORD", "").strip()
                initial_email = os.getenv(
                    "ADMIN_EMAIL",
                    "soadwacompany@gmail.com",
                ).strip()
                initial_username = os.getenv("ADMIN_USERNAME", "admin").strip()

                if initial_password:
                    admin = Admin(
                        username=initial_username,
                        email=initial_email,
                    )
                    admin.set_password(initial_password)
                    db.session.add(admin)
                else:
                    app.logger.warning(
                        "AUTO_CREATE_DB is enabled but ADMIN_PASSWORD is missing; "
                        "no admin account was created."
                    )

            db.session.commit()

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", debug=debug, port=port)
