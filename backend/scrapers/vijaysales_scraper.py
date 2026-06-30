import logging
import random
import asyncio
from scrapers.base_scraper import BaseScraper, StockResult

logger = logging.getLogger(__name__)


class VijaySalesScraper(BaseScraper):
    @property
    def retailer_name(self) -> str:
        return "vijaysales"

    async def check_stock(self) -> StockResult:
        # Since Vijay Sales uses heavy JavaScript-rendering and is prone to blocking,
        # we use Playwright in headless mode.
        try:
            from playwright.async_api import async_playwright
            from playwright_stealth import stealth_async
        except ImportError:
            return StockResult(
                retailer=self.retailer_name,
                product_slug=self.product_slug,
                in_stock=False,
                price=None,
                url=self.url,
                error="Playwright or Playwright-Stealth not installed",
            )

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 720},
                    locale="en-IN",
                )
                page = await context.new_page()

                # Enable stealth mode to bypass Cloudflare/bot detectors
                await stealth_async(page)

                # Random sleep before navigation to mimic human behavior
                await asyncio.sleep(random.uniform(1.0, 3.0))

                await page.goto(self.url, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle")

                html = (await page.content()).lower()

                # Check for out of stock signals
                # Common texts on Vijay Sales: "out of stock", "notify me", "temporarily unavailable"
                out_of_stock_signals = [
                    "out of stock",
                    "notify me",
                    "temporarily unavailable",
                    "sold out",
                ]

                is_out_of_stock = any(
                    sig in html for sig in out_of_stock_signals
                )
                has_buy_button = (
                    "add to cart" in html
                    or "buy now" in html
                    or "add-to-cart" in html
                )

                in_stock = has_buy_button and not is_out_of_stock

                # Attempt to parse price
                price = None
                try:
                    # Look for element with price attributes or class
                    price_element = await page.query_selector(
                        ".pdp-price, .price, .offer-price"
                    )
                    if price_element:
                        price_text = await price_element.text_content()
                        # Clean price string
                        cleaned = (
                            price_text.replace("₹", "")
                            .replace(",", "")
                            .strip()
                        )
                        price = int(float(cleaned))
                except Exception as pe:
                    logger.debug(f"Failed parsing price via selector: {pe}")

                await browser.close()

                return StockResult(
                    retailer=self.retailer_name,
                    product_slug=self.product_slug,
                    in_stock=in_stock,
                    price=price,
                    url=self.url,
                )

        except Exception as e:
            logger.error(
                f"Error checking Vijay Sales stock: {e}", exc_info=True
            )
            return StockResult(
                retailer=self.retailer_name,
                product_slug=self.product_slug,
                in_stock=False,
                price=None,
                url=self.url,
                error=str(e),
            )
