"""
Caching module for arXiv Newsletter.

Provides local storage for fetched papers and analysis results to avoid
redundant API calls and recomputation.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib


class NewsletterCache:
    """Cache manager for newsletter data."""
    
    def __init__(self, cache_dir: str = ".cache"):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Separate cache files for different data
        self.papers_cache = self.cache_dir / "papers.json"
        self.reference_cache = self.cache_dir / "reference_papers.json"
        self.filtered_cache = self.cache_dir / "filtered_papers.json"
        self.metadata_cache = self.cache_dir / "cache_metadata.json"
    
    def _get_config_hash(self, config) -> str:
        """
        Generate hash of configuration to detect changes.
        
        Args:
            config: Config object
        
        Returns:
            MD5 hash of relevant config parameters
        """
        # Create a dict of cache-relevant settings
        cache_key = {
            "authors": sorted(config.authors),
            "categories": sorted(config.categories),
            "keywords": sorted(config.keywords),
            "days_back": config.days_back,
            "max_authors": config.max_authors,
            "min_authors": config.min_authors,
            "exclude_keywords": sorted(config.exclude_keywords),
        }
        
        # Generate hash
        key_str = json.dumps(cache_key, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Load cache metadata."""
        if self.metadata_cache.exists():
            with open(self.metadata_cache, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self, metadata: Dict[str, Any]):
        """Save cache metadata."""
        with open(self.metadata_cache, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def is_valid(self, config, max_age_hours: int = 24) -> bool:
        """
        Check if cached data is valid for given config.
        
        Args:
            config: Current configuration
            max_age_hours: Maximum age of cache in hours
        
        Returns:
            True if cache is valid and fresh
        """
        if not self.papers_cache.exists():
            return False
        
        metadata = self._get_metadata()
        
        # Check if cache exists and has required fields
        if not metadata or "config_hash" not in metadata or "timestamp" not in metadata:
            return False
        
        # Check if config has changed
        current_hash = self._get_config_hash(config)
        if metadata["config_hash"] != current_hash:
            print("Cache invalid: configuration has changed")
            return False
        
        # Check cache age
        cache_time = datetime.fromisoformat(metadata["timestamp"])
        age_hours = (datetime.now(timezone.utc) - cache_time).total_seconds() / 3600
        
        if age_hours > max_age_hours:
            print(f"Cache invalid: {age_hours:.1f} hours old (max: {max_age_hours})")
            return False
        
        print(f"Cache valid: {age_hours:.1f} hours old")
        return True
    
    def save_papers(self, papers: List, config) -> None:
        """
        Save fetched papers to cache.
        
        Args:
            papers: List of Paper objects
            config: Current configuration
        """
        # Convert papers to serializable format
        papers_data = []
        for paper in papers:
            paper_dict = {
                "id": paper.id,
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "categories": paper.categories,
                "primary_category": paper.primary_category,
                "published": paper.published.isoformat() if paper.published else None,
                "updated": paper.updated.isoformat() if paper.updated else None,
                "pdf_url": paper.pdf_url,
                "arxiv_url": paper.arxiv_url,
                "ads_url": paper.ads_url,
            }
            papers_data.append(paper_dict)
        
        # Save papers
        with open(self.papers_cache, 'w') as f:
            json.dump(papers_data, f, indent=2)
        
        # Update metadata
        metadata = {
            "config_hash": self._get_config_hash(config),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "paper_count": len(papers),
            "days_back": config.days_back,
        }
        self._save_metadata(metadata)
        
        print(f"Cached {len(papers)} papers to {self.papers_cache}")
    
    def load_papers(self):
        """
        Load papers from cache.
        
        Returns:
            List of paper dictionaries
        """
        if not self.papers_cache.exists():
            return None
        
        with open(self.papers_cache, 'r') as f:
            papers_data = json.load(f)
        
        print(f"Loaded {len(papers_data)} papers from cache")
        return papers_data
    
    def save_reference_papers(self, papers: List) -> None:
        """
        Save reference papers to cache.
        
        Args:
            papers: List of reference Paper objects
        """
        papers_data = []
        for paper in papers:
            paper_dict = {
                "id": paper.id,
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "categories": paper.categories,
                "primary_category": paper.primary_category,
                "published": paper.published.isoformat() if paper.published else None,
                "updated": paper.updated.isoformat() if paper.updated else None,
                "pdf_url": paper.pdf_url,
                "arxiv_url": paper.arxiv_url,
                "ads_url": paper.ads_url,
            }
            papers_data.append(paper_dict)
        
        with open(self.reference_cache, 'w') as f:
            json.dump(papers_data, f, indent=2)
        
        print(f"Cached {len(papers)} reference papers")
    
    def load_reference_papers(self):
        """
        Load reference papers from cache.
        
        Returns:
            List of paper dictionaries
        """
        if not self.reference_cache.exists():
            return None
        
        with open(self.reference_cache, 'r') as f:
            papers_data = json.load(f)
        
        print(f"Loaded {len(papers_data)} reference papers from cache")
        return papers_data
    
    def save_filtered_papers(self, papers: List) -> None:
        """
        Save filtered/scored papers to cache.
        
        Args:
            papers: List of filtered Paper objects with scores
        """
        papers_data = []
        for paper in papers:
            paper_dict = {
                "id": paper.id,
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "categories": paper.categories,
                "primary_category": paper.primary_category,
                "published": paper.published.isoformat() if paper.published else None,
                "updated": paper.updated.isoformat() if paper.updated else None,
                "pdf_url": paper.pdf_url,
                "arxiv_url": paper.arxiv_url,
                "ads_url": paper.ads_url,
                "score": paper.score,
                "match_reason": paper.match_reason,
            }
            papers_data.append(paper_dict)
        
        with open(self.filtered_cache, 'w') as f:
            json.dump(papers_data, f, indent=2)
        
        print(f"Cached {len(papers)} filtered papers")
    
    def load_filtered_papers(self):
        """
        Load filtered papers from cache.
        
        Returns:
            List of paper dictionaries with scores
        """
        if not self.filtered_cache.exists():
            return None
        
        with open(self.filtered_cache, 'r') as f:
            papers_data = json.load(f)
        
        print(f"Loaded {len(papers_data)} filtered papers from cache")
        return papers_data
    
    def clear(self):
        """Clear all cache files."""
        for cache_file in [self.papers_cache, self.reference_cache, 
                          self.filtered_cache, self.metadata_cache]:
            if cache_file.exists():
                cache_file.unlink()
        print("Cache cleared")
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about current cache.
        
        Returns:
            Dictionary with cache information
        """
        metadata = self._get_metadata()
        
        info = {
            "valid": self.papers_cache.exists(),
            "metadata": metadata,
        }
        
        if self.papers_cache.exists():
            info["papers_size_kb"] = self.papers_cache.stat().st_size / 1024
        
        if self.reference_cache.exists():
            info["reference_size_kb"] = self.reference_cache.stat().st_size / 1024
        
        if self.filtered_cache.exists():
            info["filtered_size_kb"] = self.filtered_cache.stat().st_size / 1024
        
        return info
