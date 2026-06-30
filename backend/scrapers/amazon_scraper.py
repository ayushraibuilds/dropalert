from scrapers.base_scraper import BaseScraper, StockResult


class AmazonScraper(BaseScraper):
    @property
    def retailer_name(self) -> str:
        return "amazon"

    async def check_stock(self) -> StockResult:
        # Placeholder for Phase 5 implementation
        return StockResult(
            retailer=self.retailer_name,
            product_slug=self.product_slug,
            in_stock=False,
            price=None,
            url=self.url,
            error="Amazon scraper placeholder",
        )
