import logging
import httpx
from scrapers.base_scraper import BaseScraper, StockResult

logger = logging.getLogger(__name__)


class CromaScraper(BaseScraper):
    @property
    def retailer_name(self) -> str:
        return "croma"

    async def check_stock(self) -> StockResult:
        # Expected URL format: https://www.croma.com/api/v2/products/{sku}/stock-availability
        # or if configured with normal product URL, we extract the SKU from the URL.
        # Example URL: https://www.croma.com/sony-playstation-5-console-slim/p/304193
        # The SKU/Product ID is the numeric part at the end: '304193'
        try:
            sku = self.url.rstrip("/").split("/")[-1]
            if sku.startswith("p-"):
                sku = sku[2:]
            elif "-" in sku:
                sku = sku.split("-")[-1]

            api_url = (
                f"https://www.croma.com/api/v2/products/{sku}/stock-availability"
            )

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Referer": self.url,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(api_url, headers=headers)

                if response.status_code != 200:
                    return StockResult(
                        retailer=self.retailer_name,
                        product_slug=self.product_slug,
                        in_stock=False,
                        price=None,
                        url=self.url,
                        error=f"API returned status code {response.status_code}",
                    )

                data = response.json()
                # Typical response structure check:
                # {"stockLevelStatus": {"code": "inStock"}, "price": {"value": 54990.0}}
                # or {"stockLevelStatus": "inStock"}
                # Let's handle both dictionary status or direct keys
                stock_status = data.get("stockLevelStatus", {})
                status_code = ""
                if isinstance(stock_status, dict):
                    status_code = stock_status.get("code", "").lower()
                else:
                    status_code = str(stock_status).lower()

                in_stock = status_code in ["instock", "available", "limited"]

                # Extract price if present
                price_data = data.get("price", {})
                price = None
                if isinstance(price_data, dict):
                    price = price_data.get("value")
                    if price:
                        price = int(float(price))
                elif isinstance(price_data, (int, float)):
                    price = int(price_data)

                return StockResult(
                    retailer=self.retailer_name,
                    product_slug=self.product_slug,
                    in_stock=in_stock,
                    price=price,
                    url=self.url,
                )

        except Exception as e:
            logger.error(f"Error checking Croma stock: {e}", exc_info=True)
            return StockResult(
                retailer=self.retailer_name,
                product_slug=self.product_slug,
                in_stock=False,
                price=None,
                url=self.url,
                error=str(e),
            )
