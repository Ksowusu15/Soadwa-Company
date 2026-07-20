import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from flask import current_app


def send_password_reset_email(settings, admin, reset_url):
    """Send a branded password-reset email using the saved website settings."""
    if settings is None:
        current_app.logger.warning("Password reset requested without website settings.")
        return False

    smtp_host = (settings.smtp_host or "").strip()
    smtp_username = (settings.smtp_username or "").strip()
    smtp_password = settings.smtp_password or ""

    try:
        smtp_port = int(settings.smtp_port or 587)
    except (TypeError, ValueError):
        smtp_port = 587

    if not smtp_host or not smtp_username or not smtp_password:
        current_app.logger.warning("Password reset requested, but SMTP settings are incomplete.")
        return False

    company_name = (settings.company_name or "Soadwa Company Ltd").strip()
    message = EmailMessage()
    message["Subject"] = f"Reset Your Password - {company_name}"
    message["From"] = formataddr((company_name, smtp_username))
    message["To"] = admin.email
    message.set_content(
        f"Hello {admin.username},\n\n"
        f"We received a request to reset the password for your {company_name} "
        "administrator account.\n\n"
        f"Reset your password using this secure link:\n{reset_url}\n\n"
        "This link expires in 15 minutes and can only be used once.\n\n"
        "If you did not request this reset, you can safely ignore this email.\n\n"
        f"Regards,\n{company_name}\nAdministration"
    )

    context = ssl.create_default_context()

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(
                smtp_host,
                smtp_port,
                context=context,
                timeout=30,
            ) as server:
                server.login(smtp_username, smtp_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(smtp_username, smtp_password)
                server.send_message(message)

        current_app.logger.info("Password reset email sent to %s.", admin.email)
        return True
    except smtplib.SMTPAuthenticationError:
        current_app.logger.exception(
            "SMTP authentication failed. Use a valid provider app password."
        )
    except (OSError, smtplib.SMTPException):
        current_app.logger.exception("Unable to send password reset email.")

    return False
