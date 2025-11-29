"""
arXiv Newsletter - A personalized newsletter generator for arXiv papers.

This package helps you stay up-to-date with the latest research papers
from arXiv by tracking authors you follow and finding similar papers.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .config import Config
from .fetcher import ArxivFetcher
from .filter import PaperFilter
from .generator import NewsletterGenerator
from .latex_generator import LaTeXNewsletterGenerator
from .cache import NewsletterCache

__all__ = ["Config", "ArxivFetcher", "PaperFilter", "NewsletterGenerator", "LaTeXNewsletterGenerator", "NewsletterCache"]
