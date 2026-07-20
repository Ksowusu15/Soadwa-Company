from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, MultipleFileField
from wtforms import (
    BooleanField,
    DateTimeLocalField,
    DecimalField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

IMAGE_TYPES = ["jpg", "jpeg", "png", "webp"]


class LoginForm(FlaskForm):
    username = StringField(
        "Username or Email",
        validators=[DataRequired(), Length(max=120)],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Sign In")


class ForgotPasswordForm(FlaskForm):
    email = StringField(
        "Admin Email",
        validators=[DataRequired(), Email(), Length(max=120)],
    )
    submit = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Reset Password")


class CarForm(FlaskForm):
    brand = StringField("Brand", validators=[DataRequired(), Length(max=80)])
    model = StringField("Model", validators=[DataRequired(), Length(max=100)])
    year = IntegerField(
        "Year", validators=[DataRequired(), NumberRange(min=1900, max=2100)]
    )
    price = DecimalField("Price", validators=[DataRequired(), NumberRange(min=0)])
    mileage = IntegerField("Mileage", validators=[Optional(), NumberRange(min=0)])
    engine = StringField("Engine", validators=[Optional(), Length(max=100)])
    fuel = SelectField("Fuel", choices=["Petrol", "Diesel", "Hybrid", "Electric"])
    transmission = SelectField("Transmission", choices=["Automatic", "Manual"])
    body_type = SelectField(
        "Body Type",
        choices=[
            "Sedan",
            "SUV",
            "Coupe",
            "Convertible",
            "Hatchback",
            "Pickup",
            "Wagon",
        ],
    )
    color = StringField("Exterior Color", validators=[Optional(), Length(max=50)])
    interior_color = StringField(
        "Interior Color", validators=[Optional(), Length(max=50)]
    )
    vin = StringField("VIN", validators=[Optional(), Length(max=50)])
    features = TextAreaField("Features")
    description = TextAreaField("Description")
    status = SelectField("Status", choices=["Available", "Reserved", "Sold"])
    badge = SelectField(
        "Badge",
        choices=[
            ("", "None"),
            ("New Arrival", "New Arrival"),
            ("Featured", "Featured"),
            ("Sold", "Sold"),
        ],
    )
    is_featured = BooleanField("Featured vehicle")
    main_image = FileField(
        "Main Image", validators=[Optional(), FileAllowed(IMAGE_TYPES, "Images only")]
    )
    gallery_images = MultipleFileField(
        "Gallery Images",
        validators=[Optional(), FileAllowed(IMAGE_TYPES, "Images only")],
    )
    submit = SubmitField("Save Vehicle")


class MessageForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField("Phone", validators=[Optional(), Length(max=50)])
    message = TextAreaField(
        "Message", validators=[DataRequired(), Length(min=5, max=3000)]
    )
    submit = SubmitField("Send Message")


class TestDriveForm(FlaskForm):
    customer_name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField("Phone", validators=[DataRequired(), Length(max=50)])
    appointment_date = DateTimeLocalField(
        "Preferred Date & Time", format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )
    submit = SubmitField("Book Test Drive")


class TeamMemberForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    role = StringField("Role / Position", validators=[DataRequired(), Length(max=120)])
    bio = TextAreaField("Biography", validators=[Optional(), Length(max=1000)])
    image = FileField(
        "Profile Image",
        validators=[Optional(), FileAllowed(IMAGE_TYPES, "Images only")],
    )
    email = StringField("Email", validators=[Optional(), Email(), Length(max=120)])
    phone = StringField("Phone", validators=[Optional(), Length(max=50)])
    linkedin = StringField("LinkedIn URL", validators=[Optional(), Length(max=255)])
    twitter = StringField("Twitter / X URL", validators=[Optional(), Length(max=255)])
    display_order = IntegerField(
        "Display Order", validators=[Optional(), NumberRange(min=0)], default=0
    )
    is_active = BooleanField("Show on About page", default=True)
    submit = SubmitField("Save Team Member")
