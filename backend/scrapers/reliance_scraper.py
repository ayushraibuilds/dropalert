import logging
import httpx
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper, StockResult

logger = logging.getLogger(__name__)


class RelianceDigitalScraper(BaseScraper):
    @property
    def retailer_name(self) -> str:
        return "reliance"

    async def check_stock(self) -> StockResult:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.reliancedigital.in/",
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
                        error=f"Reliance Digital returned code {response.status_code}",
                    )

                soup = BeautifulSoup(response.text, "html.parser")

                # Reliance Digital typically uses buttons with text "ADD TO CART" or "NOTIFY ME"
                # Let's inspect the page content case-insensitively.
                html_lower = response.text.lower()

                # Common markers for out of stock:
                # "temporarily out of stock", "notify me", "sold out", "currently unavailable"
                out_of_stock_markers = [
                    "notify me",
                    "temporarily out of stock",
                    "currently unavailable",
                    "sold out",
                    "limit exceeded",
                ]

                # Check if any out of stock marker is present in button-like text
                # We can also check if "add to cart" is present.
                has_add_to_cart = "add to cart" in html_lower or "buy now" in html_lower
                is_out_of_stock = any(
                    marker in html_lower for marker in out_of_stock_markers
                )

                in_stock = has_add_to_cart and not is_out_of_stock

                # Try parsing the price
                # Reliance Digital typically stores price inside a meta tag or specific class like '.pdp__priceSection'
                price = None
                try:
                    # Look for meta tag: <meta itemprop="price" content="54990" />
                    meta_price = soup.find("meta", {"itemprop": "price"})
                    if meta_price and meta_price.get("content"):
                        price = int(float(meta_price.get("content")))
                    else:
                        # Fallback: find price in text if class exists
                        price_el = soup.find(class_="pdp__priceSection")
                        if price_el:
                            # Strip currency symbols and commas
                            cleaned_price = (
                                price_el.text.replace("₹", "")
                                .replace(",", "")
                                .strip()
                            )
                            price = int(float(cleaned_price))
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
                f"Error checking Reliance Digital stock: {e}", exc_info=True
            )
            return StockResult(
                retailer=self.retailer_name,
                product_slug=self.product_slug,
                in_stock=False,
                price=None,
                url=self.url,
                error=str(e),
            )
