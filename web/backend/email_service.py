"""
Email service for sending verification and password reset emails.
Uses SMTP with configurable settings via environment variables.
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

# Email configuration from environment variables
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "VDV463 Validator")

# Application URL for links in emails
APP_URL = os.environ.get("APP_URL", "http://localhost:8000")


def send_email(to_email: str, subject: str, html_content: str, text_content: str | None = None) -> bool:
    """
    Send an email using SMTP.

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML body content
        text_content: Plain text body content (optional fallback)

    Returns:
        True if email was sent successfully, False otherwise
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured. Email not sent.")
        logger.info(f"Would send email to {to_email}: {subject}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg["To"] = to_email

        # Add text and HTML parts
        if text_content:
            part1 = MIMEText(text_content, "plain")
            msg.attach(part1)

        part2 = MIMEText(html_content, "html")
        msg.attach(part2)

        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM_EMAIL, to_email, msg.as_string())

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_verification_email(to_email: str, token: str, language: str = "de") -> bool:
    """Send email verification email."""
    verification_url = f"{APP_URL}/verify-email?token={token}"

    if language == "de":
        subject = "E-Mail-Adresse bestätigen - VDV463 Validator"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Willkommen beim VDV463 Validator!</h1>
                <p>Bitte bestätigen Sie Ihre E-Mail-Adresse, indem Sie auf den folgenden Button klicken:</p>
                <a href="{verification_url}" class="button">E-Mail bestätigen</a>
                <p>Oder kopieren Sie diesen Link in Ihren Browser:</p>
                <p>{verification_url}</p>
                <p>Dieser Link ist 24 Stunden gültig.</p>
                <div class="footer">
                    <p>Falls Sie sich nicht registriert haben, können Sie diese E-Mail ignorieren.</p>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        subject = "Verify your email - VDV463 Validator"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to VDV463 Validator!</h1>
                <p>Please verify your email address by clicking the button below:</p>
                <a href="{verification_url}" class="button">Verify Email</a>
                <p>Or copy this link into your browser:</p>
                <p>{verification_url}</p>
                <p>This link expires in 24 hours.</p>
                <div class="footer">
                    <p>If you didn't register, you can safely ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

    return send_email(to_email, subject, html_content)


def send_password_reset_email(to_email: str, token: str, language: str = "de") -> bool:
    """Send password reset email."""
    reset_url = f"{APP_URL}/reset-password?token={token}"

    if language == "de":
        subject = "Passwort zurücksetzen - VDV463 Validator"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Passwort zurücksetzen</h1>
                <p>Sie haben eine Anfrage zum Zurücksetzen Ihres Passworts gestellt. Klicken Sie auf den folgenden Button:</p>
                <a href="{reset_url}" class="button">Passwort zurücksetzen</a>
                <p>Oder kopieren Sie diesen Link in Ihren Browser:</p>
                <p>{reset_url}</p>
                <p>Dieser Link ist 1 Stunde gültig.</p>
                <div class="footer">
                    <p>Falls Sie diese Anfrage nicht gestellt haben, können Sie diese E-Mail ignorieren.</p>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        subject = "Reset your password - VDV463 Validator"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Reset Your Password</h1>
                <p>You requested to reset your password. Click the button below:</p>
                <a href="{reset_url}" class="button">Reset Password</a>
                <p>Or copy this link into your browser:</p>
                <p>{reset_url}</p>
                <p>This link expires in 1 hour.</p>
                <div class="footer">
                    <p>If you didn't request this, you can safely ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

    return send_email(to_email, subject, html_content)


def send_welcome_email(to_email: str, language: str = "de") -> bool:
    """Send welcome email after successful registration."""
    if language == "de":
        subject = "Willkommen beim VDV463 Validator"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Willkommen!</h1>
                <p>Ihr Konto wurde erfolgreich erstellt. Sie können sich jetzt anmelden und die VDV463-Validierung nutzen.</p>
                <a href="{APP_URL}" class="button">Zur Anwendung</a>
            </div>
        </body>
        </html>
        """
    else:
        subject = "Welcome to VDV463 Validator"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome!</h1>
                <p>Your account has been created successfully. You can now log in and use VDV463 validation.</p>
                <a href="{APP_URL}" class="button">Go to Application</a>
            </div>
        </body>
        </html>
        """

    return send_email(to_email, subject, html_content)
