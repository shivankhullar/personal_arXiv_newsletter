"""
Sample tests for arXiv Newsletter package.

Run with: pytest
"""

import pytest
from datetime import datetime
from arxiv_newsletter.config import Config


def test_config_defaults():
    """Test that default configuration loads correctly."""
    config = Config()
    
    assert isinstance(config.authors, list)
    assert isinstance(config.categories, list)
    assert isinstance(config.keywords, list)
    assert config.days_back >= 1
    assert config.max_papers >= 1
    assert 0 <= config.min_similarity_score <= 1


def test_config_validation():
    """Test configuration validation."""
    config = Config()
    
    # Test invalid days_back
    with pytest.raises(ValueError):
        config.config["days_back"] = 0
        config._validate_config()
    
    # Test invalid similarity score
    config = Config()
    with pytest.raises(ValueError):
        config.config["min_similarity_score"] = 1.5
        config._validate_config()


def test_output_path_generation():
    """Test output path generation."""
    config = Config()
    
    output_path = config.get_output_path(datetime(2025, 11, 28))
    assert "2025-11-28" in output_path
    assert output_path.endswith(".pdf")


def test_config_properties():
    """Test configuration property accessors."""
    config = Config()
    
    # All properties should be accessible
    assert hasattr(config, 'authors')
    assert hasattr(config, 'categories')
    assert hasattr(config, 'keywords')
    assert hasattr(config, 'days_back')
    assert hasattr(config, 'max_papers')
    assert hasattr(config, 'min_similarity_score')
    assert hasattr(config, 'output_directory')
    assert hasattr(config, 'include_abstracts')
    assert hasattr(config, 'include_links')
    assert hasattr(config, 'use_semantic_similarity')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
