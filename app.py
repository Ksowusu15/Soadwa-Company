import os
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import Admin, WebsiteSettings, db

login_manager = LoginManager()
login_manager.login_view = "admin.login"
login_manager.login_message_category = "warning"
csrf = CSRFProtect()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Admin, int(user_id))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "cars"), exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "site"), exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "team"), exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from routes import main_bp, admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.context_processor
    def inject_settings():
        settings = WebsiteSettings.query.first()
        return {"site_settings": settings}

    with app.app_context():
        db.create_all()
        settings = WebsiteSettings.query.first()
        if not settings:
            db.session.add(WebsiteSettings(company_name="Soadwa Company Ltd"))
        elif not (settings.company_name or "").strip():
            settings.company_name = "Soadwa Company Ltd"
        if not Admin.query.first():
            admin = Admin(username="admin", email="soadwacompany@gmail.com")
            admin.set_password(os.getenv("ADMIN_PASSWORD", "ChangeMe123!"))
            db.session.add(admin)
        db.session.commit()
    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", debug=debug, port=port)
