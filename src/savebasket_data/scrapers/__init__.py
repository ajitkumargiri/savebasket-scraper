"""Scraper modules for automated store imports."""

from .aldi import scrape_aldi_products
from .jumbo import scrape_jumbo_products
from .vomar import scrape_vomar_products

__all__ = [
    'scrape_aldi_products',
    'scrape_jumbo_products',
    'scrape_vomar_products',
]
