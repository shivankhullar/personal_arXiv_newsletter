"""
Configuration module for arXiv Newsletter.

Handles loading and validation of user configuration from YAML files.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml


class Config:
    """Configuration handler for arXiv Newsletter."""
    
    DEFAULT_CONFIG = {
        "authors": [],
        "categories": [],
        "keywords": [],
        "days_back": 7,
        "max_papers": 20,
        "min_similarity_score": 0.3,
        "selection_mode": "threshold",
        "output": {
            "directory": "newsletters",
            "filename": "arxiv_newsletter_{date}.pdf",
            "include_abstracts": True,
            "full_abstracts": False,
            "include_links": True,
            "include_ads_links": True,
            "group_by_category": True,
            "latex_style": False,
        },
        "advanced": {
            "use_semantic_similarity": True,
            "reference_papers_limit": 50,
            "author_weight": 0.6,
        },
        "exclusions": {
            "max_authors": 0,
            "min_authors": 0,
            "exclude_keywords": [],
            "exclude_categories": [],
        },
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to config YAML file. If None, looks for config.yaml
                        in current directory, then uses defaults.
        """
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
        self._validate_config()
    
    def _find_config_file(self) -> Optional[str]:
        """Find config file in common locations."""
        possible_paths = [
            "config.yaml",
            "config.yml",
            os.path.expanduser("~/.arxiv_newsletter/config.yaml"),
            os.path.expanduser("~/.config/arxiv_newsletter/config.yaml"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        if self.config_path and os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                user_config = yaml.safe_load(f) or {}
            
            # Merge with defaults
            config = self.DEFAULT_CONFIG.copy()
            config.update(user_config)
            
            # Deep merge nested dicts
            for key in ["output", "advanced", "exclusions"]:
                if key in user_config:
                    config[key] = {**self.DEFAULT_CONFIG[key], **user_config[key]}
            
            return config
        else:
            print(f"Warning: No config file found. Using defaults.")
            print(f"Create a config.yaml file based on config.example.yaml")
            return self.DEFAULT_CONFIG.copy()
    
    def _validate_config(self):
        """Validate configuration values."""
        if not isinstance(self.config["authors"], list):
            raise ValueError("'authors' must be a list")
        
        if not isinstance(self.config["categories"], list):
            raise ValueError("'categories' must be a list")
        
        if self.config["days_back"] < 1:
            raise ValueError("'days_back' must be at least 1")
        
        if self.config["max_papers"] < 1:
            raise ValueError("'max_papers' must be at least 1")
        
        if not 0 <= self.config["min_similarity_score"] <= 1:
            raise ValueError("'min_similarity_score' must be between 0 and 1")
        
        if not 0 <= self.config["advanced"]["author_weight"] <= 1:
            raise ValueError("'author_weight' must be between 0 and 1")
        
        if self.config.get("selection_mode") not in ["threshold", "fill", None]:
            raise ValueError("'selection_mode' must be 'threshold' or 'fill'")
    
    @property
    def authors(self) -> List[str]:
        """Get list of authors to follow."""
        return self.config["authors"]
    
    @property
    def categories(self) -> List[str]:
        """Get list of arXiv categories to search."""
        return self.config["categories"]
    
    @property
    def keywords(self) -> List[str]:
        """Get list of keywords to search for."""
        return self.config["keywords"]
    
    @property
    def days_back(self) -> int:
        """Get number of days to look back for papers."""
        return self.config["days_back"]
    
    @property
    def max_papers(self) -> int:
        """Get maximum number of papers to include."""
        return self.config["max_papers"]
    
    @property
    def min_similarity_score(self) -> float:
        """Get minimum similarity score threshold."""
        return self.config["min_similarity_score"]
    
    @property
    def output_directory(self) -> str:
        """Get output directory for newsletters."""
        return self.config["output"]["directory"]
    
    @property
    def output_filename(self) -> str:
        """Get output filename pattern."""
        return self.config["output"]["filename"]
    
    def get_output_path(self, date: Optional[datetime] = None) -> str:
        """
        Get full output path for newsletter.
        
        Args:
            date: Date for filename. Uses current date if None.
        
        Returns:
            Full path to output PDF file.
        """
        if date is None:
            date = datetime.now()
        
        filename = self.output_filename.format(date=date.strftime("%Y-%m-%d"))
        
        # Create output directory if it doesn't exist
        output_dir = Path(self.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return str(output_dir / filename)
    
    @property
    def include_abstracts(self) -> bool:
        """Whether to include abstracts in newsletter."""
        return self.config["output"]["include_abstracts"]
    
    @property
    def include_links(self) -> bool:
        """Whether to include paper links in newsletter."""
        return self.config["output"]["include_links"]
    
    @property
    def group_by_category(self) -> bool:
        """Whether to group papers by category."""
        return self.config["output"]["group_by_category"]
    
    @property
    def use_semantic_similarity(self) -> bool:
        """Whether to use semantic similarity for filtering."""
        return self.config["advanced"]["use_semantic_similarity"]
    
    @property
    def reference_papers_limit(self) -> int:
        """Maximum number of reference papers to use."""
        return self.config["advanced"]["reference_papers_limit"]
    
    @property
    def author_weight(self) -> float:
        """Weight for author matching vs content similarity."""
        return self.config["advanced"]["author_weight"]
    
    @property
    def selection_mode(self) -> str:
        """Paper selection mode: 'threshold' or 'fill'."""
        return self.config.get("selection_mode", "threshold")
    
    @property
    def full_abstracts(self) -> bool:
        """Whether to include full abstracts without truncation."""
        return self.config["output"].get("full_abstracts", False)
    
    @property
    def include_ads_links(self) -> bool:
        """Whether to include ADS links."""
        return self.config["output"].get("include_ads_links", True)
    
    @property
    def latex_style(self) -> bool:
        """Whether to use LaTeX-style formatting."""
        return self.config["output"].get("latex_style", False)
    
    @property
    def max_authors(self) -> int:
        """Maximum number of authors (0 = no limit)."""
        return self.config.get("exclusions", {}).get("max_authors", 0)
    
    @property
    def min_authors(self) -> int:
        """Minimum number of authors (0 = no limit)."""
        return self.config.get("exclusions", {}).get("min_authors", 0)
    
    @property
    def exclude_keywords(self) -> List[str]:
        """Keywords to exclude from papers."""
        return self.config.get("exclusions", {}).get("exclude_keywords", [])
    
    @property
    def exclude_categories(self) -> List[str]:
        """Categories to exclude from papers."""
        return self.config.get("exclusions", {}).get("exclude_categories", [])
    
    def __repr__(self) -> str:
        """String representation of config."""
        return f"Config(authors={len(self.authors)}, categories={len(self.categories)})"
