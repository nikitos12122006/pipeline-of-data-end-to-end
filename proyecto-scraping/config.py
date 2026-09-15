"""
Centralized configuration for the PriceTrack project.
Loads credentials from environment variables (.env) and the list of
products to monitor from products.json.
"""
import json
import logging
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# --- Telegram ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Database ---
DB_PATH = BASE_DIR / "prices.db"

# --- Products to monitor ---
PRODUCTS_FILE = BASE_DIR / "products.json"


def load_products() -> list[dict]:
    """Reads the list of products from products.json.

    Each product is a dict with: name, url, threshold (price below
    which a notification is sent).
    """
    if not PRODUCTS_FILE.exists():
        raise FileNotFoundError(
            f"Could not find {PRODUCTS_FILE}. Copy products.example.json "
            "to products.json and edit it with your products."
        )
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Logging ---
LOG_FILE = BASE_DIR / "pricetrack.log"


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )