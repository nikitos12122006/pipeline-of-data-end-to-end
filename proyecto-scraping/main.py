"""
Main orchestrator for PriceTrack.

Loops over the products defined in products.json, fetches each one's
current price, stores it in the database, and sends a Telegram
notification if the price has dropped below the configured threshold
or compared to the previous reading.
"""
import logging

from config import configure_logging, load_products
from database import (
    get_last_price,
    get_or_create_product,
    init_db,
    save_price,
)
from notifications import send_telegram
from scraper import PriceNotFoundError, get_price

logger = logging.getLogger(__name__)


def process_product(product: dict) -> None:
    name = product["name"]
    url = product["url"]
    threshold = product["threshold"]

    product_id = get_or_create_product(name, url)
    # Must read the previous price BEFORE saving the new one
    previous_price = get_last_price(product_id)

    try:
        current_price = get_price(url)
    except PriceNotFoundError as exc:
        logger.error("Could not fetch price for '%s': %s", name, exc)
        return

    save_price(product_id, current_price)
    print(f"[{name}] Current price: {current_price}")

    below_threshold = current_price < threshold
    has_dropped = previous_price is not None and current_price < previous_price

    if below_threshold or has_dropped:
        message = f"{name} is now {current_price}! {url}"
        send_telegram(message)


def main() -> None:
    configure_logging()
    init_db()
    products = load_products()

    logger.info("Checking %d product(s)...", len(products))
    for product in products:
        process_product(product)


if __name__ == "__main__":
    main()