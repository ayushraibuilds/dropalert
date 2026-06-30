import json
import logging
from pywebpush import webpush, WebPushException
from config import settings

logger = logging.getLogger(__name__)


async def send_push_notification(subscription_token: str, message: dict) -> bool:
    """
    Sends a Web Push notification to the browser subscription.
    The subscription_token is a JSON string containing the Web Push subscription info:
    {
      "endpoint": "...",
      "keys": {
        "p256dh": "...",
        "auth": "..."
      }
    }
    """
    if not settings.VAPID_PUBLIC_KEY or not settings.VAPID_PRIVATE_KEY:
        logger.warning(
            "VAPID VAPID_PUBLIC_KEY or VAPID_PRIVATE_KEY is not configured. Web Push alerts are disabled."
        )
        return False

    try:
        # Parse the stored push subscription token
        subscription_info = json.loads(subscription_token)
    except Exception as e:
        logger.error(f"Failed to parse push token JSON: {e}")
        return False

    try:
        # Send the web push notification
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(message),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={
                "sub": settings.VAPID_CLAIM_EMAIL,
            }
        )
        logger.info("Web push notification sent successfully.")
        return True
    except WebPushException as ex:
        # If the endpoint is no longer valid (e.g. subscription expired or revoked),
        # return False so caller can clean up or log
        logger.warning(f"Web Push failed with exception: {ex}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in send_push_notification: {e}", exc_info=True)
        return False
