# Quick Start Guide

## Installation (< 2 minutes)

1. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

2. **Edit your config:**
   ```bash
   # Open config.yaml in your editor
   code config.yaml
   # or
   nano config.yaml
   ```

   **Minimal config example:**
   ```yaml
   authors:
     - "Your Favorite Researcher"
   
   categories:
     - "astro-ph.CO"
   
   keywords:
     - "dark matter"
   
   days_back: 7
   max_papers: 20
   ```

3. **Generate your first newsletter:**
   ```bash
   arxiv-newsletter
   ```

Done! Your newsletter is in `newsletters/arxiv_newsletter_YYYY-MM-DD.pdf`

## Tips for Your First Run

### For Astrophysics/Cosmology
```yaml
authors:
  - "Planck Collaboration"
  
categories:
  - "astro-ph.CO"  # Cosmology
  - "astro-ph.GA"  # Galaxies
  
keywords:
  - "dark matter"
  - "cosmic microwave background"
  - "large scale structure"
```

### For Machine Learning/AI
```yaml
authors:
  - "Yann LeCun"
  - "Yoshua Bengio"
  
categories:
  - "cs.LG"  # Machine Learning
  - "cs.AI"  # Artificial Intelligence
  - "stat.ML" # Statistics - Machine Learning
  
keywords:
  - "deep learning"
  - "neural networks"
  - "transformer"
```

### For High Energy Physics
```yaml
authors:
  - "ATLAS Collaboration"
  - "CMS Collaboration"
  
categories:
  - "hep-ex"   # High Energy Physics - Experiment
  - "hep-ph"   # High Energy Physics - Phenomenology
  
keywords:
  - "Higgs boson"
  - "supersymmetry"
  - "dark matter detection"
```

### For Quantum Computing
```yaml
authors:
  - "John Preskill"
  
categories:
  - "quant-ph"      # Quantum Physics
  - "cs.ET"         # Emerging Technologies
  
keywords:
  - "quantum computing"
  - "quantum error correction"
  - "quantum algorithms"
```

## Common Commands

```bash
# Generate newsletter
arxiv-newsletter

# Use more days
arxiv-newsletter --days 14

# Get fewer papers
arxiv-newsletter --max-papers 10

# Generate HTML instead of PDF
arxiv-newsletter --html

# Faster (no similarity computation)
arxiv-newsletter --no-similarity

# Verbose output
arxiv-newsletter -v

# Help
arxiv-newsletter --help
```

## Finding arXiv Categories

Visit: https://arxiv.org/category_taxonomy

**Popular categories:**
- `astro-ph.*` - Astrophysics (CO=Cosmology, GA=Galaxies, HE=High Energy)
- `cs.*` - Computer Science (AI, LG=Learning, CV=Computer Vision)
- `physics.*` - Physics (bio-ph=Biological, cond-mat=Condensed Matter)
- `math.*` - Mathematics (NA=Numerical Analysis, ST=Statistics Theory)
- `q-bio.*` - Quantitative Biology
- `quant-ph` - Quantum Physics
- `hep-*` - High Energy Physics (ex=Experiment, ph=Phenomenology, th=Theory)
- `gr-qc` - General Relativity and Quantum Cosmology

## Troubleshooting

**"No papers found"**
- Check your author names match arXiv format
- Try increasing `days_back` to 14 or 30
- Verify category codes at arXiv website

**"No papers passed threshold"**
- Lower `min_similarity_score` in config (try 0.1)
- Use `--no-similarity` flag
- Add more keywords

**Want more papers?**
- Increase `max_papers` in config
- Lower `min_similarity_score`
- Add more categories
- Increase `days_back`

**Want fewer/better papers?**
- Decrease `max_papers`
- Increase `min_similarity_score`
- Be more specific with keywords
- Add more authors to follow

## Automation

Run automatically every Monday at 9 AM:

```bash
# Add to crontab (crontab -e)
0 9 * * 1 cd /Users/skhullar/Docs/Projects/personal_arXiv_newsletter && ./venv/bin/arxiv-newsletter
```

## Next Steps

- Check out `example.py` for programmatic usage
- Read `DEVELOPMENT.md` if you want to customize
- Adjust `config.yaml` based on your first results
- Set up automation to get regular newsletters

Enjoy your personalized arXiv newsletters! 🎉
