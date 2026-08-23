import csv
import io
import os
import uuid
from io import BytesIO
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    Response,
    session,
    url_for,
)

from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError
from forms import (
    CarForm,
    ForgotPasswordForm,
    LoginForm,
    ResetPasswordForm,
    MessageForm,
    TeamMemberForm,
    TestDriveForm,
    TestimonialForm,
)
from services.email_service import send_enquiry_emails, send_password_reset_email
from models import (
    Admin,
    Car,
    CarImage,
    Message,
    PasswordResetToken,
    TeamMember,
    TestDrive,
    Testimonial,
    WebsiteSettings,
    db,
)

main_bp = Blueprint("main", __name__)
admin_bp = Blueprint("admin", __name__)
ALLOWED = {"jpg", "jpeg", "png", "webp"}


def save_image(file, folder):
    """Validate and persist an uploaded image locally or in Cloudinary."""
    if not file or not file.filename:
        return None

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED:
        raise ValueError("Unsupported image type. Use JPG, PNG, or WebP.")

    raw = file.read()
    file.seek(0)

    try:
        image = Image.open(BytesIO(raw))
        image.verify()
    except (UnidentifiedImageError, OSError):
        raise ValueError("The uploaded file is not a valid image.")

    cloudinary_url = os.getenv("CLOUDINARY_URL", "").strip()
    if cloudinary_url:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(cloudinary_url=cloudinary_url, secure=True)
        file.seek(0)
        result = cloudinary.uploader.upload(
            file,
            folder=f"soadwa-company/{folder}",
            resource_type="image",
            use_filename=True,
            unique_filename=True,
            overwrite=False,
        )
        return result["secure_url"]

    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    target_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], folder)
    os.makedirs(target_dir, exist_ok=True)
    file.seek(0)
    file.save(os.path.join(target_dir, filename))
    return f"uploads/{folder}/{filename}"


def csv_safe(value):
    """Return a spreadsheet-safe string for CSV exports."""
    if value is None:
        return ""

    text = str(value).replace("\r", " ").replace("\n", " ").strip()

    # Prevent spreadsheet applications from evaluating exported text as a formula.
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text

    return text


def _hash_reset_token(raw_token):
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_password_reset_token(admin, lifetime_minutes=15):
    """Create a single-use, database-backed reset token."""
    now = datetime.utcnow()

    # Revoke any older unused tokens for this administrator.
    PasswordResetToken.query.filter_by(
        admin_id=admin.id,
        used_at=None,
    ).update({"used_at": now}, synchronize_session=False)

    raw_token = secrets.token_urlsafe(48)
    record = PasswordResetToken(
        admin_id=admin.id,
        token_hash=_hash_reset_token(raw_token),
        expires_at=now + timedelta(minutes=lifetime_minutes),
    )
    db.session.add(record)
    db.session.commit()
    return raw_token


def verify_password_reset_token(raw_token):
    """Return a valid reset-token record, otherwise None."""
    if not raw_token:
        return None

    record = PasswordResetToken.query.filter_by(
        token_hash=_hash_reset_token(raw_token)
    ).first()

    if not record or not record.is_valid or not record.admin:
        return None

    return record


def build_csv_response(filename, headers, rows):
    """Create an Excel-friendly UTF-8 CSV download response."""
    output = io.StringIO(newline="")
    output.write("\ufeff")
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)

    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@main_bp.before_app_request
def maintenance_guard():
    settings = WebsiteSettings.query.first()
    if (
        settings
        and settings.maintenance_mode
        and not request.path.startswith("/admin")
        and not current_user.is_authenticated
        and request.endpoint != "static"
    ):
        return render_template("maintenance.html", settings=settings), 503



def _business_notification_email(settings=None):
    """Return the preferred business email for enquiry notifications."""
    explicit = os.getenv("BREVO_NOTIFY_EMAIL", "").strip()
    if explicit:
        return explicit

    admin = Admin.query.order_by(Admin.id.asc()).first()
    if admin and (admin.email or "").strip():
        return admin.email.strip()

    if settings and (settings.email or "").strip():
        return settings.email.strip()

    return ""


def _send_saved_enquiry_notifications(enquiry, settings=None):
    """Send business + customer emails without affecting the saved enquiry."""
    notify_email = _business_notification_email(settings)

    if not notify_email:
        current_app.logger.warning(
            "Enquiry %s saved, but no business notification email is configured.",
            enquiry.id,
        )
        return

    current_app.logger.info(
        "Sending enquiry %s notification to business email: %s",
        enquiry.id,
        notify_email,
    )

    admin_sent, customer_sent = send_enquiry_emails(
        settings,
        enquiry,
        notify_email,
    )

    if not admin_sent:
        current_app.logger.warning(
            "Enquiry %s saved, but business email to %s failed.",
            enquiry.id,
            notify_email,
        )

    if not customer_sent:
        current_app.logger.warning(
            "Enquiry %s saved, but customer acknowledgement to %s failed.",
            enquiry.id,
            enquiry.email,
        )


@main_bp.route("/")
def index():
    featured = (
        Car.query.filter(Car.is_featured.is_(True))
        .order_by(Car.created_at.desc())
        .limit(6)
        .all()
    )
    if not featured:
        featured = Car.query.order_by(Car.created_at.desc()).limit(6).all()

    testimonials = (
        Testimonial.query.filter_by(is_active=True)
        .order_by(Testimonial.display_order.asc(), Testimonial.created_at.desc())
        .limit(6)
        .all()
    )
    return render_template(
        "index.html",
        featured=featured,
        testimonials=testimonials,
    )


@main_bp.route("/inventory")
def inventory():
    page = request.args.get("page", 1, type=int)
    q = Car.query
    search = request.args.get("q", "").strip()
    if search:
        q = q.filter(
            or_(Car.brand.ilike(f"%{search}%"), Car.model.ilike(f"%{search}%"))
        )
    for field in ["brand", "fuel", "transmission", "body_type", "status"]:
        value = request.args.get(field, "").strip()
        if value:
            q = q.filter(getattr(Car, field) == value)
    if request.args.get("year", type=int):
        q = q.filter(Car.year == request.args.get("year", type=int))
    if request.args.get("min_price", type=float) is not None:
        q = q.filter(Car.price >= request.args.get("min_price", type=float))
    if request.args.get("max_price", type=float) is not None:
        q = q.filter(Car.price <= request.args.get("max_price", type=float))
    sort = request.args.get("sort", "latest")
    sort_map = {
        "price_asc": Car.price.asc(),
        "price_desc": Car.price.desc(),
        "oldest": Car.created_at.asc(),
        "latest": Car.created_at.desc(),
    }
    cars = q.order_by(sort_map.get(sort, Car.created_at.desc())).paginate(
        page=page, per_page=9, error_out=False
    )
    brands = [
        x[0] for x in db.session.query(Car.brand).distinct().order_by(Car.brand).all()
    ]
    return render_template("inventory.html", cars=cars, brands=brands)


@main_bp.route("/compare")
def compare():
    raw_ids = request.args.get("ids", "")
    car_ids = []

    for value in raw_ids.split(","):
        value = value.strip()

        if value.isdigit():
            car_id = int(value)

            if car_id not in car_ids:
                car_ids.append(car_id)

        if len(car_ids) == 3:
            break

    cars_by_id = {
        car.id: car
        for car in Car.query.filter(Car.id.in_(car_ids)).all()
    } if car_ids else {}

    cars = [cars_by_id[car_id] for car_id in car_ids if car_id in cars_by_id]

    return render_template("compare.html", cars=cars)


@main_bp.route("/api/inventory")
def inventory_api():
    cars = Car.query.order_by(Car.created_at.desc()).all()
    return jsonify(
        [
            {
                "id": c.id,
                "brand": c.brand,
                "model": c.model,
                "year": c.year,
                "price": float(c.price),
                "status": c.status,
                "image": c.main_image.image_path if c.main_image else "",
            }
            for c in cars
        ]
    )


@main_bp.route("/cars/<int:car_id>", methods=["GET", "POST"])
def car_details(car_id):
    car = Car.query.get_or_404(car_id)
    message_form, test_form = MessageForm(prefix="msg"), TestDriveForm(prefix="test")
    if message_form.submit.data and message_form.validate_on_submit():
        enquiry = Message(
            name=message_form.name.data,
            email=message_form.email.data,
            phone=message_form.phone.data,
            message=message_form.message.data,
            car_id=car.id,
        )
        db.session.add(enquiry)
        db.session.commit()

        settings = WebsiteSettings.query.first()
        _send_saved_enquiry_notifications(enquiry, settings)

        flash(
            "Enquiry sent successfully! Our team will get back to you shortly.",
            "success",
        )
        return redirect(url_for("main.car_details", car_id=car.id))
    if test_form.submit.data and test_form.validate_on_submit():
        db.session.add(
            TestDrive(
                customer_name=test_form.customer_name.data,
                email=test_form.email.data,
                phone=test_form.phone.data,
                car_id=car.id,
                appointment_date=test_form.appointment_date.data,
            )
        )
        db.session.commit()
        flash("Your test drive request has been submitted.", "success")
        return redirect(url_for("main.car_details", car_id=car.id))
    related = (
        Car.query.filter(
            Car.id != car.id,
            or_(Car.brand == car.brand, Car.body_type == car.body_type),
        )
        .limit(3)
        .all()
    )
    return render_template(
        "car_details.html",
        car=car,
        related=related,
        message_form=message_form,
        test_form=test_form,
    )


@main_bp.route("/about")
def about():
    team_members = (
        TeamMember.query.filter_by(is_active=True)
        .order_by(TeamMember.display_order.asc(), TeamMember.name.asc())
        .all()
    )
    return render_template("about.html", team_members=team_members)


@main_bp.route("/services")
def services():
    return render_template("services.html")


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = MessageForm()
    if form.validate_on_submit():
        enquiry = Message(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            message=form.message.data,
        )
        db.session.add(enquiry)
        db.session.commit()

        settings = WebsiteSettings.query.first()
        _send_saved_enquiry_notifications(enquiry, settings)

        flash(
            "Enquiry sent successfully! Thank you for contacting us. "
            "Our team will get back to you shortly.",
            "success",
        )
        return redirect(url_for("main.contact"))
    return render_template("contact.html", form=form)



@main_bp.route("/privacy")
def privacy():
    return render_template("privacy.html")


@main_bp.route("/terms")
def terms():
    return render_template("terms.html")


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.username.data.strip()

        # PostgreSQL string equality is case-sensitive, which preserves the
        # intended case-sensitive username login behavior.
        admin = Admin.query.filter(Admin.username == identifier).first()

        # Email addresses remain case-insensitive.
        if admin is None:
            admin = Admin.query.filter(
                db.func.lower(Admin.email) == identifier.lower()
            ).first()

        if admin and admin.check_password(form.password.data):
            login_user(admin, remember=form.remember.data)
            session.permanent = True
            session["admin_last_activity"] = datetime.now().timestamp()
            return redirect(request.args.get("next") or url_for("admin.dashboard"))

        flash("Invalid username/email or password.", "danger")
    return render_template("admin/login.html", form=form)


@admin_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        admin = Admin.query.filter(db.func.lower(Admin.email) == email).first()

        if admin:
            token = create_password_reset_token(admin)
            reset_url = url_for(
                "admin.reset_password", token=token, _external=True
            )
            sent = send_password_reset_email(
                WebsiteSettings.query.first(), admin, reset_url
            )

            if not sent and current_app.debug:
                current_app.logger.info("Development reset URL: %s", reset_url)

        flash(
            "If that email belongs to an admin account, a password reset link "
            "has been sent. Please check your inbox and spam folder.",
            "success",
        )
        return redirect(url_for("admin.login"))

    return render_template("admin/forgot_password.html", form=form)


@admin_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    reset_record = verify_password_reset_token(token)
    if not reset_record:
        flash(
            "That password reset link is invalid, expired, or has already been used. "
            "Please request a new one.",
            "danger",
        )
        return redirect(url_for("admin.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        reset_record.admin.set_password(form.password.data)
        reset_record.used_at = datetime.utcnow()

        # Revoke every other outstanding token for this administrator.
        PasswordResetToken.query.filter(
            PasswordResetToken.admin_id == reset_record.admin_id,
            PasswordResetToken.id != reset_record.id,
            PasswordResetToken.used_at.is_(None),
        ).update({"used_at": datetime.utcnow()}, synchronize_session=False)

        db.session.commit()
        flash("Your password has been reset. You can now sign in.", "success")
        return redirect(url_for("admin.login"))

    return render_template("admin/reset_password.html", form=form)


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "total": Car.query.count(),
        "available": Car.query.filter_by(status="Available").count(),
        "reserved": Car.query.filter_by(status="Reserved").count(),
        "sold": Car.query.filter_by(status="Sold").count(),
        "messages": Message.query.filter_by(is_read=False).count(),
        "test_drives": TestDrive.query.filter_by(status="Pending").count(),
    }
    recent_cars = Car.query.order_by(Car.created_at.desc()).limit(5).all()
    recent_messages = Message.query.order_by(Message.created_at.desc()).limit(5).all()
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_cars=recent_cars,
        recent_messages=recent_messages,
    )


@admin_bp.route("/cars")
@login_required
def cars():
    search = request.args.get("q", "")
    query = Car.query
    if search:
        query = query.filter(
            or_(
                Car.brand.ilike(f"%{search}%"),
                Car.model.ilike(f"%{search}%"),
                Car.vin.ilike(f"%{search}%"),
            )
        )
    return render_template(
        "admin/cars.html", cars=query.order_by(Car.created_at.desc()).all()
    )


@admin_bp.route("/cars/add", methods=["GET", "POST"])
@login_required
def add_car():
    form = CarForm()

    if form.validate_on_submit():
        vin = (form.vin.data or "").strip() or None

        if vin:
            existing_car = Car.query.filter_by(vin=vin).first()

            if existing_car:
                flash(
                    "A vehicle with this VIN already exists.",
                    "danger",
                )
                return render_template(
                    "admin/car_form.html",
                    form=form,
                    title="Add Vehicle",
                    car=None,
                )

        car = Car(
            brand=form.brand.data.strip(),
            model=form.model.data.strip(),
            year=form.year.data,
            price=form.price.data,
            mileage=form.mileage.data or 0,
            engine=form.engine.data,
            fuel=form.fuel.data,
            transmission=form.transmission.data,
            body_type=form.body_type.data,
            color=form.color.data,
            interior_color=form.interior_color.data,
            vin=vin,
            features=form.features.data,
            description=form.description.data,
            status=form.status.data,
            badge=form.badge.data,
            is_featured=form.is_featured.data,
        )

        try:
            db.session.add(car)
            db.session.flush()

            main_file = request.files.get("main_image")

            if main_file and main_file.filename:
                main_path = save_image(main_file, "cars")

                if main_path:
                    db.session.add(
                        CarImage(
                            car_id=car.id,
                            image_path=main_path,
                            is_main=True,
                        )
                    )

            gallery_files = request.files.getlist("gallery_images")

            for gallery_file in gallery_files:
                if gallery_file and gallery_file.filename:
                    gallery_path = save_image(gallery_file, "cars")

                    if gallery_path:
                        db.session.add(
                            CarImage(
                                car_id=car.id,
                                image_path=gallery_path,
                                is_main=False,
                            )
                        )

            db.session.commit()
            flash("Vehicle added successfully.", "success")
            return redirect(url_for("admin.cars"))

        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")

        except IntegrityError:
            db.session.rollback()
            flash(
                "A vehicle with this VIN already exists.",
                "danger",
            )

        except Exception:
            db.session.rollback()
            current_app.logger.exception(
                "Failed to add a new vehicle."
            )
            flash(
                "The vehicle could not be added. Please try again.",
                "danger",
            )

    return render_template(
        "admin/car_form.html",
        form=form,
        title="Add Vehicle",
        car=None,
    )

@admin_bp.route("/cars/<int:car_id>/edit", methods=["GET", "POST"])
@login_required
def edit_car(car_id):
    car = Car.query.get_or_404(car_id)
    form = CarForm(obj=car)

    if form.validate_on_submit():
        vin = (form.vin.data or "").strip() or None

        if vin:
            existing_car = (
                Car.query.filter(
                    Car.vin == vin,
                    Car.id != car.id,
                )
                .first()
            )

            if existing_car:
                flash(
                    "Another vehicle already uses this VIN.",
                    "danger",
                )
                return render_template(
                    "admin/car_form.html",
                    form=form,
                    title="Edit Vehicle",
                    car=car,
                )

        car.brand = form.brand.data.strip()
        car.model = form.model.data.strip()
        car.year = form.year.data
        car.price = form.price.data
        car.mileage = form.mileage.data or 0
        car.engine = form.engine.data
        car.fuel = form.fuel.data
        car.transmission = form.transmission.data
        car.body_type = form.body_type.data
        car.color = form.color.data
        car.interior_color = form.interior_color.data
        car.vin = vin
        car.features = form.features.data
        car.description = form.description.data
        car.status = form.status.data
        car.badge = form.badge.data
        car.is_featured = form.is_featured.data

        try:
            main_file = request.files.get("main_image")

            if main_file and main_file.filename:
                main_path = save_image(main_file, "cars")

                if main_path:
                    for image in car.images:
                        image.is_main = False

                    db.session.add(
                        CarImage(
                            car_id=car.id,
                            image_path=main_path,
                            is_main=True,
                        )
                    )

            gallery_files = request.files.getlist("gallery_images")

            for gallery_file in gallery_files:
                if gallery_file and gallery_file.filename:
                    gallery_path = save_image(gallery_file, "cars")

                    if gallery_path:
                        db.session.add(
                            CarImage(
                                car_id=car.id,
                                image_path=gallery_path,
                                is_main=False,
                            )
                        )

            db.session.commit()
            flash("Vehicle updated successfully.", "success")
            return redirect(url_for("admin.cars"))

        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")

        except IntegrityError:
            db.session.rollback()
            flash(
                "Another vehicle already uses this VIN.",
                "danger",
            )

        except Exception:
            db.session.rollback()
            current_app.logger.exception(
                "Failed to update vehicle with ID %s",
                car.id,
            )
            flash(
                "The vehicle could not be updated. Please try again.",
                "danger",
            )

    return render_template(
        "admin/car_form.html",
        form=form,
        title="Edit Vehicle",
        car=car,
    )

@admin_bp.route("/cars/<int:car_id>/delete", methods=["POST"])
@login_required
def delete_car(car_id):
    car = Car.query.get_or_404(car_id)
    db.session.delete(car)
    db.session.commit()
    flash("Vehicle deleted.", "success")
    return redirect(url_for("admin.cars"))


@admin_bp.route("/images/<int:image_id>/delete", methods=["POST"])
@login_required
def delete_image(image_id):
    image = CarImage.query.get_or_404(image_id)
    car_id = image.car_id
    db.session.delete(image)
    db.session.commit()
    flash("Image removed.", "success")
    return redirect(url_for("admin.edit_car", car_id=car_id))


@admin_bp.route("/messages")
@login_required
def messages():
    return render_template(
        "admin/messages.html",
        messages=Message.query.order_by(Message.created_at.desc()).all(),
    )


@admin_bp.route("/messages/export.csv")
@login_required
def export_messages_csv():
    messages = Message.query.order_by(Message.created_at.desc()).all()

    rows = []
    for message in messages:
        vehicle = ""
        if message.car_id:
            car = db.session.get(Car, message.car_id)
            if car:
                vehicle = f"{car.brand} {car.model} ({car.year})"

        rows.append(
            [
                message.id,
                csv_safe(message.name),
                csv_safe(message.email),
                csv_safe(message.phone),
                csv_safe(vehicle),
                csv_safe(message.message),
                "Read" if message.is_read else "Unread",
                message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )

    filename = f"customer_messages_{datetime.now().strftime('%Y-%m-%d')}.csv"

    return build_csv_response(
        filename,
        [
            "ID",
            "Customer Name",
            "Email",
            "Phone",
            "Vehicle",
            "Message",
            "Status",
            "Received At",
        ],
        rows,
    )


@admin_bp.route("/messages/<int:message_id>/toggle", methods=["POST"])
@login_required
def toggle_message(message_id):
    message = Message.query.get_or_404(message_id)
    message.is_read = not message.is_read
    db.session.commit()
    return redirect(url_for("admin.messages"))


@admin_bp.route("/messages/<int:message_id>/delete", methods=["POST"])
@login_required
def delete_message(message_id):
    db.session.delete(Message.query.get_or_404(message_id))
    db.session.commit()
    return redirect(url_for("admin.messages"))


@admin_bp.route("/test-drives")
@login_required
def test_drives():
    return render_template(
        "admin/test_drives.html",
        requests=TestDrive.query.order_by(TestDrive.created_at.desc()).all(),
    )


@admin_bp.route("/test-drives/export.csv")
@login_required
def export_test_drives_csv():
    test_drive_requests = TestDrive.query.order_by(
        TestDrive.created_at.desc()
    ).all()

    rows = []
    for item in test_drive_requests:
        vehicle = ""
        if item.car:
            vehicle = f"{item.car.brand} {item.car.model} ({item.car.year})"

        rows.append(
            [
                item.id,
                csv_safe(item.customer_name),
                csv_safe(item.email),
                csv_safe(item.phone),
                csv_safe(vehicle),
                item.appointment_date.strftime("%Y-%m-%d %H:%M:%S"),
                csv_safe(item.status),
                item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )

    filename = f"test_drive_requests_{datetime.now().strftime('%Y-%m-%d')}.csv"

    return build_csv_response(
        filename,
        [
            "ID",
            "Customer Name",
            "Email",
            "Phone",
            "Vehicle",
            "Appointment Date",
            "Status",
            "Requested At",
        ],
        rows,
    )


@admin_bp.route("/test-drives/<int:item_id>/status", methods=["POST"])
@login_required
def test_drive_status(item_id):
    item = TestDrive.query.get_or_404(item_id)
    status = request.form.get("status")
    if status in ["Pending", "Approved", "Completed", "Cancelled"]:
        item.status = status
        db.session.commit()
    return redirect(url_for("admin.test_drives"))


@admin_bp.route("/team")
@login_required
def team_members():
    members = TeamMember.query.order_by(
        TeamMember.display_order.asc(), TeamMember.name.asc()
    ).all()
    return render_template("admin/team.html", members=members)


@admin_bp.route("/team/add", methods=["GET", "POST"])
@login_required
def add_team_member():
    form = TeamMemberForm()
    if form.validate_on_submit():
        member = TeamMember(
            name=form.name.data,
            role=form.role.data,
            bio=form.bio.data,
            email=form.email.data,
            phone=form.phone.data,
            linkedin=form.linkedin.data,
            twitter=form.twitter.data,
            display_order=form.display_order.data or 0,
            is_active=form.is_active.data,
        )
        try:
            member.image = save_image(form.image.data, "team")
            db.session.add(member)
            db.session.commit()
            flash("Team member added successfully.", "success")
            return redirect(url_for("admin.team_members"))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
    return render_template(
        "admin/team_form.html", form=form, title="Add Team Member", member=None
    )


@admin_bp.route("/team/<int:member_id>/edit", methods=["GET", "POST"])
@login_required
def edit_team_member(member_id):
    member = TeamMember.query.get_or_404(member_id)
    form = TeamMemberForm(obj=member)

    if form.validate_on_submit():
        member.name = form.name.data.strip()
        member.role = form.role.data.strip()
        member.bio = form.bio.data
        member.email = form.email.data
        member.phone = form.phone.data
        member.linkedin = form.linkedin.data
        member.twitter = form.twitter.data
        member.display_order = form.display_order.data or 0
        member.is_active = form.is_active.data

        try:
            image_file = request.files.get("image")

            if image_file and image_file.filename:
                image_path = save_image(image_file, "team")

                if image_path:
                    member.image = image_path

            db.session.commit()
            flash("Team member updated successfully.", "success")
            return redirect(url_for("admin.team_members"))

        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")

        except Exception:
            db.session.rollback()
            current_app.logger.exception(
                "Failed to update team member with ID %s",
                member.id,
            )
            flash(
                "The team member could not be updated. Please try again.",
                "danger",
            )

    return render_template(
        "admin/team_form.html",
        form=form,
        title="Edit Team Member",
        member=member,
    )

@admin_bp.route("/team/<int:member_id>/toggle", methods=["POST"])
@login_required
def toggle_team_member(member_id):
    member = TeamMember.query.get_or_404(member_id)
    member.is_active = not member.is_active
    db.session.commit()
    flash("Team member visibility updated.", "success")
    return redirect(url_for("admin.team_members"))


@admin_bp.route("/team/<int:member_id>/delete", methods=["POST"])
@login_required
def delete_team_member(member_id):
    member = TeamMember.query.get_or_404(member_id)

    try:
        db.session.delete(member)
        db.session.commit()
        flash("Team member deleted successfully.", "success")

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Failed to delete team member with ID %s",
            member_id,
        )
        flash(
            "The team member could not be deleted. Please try again.",
            "danger",
        )

    return redirect(url_for("admin.team_members"))

@admin_bp.route("/testimonials")
@login_required
def testimonials():
    items = Testimonial.query.order_by(
        Testimonial.display_order.asc(), Testimonial.created_at.desc()
    ).all()
    return render_template("admin/testimonials.html", testimonials=items)


@admin_bp.route("/testimonials/add", methods=["GET", "POST"])
@login_required
def add_testimonial():
    form = TestimonialForm()
    if form.validate_on_submit():
        item = Testimonial(
            client_name=form.client_name.data.strip(),
            client_title=(form.client_title.data or "").strip() or None,
            testimonial=form.testimonial.data.strip(),
            rating=int(form.rating.data or 5),
            display_order=form.display_order.data or 0,
            is_active=form.is_active.data,
        )
        try:
            item.image = save_image(form.image.data, "testimonials")
            db.session.add(item)
            db.session.commit()
            flash("Client testimonial added successfully.", "success")
            return redirect(url_for("admin.testimonials"))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
    return render_template(
        "admin/testimonial_form.html",
        form=form,
        title="Add Client Testimonial",
        testimonial=None,
    )


@admin_bp.route("/testimonials/<int:testimonial_id>/edit", methods=["GET", "POST"])
@login_required
def edit_testimonial(testimonial_id):
    item = Testimonial.query.get_or_404(testimonial_id)
    form = TestimonialForm(obj=item)
    if request.method == "GET":
        form.rating.data = str(item.rating or 5)

    if form.validate_on_submit():
        item.client_name = form.client_name.data.strip()
        item.client_title = (form.client_title.data or "").strip() or None
        item.testimonial = form.testimonial.data.strip()
        item.rating = int(form.rating.data or 5)
        item.display_order = form.display_order.data or 0
        item.is_active = form.is_active.data

        try:
            image_file = request.files.get("image")
            if image_file and image_file.filename:
                item.image = save_image(image_file, "testimonials")
            db.session.commit()
            flash("Client testimonial updated successfully.", "success")
            return redirect(url_for("admin.testimonials"))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    return render_template(
        "admin/testimonial_form.html",
        form=form,
        title="Edit Client Testimonial",
        testimonial=item,
    )


@admin_bp.route("/testimonials/<int:testimonial_id>/toggle", methods=["POST"])
@login_required
def toggle_testimonial(testimonial_id):
    item = Testimonial.query.get_or_404(testimonial_id)
    item.is_active = not item.is_active
    db.session.commit()
    flash("Testimonial visibility updated.", "success")
    return redirect(url_for("admin.testimonials"))


@admin_bp.route("/testimonials/<int:testimonial_id>/delete", methods=["POST"])
@login_required
def delete_testimonial(testimonial_id):
    item = Testimonial.query.get_or_404(testimonial_id)
    db.session.delete(item)
    db.session.commit()
    flash("Client testimonial deleted successfully.", "success")
    return redirect(url_for("admin.testimonials"))


@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    settings = WebsiteSettings.query.first()
    if settings is None:
        settings = WebsiteSettings(
            company_name="Soadwa Company Ltd",
            primary_color="#c1121f",
            secondary_color="#111111",
            currency="GHS",
        )
        db.session.add(settings)
        db.session.commit()
    if request.method == "POST":
        boolean_fields = {"maintenance_mode"}
        integer_fields = {"cars_sold", "customers", "experience", "smtp_port"}
        file_fields = {"logo", "favicon", "hero_image", "social_image"}

        for column in WebsiteSettings.__table__.columns:
            key = column.name
            if key in {"id", "updated_at"} or key in file_fields:
                continue
            if key in boolean_fields:
                setattr(settings, key, key in request.form)
            elif key in integer_fields:
                try:
                    setattr(settings, key, int(request.form.get(key) or 0))
                except ValueError:
                    pass
            elif key in request.form:
                setattr(settings, key, request.form.get(key))

        try:
            # Handle media explicitly so each uploaded file is guaranteed to be
            # written and its saved path/URL persisted in WebsiteSettings.
            media_uploads = {
                "logo": request.files.get("logo"),
                "favicon": request.files.get("favicon"),
                "hero_image": request.files.get("hero_image"),
                "social_image": request.files.get("social_image"),
            }

            for field, uploaded_file in media_uploads.items():
                if not uploaded_file or not uploaded_file.filename:
                    continue

                saved_path = save_image(uploaded_file, "site")
                if not saved_path:
                    raise ValueError(f"The {field.replace('_', ' ')} could not be saved.")

                setattr(settings, field, saved_path)
                current_app.logger.info(
                    "Saved website media field %s as %s",
                    field,
                    saved_path,
                )

            db.session.add(settings)
            db.session.commit()
            flash("Website settings updated successfully.", "success")

        except ValueError as exc:
            db.session.rollback()
            current_app.logger.warning("Settings media upload rejected: %s", exc)
            flash(str(exc), "danger")

        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to update website settings.")
            flash("Website settings could not be saved. Please try again.", "danger")

        return redirect(url_for("admin.settings"))
    return render_template("admin/settings.html", settings=settings)
