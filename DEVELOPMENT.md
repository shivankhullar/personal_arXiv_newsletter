# Development Guide

## Setting up development environment

```bash
# Clone the repository
cd /Users/skhullar/Docs/Projects/personal_arXiv_newsletter

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

## Project Structure

```
arxiv_newsletter/
├── __init__.py          # Package initialization and exports
├── cli.py               # Command-line interface (main entry point)
├── config.py            # Configuration loading and validation
├── fetcher.py           # arXiv API interaction and paper fetching
├── filter.py            # Paper filtering, ranking, and similarity
└── generator.py         # PDF/HTML newsletter generation
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=arxiv_newsletter

# Run specific test file
pytest tests/test_config.py
```

## Code Quality

```bash
# Format code with black
black arxiv_newsletter/

# Check with flake8
flake8 arxiv_newsletter/
```

## Adding New Features

### Adding a new arXiv search method

1. Add method to `ArxivFetcher` class in `fetcher.py`
2. Update `fetch_all_papers()` to incorporate the new method
3. Update configuration in `config.py` if needed
4. Document in README.md

### Adding a new filtering criterion

1. Add scoring logic to `PaperFilter.filter_and_rank()` in `filter.py`
2. Add configuration option in `config.py`
3. Update `config.example.yaml`
4. Document in README.md

### Adding a new output format

1. Add generation method to `NewsletterGenerator` in `generator.py`
2. Add CLI flag in `cli.py`
3. Update README.md with usage example

## Release Process

1. Update version in `pyproject.toml` and `__init__.py`
2. Update CHANGELOG.md
3. Create git tag: `git tag v0.1.0`
4. Push tag: `git push origin v0.1.0`

## Common Development Tasks

### Testing with different configurations

```bash
# Create test configs
cp config.example.yaml test_config_ml.yaml
cp config.example.yaml test_config_astro.yaml

# Edit them for different fields
# Test each
arxiv-newsletter --config test_config_ml.yaml
arxiv-newsletter --config test_config_astro.yaml
```

### Debugging API calls

```python
# Add to fetcher.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Profiling performance

```bash
# Time the execution
time arxiv-newsletter

# Profile with cProfile
python -m cProfile -s cumtime -m arxiv_newsletter.cli
```

## API Reference

### Config

```python
from arxiv_newsletter import Config

config = Config("config.yaml")
# or
config = Config()  # Uses defaults

# Access properties
authors = config.authors
categories = config.categories
days_back = config.days_back
```

### ArxivFetcher

```python
from arxiv_newsletter import ArxivFetcher

fetcher = ArxivFetcher(config)

# Fetch papers
papers = fetcher.fetch_all_papers()
reference_papers = fetcher.fetch_reference_papers()

# Or fetch by specific method
author_papers = fetcher.fetch_papers_by_authors()
category_papers = fetcher.fetch_papers_by_categories()
keyword_papers = fetcher.fetch_papers_by_keywords()
```

### PaperFilter

```python
from arxiv_newsletter import PaperFilter

paper_filter = PaperFilter(config)

# Filter and rank papers
filtered = paper_filter.filter_and_rank(papers, reference_papers)

# Get statistics
stats = paper_filter.get_statistics(filtered)

# Group by category
grouped = paper_filter.group_by_category(filtered)
```

### NewsletterGenerator

```python
from arxiv_newsletter import NewsletterGenerator

generator = NewsletterGenerator(config)

# Generate PDF
generator.generate(papers, "output.pdf")

# Generate HTML
html = generator.generate_html_preview(papers)
with open("output.html", "w") as f:
    f.write(html)
```

## Troubleshooting

### Import errors during development

Make sure you installed in editable mode:
```bash
pip install -e .
```

### Changes not taking effect

Restart Python interpreter or reload modules:
```python
import importlib
import arxiv_newsletter
importlib.reload(arxiv_newsletter)
```

### arXiv API rate limiting

The arXiv API has rate limits. If you hit them:
- Wait a few seconds between requests
- Reduce the number of queries
- Cache results for development

## Contributing

When contributing:
1. Create a new branch for your feature
2. Write tests for new functionality
3. Ensure all tests pass
4. Format code with black
5. Update documentation
6. Submit a pull request

## Future Enhancements

- [ ] Add support for ADS API
- [ ] Email delivery of newsletters
- [ ] Web interface
- [ ] Better ML models (BERT, SciBERT)
- [ ] Citation analysis
- [ ] Markdown output
- [ ] RSS feed generation
- [ ] Database for tracking history
- [ ] Duplicate detection across weeks
- [ ] Scheduled generation
