import abc
from dataclasses import dataclass
from typing import Optional


@dataclass
class StockResult:
    retailer: str
    product_slug: str
    in_stock: bool
    price: Optional[int]
    url: str
    error: Optional[str] = None


class BaseScraper(abc.ABC):
    def __init__(self, product_slug: str, url: str):
        self.product_slug = product_slug
        self.url = url

    @property
    @abc.abstractmethod
    def retailer_name(self) -> str:
        """Return the name of the retailer (e.g., 'amazon', 'croma')"""
        pass

    @abc.abstractmethod
    async def check_stock(self) -> StockResult:
        """Perform stock check and return StockResult"""
        pass
