# Caching System Guide

The arXiv Newsletter includes a smart caching system to avoid redundant API calls and speed up iterations, especially when you're just tweaking PDF styling.

## How It Works

### What Gets Cached

The system maintains three separate caches in the `.cache/` directory:

1. **papers.json** (1-2 MB)
   - All papers fetched from arXiv based on your search criteria
   - Includes titles, authors, abstracts, categories, etc.

2. **reference_papers.json** (~100 KB)
   - Papers by your followed authors used for similarity computation
   - Used to train the TF-IDF model

3. **filtered_papers.json** (200-500 KB)
   - Final filtered and scored papers
   - Includes relevance scores and match reasons
   - This is what gets turned into the PDF

4. **cache_metadata.json** (< 1 KB)
   - Timestamp of when cache was created
   - Hash of configuration used
   - Paper counts

### Cache Validity

Cache is considered valid if:
- ✅ It exists
- ✅ It's less than 24 hours old
- ✅ Configuration hasn't changed (authors, categories, keywords, days_back, exclusions)

If any of these conditions fail, the cache is automatically invalidated and fresh data is fetched.

### Configuration Hash

The system generates an MD5 hash of cache-relevant settings:
```python
{
    "authors": ["Author 1", "Author 2"],
    "categories": ["astro-ph.GA"],
    "keywords": ["star formation"],
    "days_back": 31,
    "max_authors": 1000,
    "exclude_keywords": ["review"]
}
```

If you change any of these, the hash changes and cache is invalidated.

**Note**: Changing PDF styling options (latex_style, full_abstracts, etc.) does NOT invalidate the cache!

## Commands

### Check Cache Status
```bash
arxiv-newsletter --cache-info
```

Output:
```
Cache Information:
  Valid: True
  Timestamp: 2025-11-28T15:30:00+00:00
  Papers: 692
  Days back: 31
  Config hash: 419dcb30...
  Papers cache: 1572.4 KB
  Reference cache: 91.7 KB
  Filtered cache: 225.5 KB
```

### Clear Cache
```bash
arxiv-newsletter --clear-cache
```

Removes all cache files. Next run will fetch fresh data.

### Ignore Cache
```bash
arxiv-newsletter --no-cache
```

Fetches fresh data even if valid cache exists. Updates the cache with new data.

### Use Cache (Default)
```bash
arxiv-newsletter
```

Automatically uses cache if valid, otherwise fetches fresh data.

## PDF-Only Mode 🚀

This is the killer feature for rapid iterations!

```bash
arxiv-newsletter --pdf-only
```

**What it does:**
1. Loads filtered papers directly from `filtered_papers.json`
2. Skips all API calls (no fetching, no similarity computation)
3. Regenerates the PDF immediately

**Perfect for:**
- Tweaking LaTeX vs. modern styling
- Adjusting abstract truncation
- Testing different layouts
- Adding/removing ADS links
- Any PDF-only configuration changes

**Speed:** ~1-2 seconds instead of ~30-60 seconds!

### Example Workflow

```bash
# First run: fetch and analyze papers (slow)
arxiv-newsletter
# ⏱️  Takes 30-60 seconds

# Edit config.yaml to enable LaTeX style
# output:
#   latex_style: true

# Regenerate PDF only (fast!)
arxiv-newsletter --pdf-only
# ⏱️  Takes 1-2 seconds

# Try different style
# output:
#   full_abstracts: true

# Regenerate again
arxiv-newsletter --pdf-only
# ⏱️  Takes 1-2 seconds
```

## Cache Invalidation Scenarios

### Automatically Invalidates

Changing any of these will invalidate cache:
- ✅ Adding/removing authors
- ✅ Changing categories
- ✅ Modifying keywords
- ✅ Adjusting days_back
- ✅ Changing max_authors exclusion
- ✅ Modifying exclude_keywords

### Does NOT Invalidate

These changes don't affect the cache:
- ✅ max_papers (just uses more/less from filtered cache)
- ✅ min_similarity_score (uses different subset)
- ✅ selection_mode (threshold vs. fill)
- ✅ output directory or filename
- ✅ latex_style, full_abstracts
- ✅ include_abstracts, include_links
- ✅ include_ads_links, group_by_category

**Tip**: Use `--pdf-only` when changing these!

## Manual Cache Management

### Inspect Cache Files

```bash
# View cache directory
ls -lh .cache/

# Preview papers cache
head -100 .cache/papers.json

# Count papers
jq 'length' .cache/papers.json
```

### Backup Cache

```bash
# Backup cache for different configs
cp -r .cache .cache_backup_astro
cp -r .cache .cache_backup_ml
```

### Restore Cache

```bash
# Restore previous cache
rm -rf .cache
cp -r .cache_backup_astro .cache
```

## Performance Benefits

### Without Cache
```
Step 1: Fetch papers      - 15-20 seconds
Step 2: Fetch references  - 10-15 seconds  
Step 3: Filter & rank     - 5-10 seconds
Step 4: Generate PDF      - 1-2 seconds
────────────────────────────────────────
Total:                     31-47 seconds
```

### With Cache (Valid)
```
Step 1: Load papers       - 0.5 seconds
Step 2: Load references   - 0.2 seconds  
Step 3: Filter & rank     - 5-10 seconds
Step 4: Generate PDF      - 1-2 seconds
────────────────────────────────────────
Total:                     6-13 seconds
```

### PDF-Only Mode
```
Load filtered papers      - 0.3 seconds
Generate PDF              - 1-2 seconds
────────────────────────────────────────
Total:                     1-3 seconds
```

## Best Practices

### 1. First Run of the Day
```bash
# Start fresh in the morning
arxiv-newsletter --no-cache
```

### 2. Iterating on Filters
```bash
# Use cache while tuning min_similarity_score
arxiv-newsletter  # Uses cache
# Edit config, adjust min_similarity_score
arxiv-newsletter  # Uses cache again, faster
```

### 3. Iterating on PDF Style
```bash
# Fetch once
arxiv-newsletter

# Then iterate quickly
arxiv-newsletter --pdf-only  # Edit styling
arxiv-newsletter --pdf-only  # Edit more
arxiv-newsletter --pdf-only  # Perfect!
```

### 4. Testing Different Configs
```bash
# Clear cache between major config changes
arxiv-newsletter --clear-cache
arxiv-newsletter --config config_astro.yaml

arxiv-newsletter --clear-cache  
arxiv-newsletter --config config_ml.yaml
```

### 5. Weekly Newsletter
```bash
# Use cache for multiple outputs
arxiv-newsletter                          # Fetch data
arxiv-newsletter --pdf-only               # PDF version
arxiv-newsletter --pdf-only --html        # HTML version
```

## Troubleshooting

### Cache seems stale but shows as valid

```bash
# Force refresh
arxiv-newsletter --clear-cache
arxiv-newsletter
```

### Config changed but cache wasn't invalidated

The system tracks specific fields. If you changed something not tracked (like a comment), the hash won't change. Clear cache manually:

```bash
arxiv-newsletter --clear-cache
```

### Want to see what's cached

```bash
# Pretty print first paper
jq '.[0]' .cache/papers.json

# Count papers by category
jq '[.[].primary_category] | group_by(.) | map({category: .[0], count: length})' .cache/filtered_papers.json
```

### Cache directory getting large

```bash
# Check size
du -sh .cache/

# Clear old cache
arxiv-newsletter --clear-cache

# Cache size should be 2-5 MB typically
```

## Summary

- ✅ Cache automatically speeds up repeat runs
- ✅ Valid for 24 hours
- ✅ Invalidates when search criteria change
- ✅ Use `--pdf-only` for super-fast styling iterations
- ✅ Use `--no-cache` to force fresh data
- ✅ Use `--cache-info` to check status

The caching system makes the workflow much smoother, especially when you're experimenting with different PDF styles or fine-tuning your search criteria! 🚀
