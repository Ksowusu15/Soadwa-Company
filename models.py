from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_token"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(
        db.Integer,
        db.ForeignKey("admin.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    admin = db.relationship(
        "Admin",
        backref=db.backref(
            "password_reset_tokens",
            lazy=True,
            cascade="all, delete-orphan",
        ),
    )

    @property
    def is_valid(self):
        return self.used_at is None and self.expires_at > datetime.utcnow()


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(80), nullable=False, index=True)
    model = db.Column(db.String(100), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    price = db.Column(db.Numeric(12, 2), nullable=False, index=True)
    mileage = db.Column(db.Integer, default=0)
    engine = db.Column(db.String(100))
    fuel = db.Column(db.String(50), index=True)
    transmission = db.Column(db.String(50), index=True)
    body_type = db.Column(db.String(50), index=True)
    color = db.Column(db.String(50))
    interior_color = db.Column(db.String(50))
    vin = db.Column(db.String(50), unique=True)
    features = db.Column(db.Text)
    description = db.Column(db.Text)
    status = db.Column(db.String(30), default="Available", index=True)
    badge = db.Column(db.String(30), default="")
    is_featured = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    images = db.relationship(
        "CarImage", backref="car", lazy=True, cascade="all, delete-orphan"
    )
    test_drives = db.relationship(
        "TestDrive", backref="car", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def main_image(self):
        image = next((i for i in self.images if i.is_main), None)
        return image or (self.images[0] if self.images else None)

    @property
    def feature_list(self):
        return [x.strip() for x in (self.features or "").split(",") if x.strip()]


class CarImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey("car.id"), nullable=False, index=True)
    image_path = db.Column(db.String(255), nullable=False)
    is_main = db.Column(db.Boolean, default=False)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50))
    message = db.Column(db.Text, nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey("car.id"), nullable=True)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class TestDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey("car.id"), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(30), default="Pending", index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120), nullable=False)
    bio = db.Column(db.Text)
    image = db.Column(db.String(255))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    linkedin = db.Column(db.String(255))
    twitter = db.Column(db.String(255))
    display_order = db.Column(db.Integer, default=0, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(120), nullable=False)
    client_title = db.Column(db.String(160))
    testimonial = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5, nullable=False)
    image = db.Column(db.String(255))
    display_order = db.Column(db.Integer, default=0, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class WebsiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(120), default="Soadwa Company Ltd")
    logo = db.Column(db.String(255))
    favicon = db.Column(db.String(255))
    slogan = db.Column(db.String(255), default="Drive Your Dream Car")
    description = db.Column(
        db.Text, default="Luxury vehicles. Exceptional performance. Trusted service."
    )
    about_text = db.Column(
        db.Text,
        default="Soadwa Company Ltd delivers carefully selected premium vehicles and exceptional customer care.",
    )
    mission = db.Column(
        db.Text,
        default="To make luxury vehicle ownership simple, transparent and rewarding.",
    )
    vision = db.Column(
        db.Text,
        default="To become the most trusted premium automotive destination in the region.",
    )
    phone = db.Column(db.String(50), default="+233 00 000 0000")
    whatsapp = db.Column(db.String(50), default="233000000000")
    email = db.Column(db.String(120), default="sales@elitemotors.com")
    address = db.Column(db.String(255), default="Accra, Ghana")
    google_maps = db.Column(db.Text)
    business_hours = db.Column(db.String(255), default="Mon–Sat: 8:00 AM–6:00 PM")
    facebook = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    twitter = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    youtube = db.Column(db.String(255))
    tiktok = db.Column(db.String(255))
    hero_title = db.Column(db.String(255), default="Drive Your Dream Car")
    hero_subtitle = db.Column(
        db.String(255),
        default="Luxury vehicles. Exceptional performance. Trusted service.",
    )
    hero_image = db.Column(db.String(255))
    cars_sold = db.Column(db.Integer, default=500)
    customers = db.Column(db.Integer, default=100)
    experience = db.Column(db.Integer, default=10)
    primary_color = db.Column(db.String(20), default="#c1121f")
    secondary_color = db.Column(db.String(20), default="#111111")
    seo_title = db.Column(
        db.String(255), default="Soadwa Company Ltd | Premium Luxury Vehicles"
    )
    seo_description = db.Column(
        db.String(320), default="Browse premium luxury vehicles from Soadwa Company Ltd."
    )
    keywords = db.Column(
        db.String(500), default="luxury cars, premium vehicles, car dealership"
    )
    google_analytics_id = db.Column(db.String(80))
    social_image = db.Column(db.String(255))
    currency = db.Column(db.String(10), default="GHS")
    smtp_host = db.Column(db.String(120))
    smtp_port = db.Column(db.Integer, default=587)
    smtp_username = db.Column(db.String(120))
    smtp_password = db.Column(db.String(255))
    maintenance_mode = db.Column(db.Boolean, default=False)
    maintenance_message = db.Column(
        db.String(500),
        default="We are upgrading our showroom. Please check back shortly.",
    )
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
