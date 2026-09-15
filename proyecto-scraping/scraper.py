"""
Ingestion layer (Extract). Brings a product's current price via web
scraping with Playwright.
"""
import logging

from playwright.sync_api import Error as PlaywrightError, sync_playwright

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# CSS selector for the price. Amazon changes its HTML often: if this
# stops working, inspect the page and update this value.
PRICE_SELECTOR = "span.a-price-whole"

TIMEOUT_MS = 15_000


class PriceNotFoundError(Exception):
    """The selector could not find the price on the page (HTML changed, captcha, etc.)."""


def get_price(url: str) -> float:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(url, timeout=TIMEOUT_MS)

            try:
                page.wait_for_selector(PRICE_SELECTOR, timeout=TIMEOUT_MS)
            except PlaywrightError as exc:
                raise PriceNotFoundError(
                    f"Could not find selector '{PRICE_SELECTOR}' on {url}. "
                    "Has the page's HTML changed, or is there a captcha?"
                ) from exc

            price_text = page.locator(PRICE_SELECTOR).first.inner_text()
            price = float(price_text.replace(".", "").replace(",", "."))
            logger.info("Price fetched from %s: %.2f", url, price)
            return price
        finally:
            browser.close()