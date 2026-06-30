import logging
import asyncio
import random
from scrapers.base_scraper import BaseScraper, StockResult

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]


class AmazonScraper(BaseScraper):
    @property
    def retailer_name(self) -> str:
        return "amazon"

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
                
                # Add random user-agent and settings to bypass Amazon anti-bot
                user_agent = random.choice(USER_AGENTS)
                context = await browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": 1920, "height": 1080},
                    locale="en-IN",
                )
                
                page = await context.new_page()
                await stealth_async(page)

                # Anti-bot sleep delay
                await asyncio.sleep(random.uniform(2.0, 5.0))

                # Go to Amazon product page
                await page.goto(self.url, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle")

                html = (await page.content()).lower()

                # Check if Amazon blocked us (e.g. captcha page)
                if "api-services-support@amazon.com" in html or "enter the characters you see below" in html:
                    await browser.close()
                    return StockResult(
                        retailer=self.retailer_name,
                        product_slug=self.product_slug,
                        in_stock=False,
                        price=None,
                        url=self.url,
                        error="Amazon scraper was blocked by CAPTCHA",
                    )

                # Check indicators for stock
                # Amazon India "Add to Cart" button typically has id="add-to-cart-button"
                add_to_cart = await page.query_selector("#add-to-cart-button")
                buy_now = await page.query_selector("#buy-now-button")
                
                # Out of stock markers
                out_of_stock_div = await page.query_selector("#outOfStock")
                availability_text_div = await page.query_selector("#availability")
                availability_text = ""
                if availability_text_div:
                    availability_text = (await availability_text_div.text_content()).lower()

                in_stock = (add_to_cart is not None or buy_now is not None) and (out_of_stock_div is None)
                if "currently unavailable" in availability_text or "out of stock" in availability_text:
                    in_stock = False

                # Extract price
                price = None
                try:
                    # Amazon price class is usually .a-price-whole
                    price_element = await page.query_selector(".a-price-whole")
                    if price_element:
                        price_text = await price_element.text_content()
                        # Clean price (remove commas, decimals, spaces)
                        cleaned_price = price_text.replace(",", "").replace(".", "").strip()
                        price = int(cleaned_price)
                except Exception as pe:
                    logger.debug(f"Failed to parse Amazon price: {pe}")

                await browser.close()

                return StockResult(
                    retailer=self.retailer_name,
                    product_slug=self.product_slug,
                    in_stock=in_stock,
                    price=price,
                    url=self.url,
                )

        except Exception as e:
            logger.error(f"Error scraping Amazon: {e}", exc_info=True)
            return StockResult(
                retailer=self.retailer_name,
                product_slug=self.product_slug,
                in_stock=False,
                price=None,
                url=self.url,
                error=str(e),
            )
