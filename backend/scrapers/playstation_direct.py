import logging
import httpx
from scrapers.base_scraper import BaseScraper, StockResult

logger = logging.getLogger(__name__)


class PlayStationDirectScraper(BaseScraper):
    @property
    def retailer_name(self) -> str:
        return "playstation_direct"

    async def check_stock(self) -> StockResult:
        # ShopAtSC (Sony Centre India) is Shopify-based:
        # Appending '.js' to the product URL returns structured JSON.
        # Example URL: https://shopatsc.com/products/playstation-5-slim-console
        # If a direct.playstation.com URL is used, we fallback to parsing JSON status.
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
            }

            # Check if it is ShopAtSC (Shopify site)
            if "shopatsc.com" in self.url:
                json_url = self.url
                if not json_url.endswith(".js"):
                    # Strip trailing slash if present
                    json_url = json_url.rstrip("/") + ".js"

                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(json_url, headers=headers)

                    if response.status_code != 200:
                        return StockResult(
                            retailer=self.retailer_name,
                            product_slug=self.product_slug,
                            in_stock=False,
                            price=None,
                            url=self.url,
                            error=f"ShopAtSC returned code {response.status_code}",
                        )

                    data = response.json()
                    # Shopify product JSON structure contains:
                    # {"available": true, "price": 5499000} (price is in cents/paise)
                    in_stock = data.get("available", False)
                    price_paise = data.get("price", 0)
                    price = int(price_paise / 100) if price_paise else None

                    return StockResult(
                        retailer=self.retailer_name,
                        product_slug=self.product_slug,
                        in_stock=in_stock,
                        price=price,
                        url=self.url,
                    )
            else:
                # Fallback for official Sony PlayStation Direct API (direct.playstation.com)
                # It uses product availability API endpoint:
                # direct.playstation.com/api/products/availability
                # We can extract the SKU from self.url or query direct availability if configured
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Let's perform a get request to the URL, check direct HTML or API
                    response = await client.get(self.url, headers=headers)

                    if response.status_code != 200:
                        return StockResult(
                            retailer=self.retailer_name,
                            product_slug=self.product_slug,
                            in_stock=False,
                            price=None,
                            url=self.url,
                            error=f"Sony Direct returned status code {response.status_code}",
                        )

                    # Quick search in page HTML for in-stock markers or out of stock text
                    html = response.text.lower()
                    in_stock = (
                        "out of stock" not in html
                        and "currently unavailable" not in html
                        and "add to cart" in html
                    )

                    return StockResult(
                        retailer=self.retailer_name,
                        product_slug=self.product_slug,
                        in_stock=in_stock,
                        price=None,  # Page parsing price is tricky; set None if fallback
                        url=self.url,
                    )

        except Exception as e:
            logger.error(
                f"Error checking PlayStation Direct stock: {e}", exc_info=True
            )
            return StockResult(
                retailer=self.retailer_name,
                product_slug=self.product_slug,
                in_stock=False,
                price=None,
                url=self.url,
                error=str(e),
            )
