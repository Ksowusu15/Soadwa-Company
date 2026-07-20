import os

import resend
from flask import current_app


def send_password_reset_email(settings, admin, reset_url):
    """Send a branded password-reset email through the Resend HTTPS API."""

    api_key = os.getenv("RESEND_API_KEY", "").strip()

    if not api_key:
        current_app.logger.error(
            "RESEND_API_KEY is not configured."
        )
        return False

    company_name = (
        settings.company_name
        if settings and settings.company_name
        else "Soadwa Company Ltd"
    ).strip()

    sender_email = os.getenv(
        "RESEND_FROM_EMAIL",
        "onboarding@resend.dev",
    ).strip()

    resend.api_key = api_key

    text_body = (
        f"Hello {admin.username},\n\n"
        f"We received a request to reset the password for your "
        f"{company_name} administrator account.\n\n"
        f"Reset your password using this secure link:\n"
        f"{reset_url}\n\n"
        f"This link expires in 15 minutes and can only be used once.\n\n"
        f"If you did not request this reset, you can safely ignore "
        f"this email.\n\n"
        f"Regards,\n"
        f"{company_name}\n"
        f"Administration"
    )

    html_body = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #222;">
        <h2 style="color: #b91c1c;">{company_name}</h2>

        <p>Hello {admin.username},</p>

        <p>
            We received a request to reset the password for your
            {company_name} administrator account.
        </p>

        <p>
            <a
                href="{reset_url}"
                style="
                    display: inline-block;
                    padding: 12px 20px;
                    background: #b91c1c;
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                "
            >
                Reset Password
            </a>
        </p>

        <p>
            This link expires in 15 minutes and can only be used once.
        </p>

        <p>
            If you did not request this reset, you can safely ignore
            this email.
        </p>

        <p>
            Regards,<br>
            {company_name}<br>
            Administration
        </p>
    </div>
    """

    try:
        result = resend.Emails.send(
            {
                "from": f"{company_name} <{sender_email}>",
                "to": [admin.email],
                "subject": f"Reset Your Password - {company_name}",
                "text": text_body,
                "html": html_body,
            }
        )

        current_app.logger.info(
            "Password reset email sent to %s. Resend ID: %s",
            admin.email,
            result.get("id"),
        )
        return True

    except Exception:
        current_app.logger.exception(
            "Unable to send password reset email through Resend."
        )
        return False