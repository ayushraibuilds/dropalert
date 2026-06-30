import logging
from config import settings

logger = logging.getLogger(__name__)


async def send_email_alert(to_email: str, subject: str, body_html: str) -> bool:
    """Send an email using Resend SDK."""
    if not settings.RESEND_API_KEY:
        logger.warning("Resend API key not configured. Skipping email alert.")
        return False

    try:
        import resend

        resend.api_key = settings.RESEND_API_KEY

        # If domain is not verified, Resend allows sending to verified single sender only.
        # Default fallback from is 'onboarding@resend.dev' for testing.
        from_address = "DropAlert <onboarding@resend.dev>"
        # When domain is set up, update to:
        # from_address = "DropAlert Alerts <alerts@dropalert.in>"

        params = {
            "from": from_address,
            "to": [to_email],
            "subject": subject,
            "html": body_html,
        }

        # Send email synchronously as Resend SDK is synchronous,
        # but we wrap in async function.
        # Alternatively, we could run in an executor thread.
        response = resend.Emails.send(params)

        if response and response.get("id"):
            logger.info(f"Email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send email to {to_email}, invalid response")
            return False

    except Exception as e:
        logger.error(f"Error sending email alert: {e}", exc_info=True)
        return False
