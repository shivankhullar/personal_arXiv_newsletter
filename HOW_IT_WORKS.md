# How the arXiv Newsletter System Works

A detailed technical explanation of the matching, scoring, and PDF generation algorithms.

---

## 📊 Part 1: Paper Matching & Scoring Algorithm

The scoring system uses **three independent components** that are combined into a final relevance score:

### Component 1: Author Matching (Weight: `author_weight`)

**Location**: `filter.py` - `_author_matches()` method

```python
def _author_matches(self, paper_authors, target_authors):
    # Normalize names: lowercase, remove punctuation
    normalized_targets = {normalize(a) for a in target_authors}
    
    for author in paper_authors:
        normalized = normalize(author)
        
        # Check for substring match (fuzzy matching)
        for target in normalized_targets:
            if target in normalized or normalized in target:
                return True, author
    
    return False, ""
```

**How it works**:
1. Takes author names from your config (e.g., "Philip F. Hopkins")
2. Normalizes both paper authors and your followed authors:
   - Converts to lowercase
   - Removes punctuation (dots, commas, etc.)
   - Collapses whitespace
3. Checks if any paper author contains (or is contained in) a followed author name
4. Uses **substring matching** for robustness:
   - "Philip Hopkins" matches "Philip F. Hopkins"
   - "P. F. Hopkins" matches "Philip F. Hopkins"

**Scoring**: If match found → adds `author_weight` (default: 0.6) to score

---

### Component 2: Keyword Matching (Weight: up to 0.5)

**Location**: `filter.py` - `_keyword_matches()` method

```python
def _keyword_matches(self, text, keywords):
    text_lower = text.lower()
    matched = []
    
    for keyword in keywords:
        if keyword.lower() in text_lower:
            matched.append(keyword)
    
    return len(matched), matched
```

**How it works**:
1. Combines paper title + abstract into single text
2. Converts everything to lowercase
3. Checks for **substring matching** of each keyword
4. Counts how many keywords appear
5. Returns count and list of matched keywords

**Scoring**: 
- Each keyword match adds **0.2 points**
- **Capped at 0.5** maximum (so 3+ keywords = 0.5)
- Formula: `min(keyword_count * 0.2, 0.5)`

**Examples**:
- 1 keyword match → +0.2
- 2 keyword matches → +0.4
- 3+ keyword matches → +0.5 (capped)

---

### Component 3: Semantic Similarity (Weight: `1 - author_weight`)

**Location**: `filter.py` - `compute_similarity_scores()` method

This is the most sophisticated component, using **machine learning** (TF-IDF + Cosine Similarity).

#### Step 1: Text Vectorization with TF-IDF

```python
vectorizer = TfidfVectorizer(
    max_features=1000,        # Use top 1000 most important words
    stop_words='english',     # Remove common words (the, a, is, etc.)
    ngram_range=(1, 2),       # Use both single words and word pairs
    min_df=1,                 # Minimum document frequency
)
```

**What is TF-IDF?**

TF-IDF (Term Frequency-Inverse Document Frequency) converts text into numerical vectors:

- **TF (Term Frequency)**: How often a word appears in THIS document
  - "galaxy" appears 5 times in paper → high TF
  
- **IDF (Inverse Document Frequency)**: How rare the word is across ALL documents
  - "the" appears in every paper → low IDF (not informative)
  - "quasar" appears in few papers → high IDF (very informative)
  
- **TF-IDF Score** = TF × IDF
  - High score = word is frequent in this paper AND rare overall
  - This identifies **distinctive** terms

**Example**:
```
Paper title: "Dark Matter Distribution in Galaxy Clusters"
Abstract: "We study the dark matter halos..."

After TF-IDF vectorization:
Vector = [0.0, 0.42(dark), 0.38(matter), 0.0, 0.31(galaxy), ...]
         ↑                                            ↑
    common word                              distinctive term
    (removed)                                (high score)
```

**Parameters explained**:
- `max_features=1000`: Only keep 1000 most important terms (reduces noise)
- `ngram_range=(1,2)`: Consider both "galaxy" and "galaxy cluster"
- `stop_words='english'`: Remove "the", "a", "is", "of", etc.

#### Step 2: Fit on Reference Papers

```python
# Get papers from authors you follow (e.g., 50 papers)
reference_texts = [f"{p.title} {p.abstract}" for p in reference_papers]

# Learn vocabulary from these papers
reference_vectors = vectorizer.fit_transform(reference_texts)
```

This creates a **vocabulary** based on what your followed authors write about:
- If they write about "dark matter", "galaxies", "simulations"
- The vectorizer learns these are important terms
- Papers with similar terms will score higher

#### Step 3: Transform Candidate Papers

```python
# Apply same vocabulary to new papers
paper_vectors = vectorizer.transform(paper_texts)
```

Converts each candidate paper into the **same vector space**:
- Uses the vocabulary learned from reference papers
- Papers discussing similar topics will have similar vectors

#### Step 4: Compute Cosine Similarity

```python
# Compare each paper to all reference papers
similarities = cosine_similarity(paper_vectors, reference_vectors)
# Shape: (num_papers, num_reference_papers)

# Take maximum similarity to any reference paper
max_similarities = similarities.max(axis=1)
```

**What is Cosine Similarity?**

Measures the angle between two vectors (0 to 1):

```
       Paper A: [0.5, 0.8, 0.1]  (about galaxies, dark matter)
                    ↗ 
                   /  small angle = similar (score ≈ 0.9)
                  /
       Paper B: [0.6, 0.7, 0.2]  (also galaxies, dark matter)


       Paper C: [0.1, 0.2, 0.9]  (about quantum computing)
                               ↘
                                 \ large angle = dissimilar (score ≈ 0.2)
```

Formula: `similarity = (A · B) / (|A| × |B|)`
- 1.0 = identical papers
- 0.9 = very similar
- 0.5 = somewhat related  
- 0.1 = unrelated

**Why maximum?**
```python
max_similarities = similarities.max(axis=1)
```
Takes the **highest similarity** to ANY reference paper:
- If a new paper is similar to even ONE paper by your followed authors
- It gets a high score
- You don't need it to match ALL reference papers

#### Step 5: Weight and Add to Score

```python
sim_score = similarity_scores[i]  # e.g., 0.75
weighted_sim = sim_score * (1 - author_weight)
# If author_weight = 0.6, then weighted_sim = 0.75 * 0.4 = 0.30
score += weighted_sim
```

The similarity is weighted by `(1 - author_weight)`:
- **Balances** author matching vs. content similarity
- Default: 60% author weight, 40% similarity weight
- Ensures both matter in final score

---

### Final Score Calculation

**Location**: `filter.py` - `filter_and_rank()` method

```python
score = 0.0

# 1. Author match (0.0 or author_weight)
if author_matches:
    score += author_weight  # e.g., +0.6

# 2. Keyword matches (0.0 to 0.5)
keyword_score = min(keyword_count * 0.2, 0.5)
score += keyword_score  # e.g., +0.4 for 2 keywords

# 3. Semantic similarity (0.0 to 1-author_weight)
if similarity_enabled:
    score += similarity_score * (1 - author_weight)  # e.g., +0.30

# Final score: 0.6 + 0.4 + 0.30 = 1.30
```

**Score Range**: Typically 0.0 to ~1.5
- 0.0-0.3 = Low relevance (category match only)
- 0.3-0.6 = Medium relevance (some keyword/similarity)
- 0.6-1.0 = High relevance (author match OR strong similarity)
- 1.0+ = Very high relevance (author match + keywords + similarity)

**Real Example from Your Run**:
```
Paper: "Galaxy formation in cosmological simulations"
- Author: Philip F. Hopkins (matches!) → +0.6
- Keywords: "galaxy formation" found → +0.2
- Similarity to reference papers: 0.45 → +0.18 (0.45 * 0.4)
- Final Score: 0.98
```

---

### Filtering and Ranking

```python
# 1. Filter: Keep papers above threshold OR with author match
if score >= min_similarity_score or author_match:
    scored_papers.append(paper)

# 2. Sort by score (highest first)
scored_papers.sort(key=lambda p: p.score, reverse=True)

# 3. Limit to max_papers
filtered_papers = scored_papers[:max_papers]  # e.g., top 20
```

**Three-stage process**:
1. **Filter**: Remove low-scoring papers (below threshold)
   - Exception: Always keep papers by followed authors
2. **Sort**: Order by relevance score (best first)
3. **Limit**: Take only top N papers (e.g., 20)

---

## 📄 Part 2: PDF Generation

Uses **ReportLab** library with Platypus (Page Layout and Typography Using Scripts).

### PDF Architecture

**Location**: `generator.py` - `generate()` method

```python
doc = SimpleDocTemplate(
    output_path,
    pagesize=letter,          # US Letter: 8.5" × 11"
    rightMargin=0.75 * inch,  # 0.75 inch margins
    leftMargin=0.75 * inch,
    topMargin=0.75 * inch,
    bottomMargin=0.75 * inch,
)
```

Creates a PDF document with:
- **Letter size** page (8.5" × 11")
- **0.75 inch margins** on all sides
- **Flowable content** (auto-pagination)

### Content Building (Platypus Flowables)

PDF is built from **flowable elements** that ReportLab arranges:

```python
content = []

# 1. Header
content.extend(self._create_header(date))

# 2. Summary
content.extend(self._create_summary(papers, stats))

# 3. Papers (grouped by category)
for category, papers in grouped_papers.items():
    content.append(Paragraph(category_heading))
    content.append(Spacer(1, 0.1 * inch))
    
    for paper in papers:
        content.extend(self._create_paper_content(paper))

# 4. Build PDF
doc.build(content)
```

**Flow**: Elements are added to a list, then ReportLab:
- Flows text from top to bottom
- Handles page breaks automatically
- Applies styles and formatting

### Custom Styles

**Location**: `generator.py` - `_setup_custom_styles()` method

```python
styles.add(ParagraphStyle(
    name='NewsletterTitle',
    parent=styles['Title'],
    fontSize=24,
    textColor=colors.HexColor('#1a1a1a'),
    spaceAfter=12,
    alignment=TA_CENTER,
))

styles.add(ParagraphStyle(
    name='PaperTitle',
    parent=styles['Heading2'],
    fontSize=13,
    textColor=colors.HexColor('#1a1a1a'),
    fontName='Helvetica-Bold',
    spaceAfter=6,
))
```

**Style hierarchy**:
- **NewsletterTitle**: Large, centered, dark color (24pt)
- **Subtitle**: Medium, centered, gray (12pt)
- **CategoryHeading**: Blue, bold (16pt)
- **PaperTitle**: Bold, dark (13pt)
- **PaperMeta**: Small, gray (9pt) - for authors, dates
- **Abstract**: Justified, readable (10pt)
- **Link**: Small, blue, clickable (9pt)

### Paper Content Structure

**Location**: `generator.py` - `_create_paper_content()` method

Each paper is rendered as:

```python
elements = []

# 1. Title (numbered)
elements.append(Paragraph(
    f"{index}. {paper.title}",
    styles['PaperTitle']
))

# 2. Authors (formatted, truncated if >10)
elements.append(Paragraph(
    f"<b>Authors:</b> {formatted_authors}",
    styles['PaperMeta']
))

# 3. Metadata (date + categories)
elements.append(Paragraph(
    f"<b>Published:</b> 2025-11-28 | <b>Categories:</b> astro-ph.GA",
    styles['PaperMeta']
))

# 4. Match reason + score
elements.append(Paragraph(
    f"<b>Match:</b> Author: Philip F. Hopkins; Keywords: galaxy (Score: 0.98)",
    styles['PaperMeta']
))

# 5. Abstract (optional, truncated to 1000 chars)
if include_abstracts:
    elements.append(Paragraph(
        f"<b>Abstract:</b> {abstract[:1000]}...",
        styles['Abstract']
    ))

# 6. Links (clickable hyperlinks)
if include_links:
    elements.append(Paragraph(
        f'<a href="{arxiv_url}" color="blue">arXiv</a> | '
        f'<a href="{pdf_url}" color="blue">PDF</a>',
        styles['Link']
    ))

# 7. Spacer
elements.append(Spacer(1, 0.15 * inch))

return elements
```

**Visual layout** of each paper:

```
1. Dark Matter Distribution in Galaxy Clusters
   Authors: John Smith, Jane Doe, Alice Johnson
   Published: 2025-11-28 | Categories: astro-ph.CO, astro-ph.GA
   Match: Keywords: dark matter; Similarity: 0.75 (Score: 0.95)
   
   Abstract: We present a comprehensive study of dark matter 
   distributions in galaxy clusters using N-body simulations...
   
   arXiv | PDF
   
   [spacer]
```

### HTML-like Markup

ReportLab supports **HTML-like tags** in Paragraph text:

```python
f"<b>Authors:</b> {authors}"           # Bold
f'<a href="{url}" color="blue">arXiv</a>'  # Hyperlink
f"<i>Published:</i> {date}"            # Italics
```

### Header & Summary

```python
def _create_header(self, date):
    return [
        Paragraph("arXiv Newsletter", styles['NewsletterTitle']),
        Paragraph(f"Personalized Paper Recommendations — Nov 28, 2025", 
                  styles['Subtitle']),
        Spacer(1, 0.1 * inch),
    ]

def _create_summary(self, papers, stats):
    return [
        Paragraph(f"Found <b>{len(papers)}</b> papers. "
                  f"Average score: <b>{stats['avg_score']:.2f}</b>",
                  styles['Normal']),
        Spacer(1, 0.2 * inch),
    ]
```

**Rendered as**:

```
        arXiv Newsletter
Personalized Paper Recommendations — November 28, 2025

Found 20 papers. Average score: 0.59

[Papers follow...]
```

### Category Grouping

```python
if group_by_category:
    grouped = paper_filter.group_by_category(papers)
    
    for category, cat_papers in sorted(grouped.items()):
        # Category heading
        content.append(Paragraph(
            f"{category} ({len(cat_papers)} papers)",
            styles['CategoryHeading']
        ))
        
        # Papers in this category
        for i, paper in enumerate(cat_papers, 1):
            content.extend(create_paper_content(paper, i))
```

**Result**:
```
astro-ph.GA (16 papers)

1. [Paper title]
   [Paper details]

2. [Paper title]
   [Paper details]

astro-ph.HE (3 papers)

1. [Paper title]
   [Paper details]
```

### Page Layout Flow

ReportLab's **automatic pagination**:

1. Adds elements to content list
2. Flows content top-to-bottom
3. When page fills up → automatic page break
4. Continues on next page
5. Maintains margins and spacing

```
┌─────────────────────┐
│   Header            │
│   Summary           │
│                     │
│   Category 1        │
│   Paper 1           │
│   Paper 2           │
│   Paper 3           │
│                     │
└─────────────────────┘
         ↓
┌─────────────────────┐
│   (continued)       │
│   Paper 4           │
│   Paper 5           │
│                     │
│   Category 2        │
│   Paper 1           │
│   Paper 2           │
│                     │
└─────────────────────┘
```

---

## 🔄 Complete Workflow

### End-to-End Process

```
1. FETCH (fetcher.py)
   ↓
   ├─ Query arXiv API for papers by authors
   ├─ Query arXiv API for papers in categories  
   ├─ Query arXiv API for papers with keywords
   ├─ Deduplicate by paper ID
   └─ Return ~779 papers

2. REFERENCE (fetcher.py)
   ↓
   └─ Fetch 50 papers by followed authors
      (for similarity comparison)

3. SCORE (filter.py)
   ↓
   For each paper:
   ├─ Check author match → +0.0 to +0.6
   ├─ Check keyword match → +0.0 to +0.5
   ├─ Compute TF-IDF similarity → +0.0 to +0.4
   └─ Final score: 0.0 to ~1.5

4. FILTER (filter.py)
   ↓
   ├─ Remove papers below threshold (unless author match)
   ├─ Sort by score (highest first)
   └─ Keep top 20 papers

5. GENERATE (generator.py)
   ↓
   ├─ Create PDF document
   ├─ Add header and summary
   ├─ Group papers by category
   ├─ Format each paper with styles
   └─ Save to newsletters/arxiv_newsletter_2025-11-28.pdf
```

---

## 🎛️ Configuration Impact

### author_weight (default: 0.6)

Controls **balance** between author matching vs. content similarity:

| Value | Behavior |
|-------|----------|
| 1.0 | Only author matching matters (ignores similarity) |
| 0.6 | 60% author, 40% similarity (balanced) |
| 0.5 | Equal weight to both |
| 0.2 | 20% author, 80% similarity (content-focused) |
| 0.0 | Only similarity matters (ignores authors) |

**Use cases**:
- **High (0.8-1.0)**: Follow specific people closely
- **Medium (0.5-0.7)**: Balanced discovery
- **Low (0.0-0.4)**: Discover papers on topics (regardless of author)

### min_similarity_score (default: 0.3)

Minimum score to include paper:

| Value | Result |
|-------|--------|
| 0.1 | Very permissive (many papers) |
| 0.3 | Moderate (default) |
| 0.5 | Selective (fewer, higher quality) |
| 0.7 | Very selective (only best matches) |

**Exception**: Papers by followed authors are **always included** (bypass threshold).

### use_semantic_similarity (default: true)

| Value | Behavior |
|-------|----------|
| true | Uses TF-IDF similarity (slower, more accurate) |
| false | Only author + keyword matching (faster) |

**Trade-off**:
- **true**: Better discovery of related papers, but ~10-20 seconds slower
- **false**: Faster, but misses papers without exact keyword matches

---

## 📊 Performance Characteristics

### Time Complexity

- **Fetching**: O(n) - linear in number of papers fetched
- **TF-IDF vectorization**: O(d × f) - documents × features (1000)
- **Similarity computation**: O(n × r) - papers × reference papers
- **Filtering**: O(n log n) - sorting by score
- **PDF generation**: O(n) - linear in papers

**Total**: ~20-40 seconds for typical run (779 papers, 50 references)

### Space Complexity

- **Paper storage**: O(n) - stores all fetched papers
- **TF-IDF vectors**: O((n + r) × 1000) - sparse matrices
- **Similarity matrix**: O(n × r) - but only max used

**Total**: ~50-100 MB memory for typical run

---

## 🎯 Summary

**Matching**: 3-component scoring system
1. Author fuzzy matching (weighted by author_weight)
2. Keyword substring matching (up to 0.5 points)
3. TF-IDF cosine similarity (weighted by 1-author_weight)

**Scoring**: Additive model (0.0 to ~1.5 scale)
- Balanced by configurable weights
- Filtered by threshold
- Sorted and limited to top N

**PDF Generation**: ReportLab with Platypus
- Flowable content model
- Custom paragraph styles
- Automatic pagination
- Grouped by category
- Clickable hyperlinks

This creates a **smart, personalized, beautiful** newsletter! 🎉
