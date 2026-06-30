from scrapers.base_scraper import BaseScraper, StockResult
from scrapers.croma_scraper import CromaScraper
from scrapers.playstation_direct import PlayStationDirectScraper
from scrapers.reliance_scraper import RelianceDigitalScraper
from scrapers.games_the_shop import GamesTheShopScraper
from scrapers.vijaysales_scraper import VijaySalesScraper
from scrapers.amazon_scraper import AmazonScraper
from scrapers.flipkart_scraper import FlipkartScraper

SCRAPER_CLASSES = {
    "croma": CromaScraper,
    "playstation_direct": PlayStationDirectScraper,
    "reliance": RelianceDigitalScraper,
    "games_the_shop": GamesTheShopScraper,
    "vijaysales": VijaySalesScraper,
    "amazon": AmazonScraper,
    "flipkart": FlipkartScraper,
}

__all__ = [
    "BaseScraper",
    "StockResult",
    "SCRAPER_CLASSES",
    "CromaScraper",
    "PlayStationDirectScraper",
    "RelianceDigitalScraper",
    "GamesTheShopScraper",
    "VijaySalesScraper",
    "AmazonScraper",
    "FlipkartScraper",
]
