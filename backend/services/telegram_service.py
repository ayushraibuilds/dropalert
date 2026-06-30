import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)


async def send_telegram_message(chat_id: str, message: str) -> bool:
    """Send message to a specific Telegram Chat ID using HTTP request."""
    if not settings.TELEGRAM_TOKEN:
        logger.warning(
            "Telegram token is not configured. Skipping telegram alert."
        )
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                logger.info(f"Telegram message sent successfully to {chat_id}")
                return True
            else:
                logger.error(
                    f"Telegram API returned error: {response.status_code} - {response.text}"
                )
                return False
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}", exc_info=True)
        return False
