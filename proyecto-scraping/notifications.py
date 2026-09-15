"""
Alert layer (Action). Sends Telegram notifications when a price drop
is detected.
"""
import logging

import requests

from config import TELEGRAM_CHAT_ID, TELEGRAM_TOKEN

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"
TIMEOUT_S = 10


def send_telegram(message: str) -> bool:
    """Sends a message via Telegram. Returns True on success."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error(
            "TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not set. Check your .env file."
        )
        return False

    url = TELEGRAM_API_URL.format(token=TELEGRAM_TOKEN)
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

    try:
        response = requests.post(url, data=payload, timeout=TIMEOUT_S)
        response.raise_for_status()
        logger.info("Notification sent: %s", message)
        return True
    except requests.RequestException as exc:
        logger.error("Error sending Telegram notification: %s", exc)
        return False