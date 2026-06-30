import logging
from config import settings

logger = logging.getLogger(__name__)


async def send_whatsapp_alert(to_phone: str, body: str) -> bool:
    """Send WhatsApp message using Twilio WhatsApp API (Premium Tier)."""
    if (
        not settings.TWILIO_ACCOUNT_SID
        or not settings.TWILIO_AUTH_TOKEN
        or not settings.TWILIO_WHATSAPP_NUMBER
    ):
        logger.warning("Twilio credentials not configured. Skipping WhatsApp alert.")
        return False

    try:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        # Phone numbers must contain country prefix (e.g. +91XXXXXXXXXX)
        to_number = (
            f"whatsapp:{to_phone}"
            if not to_phone.startswith("whatsapp:")
            else to_phone
        )
        from_number = (
            f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}"
            if not settings.TWILIO_WHATSAPP_NUMBER.startswith("whatsapp:")
            else settings.TWILIO_WHATSAPP_NUMBER
        )

        # Note: Twilio requires approved WhatsApp Templates for user-initiated conversations,
        # but Sandbox allows free-form text. During development/testing we use free-form.
        message = client.messages.create(
            body=body, from_=from_number, to=to_number
        )

        if message.sid:
            logger.info(
                f"WhatsApp message SID {message.sid} sent successfully to {to_phone}"
            )
            return True
        else:
            logger.error(f"Failed to get message SID from Twilio")
            return False

    except Exception as e:
        logger.error(f"Error sending WhatsApp alert: {e}", exc_info=True)
        return False
