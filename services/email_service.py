import html
import os

from brevo import Brevo
from brevo.transactional_emails import (
    SendTransacEmailRequestSender,
    SendTransacEmailRequestToItem,
)
from flask import current_app


def _brevo_settings(settings=None):
    company_name = (
        settings.company_name
        if settings and settings.company_name
        else "Soadwa Company Ltd"
    ).strip()

    return {
        "api_key": os.getenv("BREVO_API_KEY", "").strip(),
        "sender_email": os.getenv("BREVO_FROM_EMAIL", "").strip(),
        "sender_name": (
            os.getenv("BREVO_FROM_NAME", company_name).strip() or company_name
        ),
        "company_name": company_name,
    }


def _send_brevo_email(*, subject, html_content, recipient_email, recipient_name, settings=None):
    config = _brevo_settings(settings)

    if not config["api_key"]:
        current_app.logger.error("BREVO_API_KEY is not configured.")
        return False

    if not config["sender_email"]:
        current_app.logger.error(
            "BREVO_FROM_EMAIL is not configured. "
            "Use an email address registered and verified as a sender in Brevo."
        )
        return False

    try:
        client = Brevo(api_key=config["api_key"], timeout=15.0)
        result = client.transactional_emails.send_transac_email(
            subject=subject,
            html_content=html_content,
            sender=SendTransacEmailRequestSender(
                name=config["sender_name"],
                email=config["sender_email"],
            ),
            to=[
                SendTransacEmailRequestToItem(
                    email=recipient_email,
                    name=recipient_name or recipient_email,
                )
            ],
            request_options={
                "timeout_in_seconds": 15,
                "max_retries": 1,
            },
        )

        current_app.logger.info(
            "Brevo email sent to %s. Message ID: %s",
            recipient_email,
            getattr(result, "message_id", "unknown"),
        )
        return True

    except Exception:
        current_app.logger.exception(
            "Unable to send transactional email through Brevo to %s.",
            recipient_email,
        )
        return False


def send_password_reset_email(settings, admin, reset_url):
    """Send a branded password-reset email through the Brevo HTTPS API."""
    config = _brevo_settings(settings)
    company_name = config["company_name"]

    safe_company = html.escape(company_name)
    safe_username = html.escape(admin.username)
    safe_reset_url = html.escape(reset_url, quote=True)

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:620px;margin:0 auto;
                padding:28px;color:#222;background:#fff;">
        <div style="border-bottom:3px solid #c1121f;padding-bottom:16px;margin-bottom:24px;">
            <h2 style="margin:0;color:#111;">{safe_company}</h2>
            <p style="margin:6px 0 0;color:#666;">Administrator password reset</p>
        </div>

        <p>Hello {safe_username},</p>
        <p>
            We received a request to reset the password for your
            {safe_company} administrator account.
        </p>

        <p style="margin:28px 0;">
            <a href="{safe_reset_url}"
               style="display:inline-block;padding:13px 22px;background:#c1121f;
                      color:#fff;text-decoration:none;border-radius:7px;
                      font-weight:600;">
                Reset Password
            </a>
        </p>

        <p>This secure link expires in 15 minutes and can only be used once.</p>
        <p>If you did not request this password reset, you can safely ignore this email.</p>

        <p style="margin-top:28px;">
            Regards,<br>
            <strong>{safe_company}</strong><br>
            Administration
        </p>
    </div>
    """

    return _send_brevo_email(
        subject=f"Reset Your Password - {company_name}",
        html_content=html_body,
        recipient_email=admin.email,
        recipient_name=admin.username,
        settings=settings,
    )


def send_enquiry_emails(settings, message, admin_email):
    """Notify the business about a new enquiry and acknowledge the customer."""
    config = _brevo_settings(settings)
    company_name = config["company_name"]

    safe_company = html.escape(company_name)
    safe_name = html.escape(message.name)
    safe_email = html.escape(message.email)
    safe_phone = html.escape(message.phone or "Not provided")
    safe_message = html.escape(message.message).replace("\n", "<br>")

    admin_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:660px;margin:0 auto;
                padding:28px;color:#222;background:#fff;">
        <div style="border-bottom:3px solid #c1121f;padding-bottom:16px;margin-bottom:24px;">
            <h2 style="margin:0;color:#111;">New Website Enquiry</h2>
            <p style="margin:6px 0 0;color:#666;">{safe_company}</p>
        </div>

        <p><strong>Name:</strong> {safe_name}</p>
        <p><strong>Email:</strong> {safe_email}</p>
        <p><strong>Phone:</strong> {safe_phone}</p>

        <div style="margin-top:22px;padding:18px;background:#f7f7f7;border-radius:10px;">
            <strong>Message</strong>
            <p style="margin-bottom:0;line-height:1.6;">{safe_message}</p>
        </div>

        <p style="margin-top:24px;color:#666;">
            This enquiry has also been saved in your admin dashboard.
        </p>
    </div>
    """

    admin_sent = _send_brevo_email(
        subject=f"New Website Enquiry - {message.name}",
        html_content=admin_body,
        recipient_email=admin_email,
        recipient_name=company_name,
        settings=settings,
    )

    customer_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:620px;margin:0 auto;
                padding:28px;color:#222;background:#fff;">
        <div style="border-bottom:3px solid #c1121f;padding-bottom:16px;margin-bottom:24px;">
            <h2 style="margin:0;color:#111;">{safe_company}</h2>
        </div>

        <p>Hello {safe_name},</p>

        <p>
            Thank you for your enquiry. We have received your message successfully
            and our team will get back to you shortly.
        </p>

        <p style="margin-top:26px;">
            Regards,<br>
            <strong>{safe_company}</strong>
        </p>
    </div>
    """

    customer_sent = _send_brevo_email(
        subject=f"We received your enquiry - {company_name}",
        html_content=customer_body,
        recipient_email=message.email,
        recipient_name=message.name,
        settings=settings,
    )

    return admin_sent, customer_sent
