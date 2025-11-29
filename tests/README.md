# Test directory for arXiv Newsletter

This directory contains tests for the arXiv Newsletter package.

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=arxiv_newsletter --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run with verbose output
pytest -v
```

## Test Structure

- `test_config.py` - Configuration loading and validation tests
- More tests can be added for other modules

## Writing Tests

Example test:

```python
def test_something():
    """Test description."""
    config = Config()
    assert config.days_back > 0
```

## Note

Some tests may require internet connection to test arXiv API functionality.
These can be marked with `@pytest.mark.integration` for optional execution.
