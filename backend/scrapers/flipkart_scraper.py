import logging
import asyncio
import random
from scrapers.base_scraper import BaseScraper, StockResult

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


class FlipkartScraper(BaseScraper):
    @property
    def retailer_name(self) -> str:
        return "flipkart"

    async def check_stock(self) -> StockResult:
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
                user_agent = random.choice(USER_AGENTS)
                context = await browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": 1280, "height": 720},
                    locale="en-IN",
                )
                page = await context.new_page()
                await stealth_async(page)

                await asyncio.sleep(random.uniform(1.0, 3.0))

                await page.goto(self.url, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle")

                html = (await page.content()).lower()

                # Check if product is sold out
                is_sold_out = "sold out" in html or "this item is currently out of stock" in html
                
                # Check for buy buttons
                has_buy_button = (
                    "add to cart" in html
                    or "buy now" in html
                    or "notify me" in html  # But notify me means out of stock!
                )
                
                in_stock = has_buy_button and not is_sold_out
                if "notify me" in html and "add to cart" not in html:
                    in_stock = False

                # Extract price
                price = None
                try:
                    # Flipkart standard price selector is usually a div containing class '_30jeq3' or '_16Jk6d'
                    # or checking element text with a Rupee symbol
                    price_element = await page.query_selector("div[class*='_30jeq3'], div[class*='_16Jk6d'], div[class*='Nx9bqa']")
                    if price_element:
                        price_text = await price_element.text_content()
                        # Clean price
                        cleaned_price = price_text.replace("₹", "").replace(",", "").strip()
                        price = int(cleaned_price)
                except Exception as pe:
                    logger.debug(f"Failed to parse Flipkart price: {pe}")

                await browser.close()

                return StockResult(
                    retailer=self.retailer_name,
                    product_slug=self.product_slug,
                    in_stock=in_stock,
                    price=price,
                    url=self.url,
                )

        except Exception as e:
            logger.error(f"Error scraping Flipkart: {e}", exc_info=True)
            return StockResult(
                retailer=self.retailer_name,
                product_slug=self.product_slug,
                in_stock=False,
                price=None,
                url=self.url,
                error=str(e),
            )
