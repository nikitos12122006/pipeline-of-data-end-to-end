# PriceTrack

PriceTrack is an automated data pipeline that monitors product prices on e-commerce sites, stores their historical evolution in a lightweight database, and sends instant Telegram notifications when a price drop is detected.

It covers the full data lifecycle in a small, easy-to-read codebase:

- **Ingest (Extract):** automated web scraping with [Playwright](https://playwright.dev/).
- **Store (Load):** structured persistence in a relational database (SQLite).
- **Process & Alert (Transform & Action):** historical price comparison and real-time communication via the Telegram Bot API.

## Architecture

```
products.json ──► main.py ──► scraper.py ──► database.py ──► notifications.py
                     │              │              │               │
                 orchestrates   fetches price   stores price   sends Telegram
                                 (Playwright)     (SQLite)         alert
```

Each script has a single responsibility, which makes the pipeline easy to test, extend, and reuse:

| File | Layer | Responsibility |
|---|---|---|
| `config.py` | Configuration | Loads secrets from `.env`, resolves file paths, loads the product list from `products.json`, and sets up logging. |
| `scraper.py` | Extract | Opens each product URL in a headless browser and pulls out the current price. |
| `database.py` | Load | Creates the SQLite schema and reads/writes products and price history. |
| `notifications.py` | Action | Sends a Telegram message via the Bot API when a price drop is detected. |
| `main.py` | Orchestration | Ties everything together: loops over products, calls the scraper, saves the result, decides whether to notify. |

### `config.py`
Central place for anything the rest of the project needs to know. It loads `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` from environment variables (via `.env`, so secrets never get committed to Git), defines where the SQLite database and log file live, and exposes `load_products()`, which reads the list of tracked products from `products.json`. It also configures Python's `logging` module so every run writes to both the console and `pricetrack.log`.

### `scraper.py`
The scraping engine. `get_price(url)` launches a headless Chromium browser with Playwright, navigates to the product page, waits for the price element to appear, and parses it into a `float`. If the price selector isn't found — because the page structure changed, the request got blocked, or a captcha appeared — it raises a clear `PriceNotFoundError` instead of crashing silently, and the browser is always closed via a `finally` block even if something goes wrong.

### `database.py`
The persistence layer, built on two SQLite tables:
- `products` — one row per tracked URL (id, name, url).
- `price_history` — one row per price reading, linked to a product, with a UTC `timestamp`.

This schema (instead of a single flat table) is what actually makes "historical evolution" possible and lets the project track multiple products at once. Key functions: `init_db()` creates the tables if missing, `get_or_create_product()` avoids duplicate rows for the same URL, `save_price()` inserts a new reading, and `get_last_price()` retrieves the previous reading so `main.py` can compare it against the new one.

### `notifications.py`
A thin wrapper around the Telegram Bot API. `send_telegram(message)` sends a `POST` request (instead of hand-building a URL with string interpolation, which breaks on special characters like `€` or `¡`), checks the response with `raise_for_status()`, and logs success or failure instead of letting the request fail silently.

### `main.py`
The entry point. For each product in `products.json`, it: registers the product in the database if it's new, fetches the last known price, scrapes the current price, saves it, and sends a Telegram notification if the price is below the configured `threshold` **or** lower than the last recorded price. Run it directly with:

```bash
python main.py
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
2. Copy `.env.example` to `.env` and fill in your Telegram bot token and chat ID (get these from [@BotFather](https://t.me/BotFather) on Telegram).
3. Copy `products.example.json` to `products.json` and list the products you want to track.
4. Run it:
   ```bash
   python main.py
   ```
5. (Optional) Schedule it to run automatically with `cron`, the `schedule` Python library, or a scheduled GitHub Action, so it checks prices periodically without manual intervention.

## ⚠️ A note on scraping Amazon specifically

This project uses Amazon as the example target because it's a familiar, price-rich site to demo the pipeline against. In practice, Amazon is one of the **hardest and riskiest** sites to scrape reliably, for a few reasons worth being upfront about — especially if this project goes in a portfolio:

- **Fragile HTML:** Amazon changes its page structure frequently. The CSS selector in `scraper.py` (`span.a-price-whole`) can and will break without warning; there's no stable public contract for it.
- **Anti-bot defenses:** repeated automated requests from the same IP are likely to trigger CAPTCHAs or temporary blocks, which will make `get_price()` fail (correctly caught as a `PriceNotFoundError`, but still a dead end until the block clears).
- **Terms of Service:** Amazon's ToS explicitly restrict automated data collection from its site. Running this against Amazon at any real frequency, or at scale, isn't something to do in production without checking the legal implications for your use case and jurisdiction.

**For a data engineering portfolio, the honest framing is:** this project demonstrates the *pipeline architecture* — ingestion, storage, transformation, alerting — using Amazon as a convenient, realistic-looking example. In an actual production deployment, you'd point the scraper at a site that permits it (many smaller e-commerce sites do), or better yet, use an official product/price API where one is available, and keep the same architecture underneath. It's worth saying this explicitly in interviews or in the repo description — it shows you understand not just how to scrape, but when scraping is and isn't the right tool.

## Tech stack

- **Python 3.10+** (uses the `X | None` type hint syntax)
- **Playwright** — browser automation for scraping
- **SQLite** — lightweight relational storage
- **Telegram Bot API** — real-time notifications
- **python-dotenv** — environment-based configuration
