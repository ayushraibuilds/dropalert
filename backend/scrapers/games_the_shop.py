import logging
import httpx
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper, StockResult

logger = logging.getLogger(__name__)


class GamesTheShopScraper(BaseScraper):
    @property
    def retailer_name(self) -> str:
        return "games_the_shop"

    async def check_stock(self) -> StockResult:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Referer": "https://www.gamesthe.shop/",
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.url, headers=headers)

                if response.status_code != 200:
                    return StockResult(
                        retailer=self.retailer_name,
                        product_slug=self.product_slug,
                        in_stock=False,
                        price=None,
                        url=self.url,
                        error=f"Games The Shop returned status code {response.status_code}",
                    )

                soup = BeautifulSoup(response.text, "html.parser")
                html_lower = response.text.lower()

                # Games The Shop typically uses an 'add to cart' class or button.
                # Check for "out of stock" or "pre-order" markers.
                # Sometimes pre-orders are effectively in stock for purchase.
                is_out_of_stock = (
                    "out of stock" in html_lower
                    or "temporarily unavailable" in html_lower
                    or "sold out" in html_lower
                )
                has_buy_button = (
                    "buy now" in html_lower
                    or "add to cart" in html_lower
                    or "pre-order" in html_lower
                )

                in_stock = has_buy_button and not is_out_of_stock

                # Try to parse the price
                price = None
                try:
                    # Look for product price class, e.g., class containing "price"
                    # Games The Shop often has a div/span with class containing "price" or "our-price"
                    price_tags = soup.find_all(
                        class_=lambda c: c and ("price" in c or "amount" in c)
                    )
                    for tag in price_tags:
                        text = tag.text.replace("₹", "").replace(",", "").strip()
                        if text.isdigit():
                            price = int(text)
                            break
                except Exception as pe:
                    logger.debug(f"Failed to parse price: {pe}")

                return StockResult(
                    retailer=self.retailer_name,
                    product_slug=self.product_slug,
                    in_stock=in_stock,
                    price=price,
                    url=self.url,
                )

        except Exception as e:
            logger.error(
                f"Error checking Games The Shop stock: {e}", exc_info=True
            )
            return StockResult(
                retailer=self.retailer_name,
                product_slug=self.product_slug,
                in_stock=False,
                price=None,
                url=self.url,
                error=str(e),
            )
