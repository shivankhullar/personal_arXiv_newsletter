"""
Command-line interface for arXiv Newsletter.

Main entry point for generating personalized newsletters.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from .config import Config
from .fetcher import ArxivFetcher, Paper
from .filter import PaperFilter
from .generator import NewsletterGenerator
from .latex_generator import LaTeXNewsletterGenerator
from .cache import NewsletterCache


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate personalized arXiv newsletters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate newsletter with default config
  arxiv-newsletter
  
  # Use custom config file
  arxiv-newsletter --config my_config.yaml
  
  # Override days back to search
  arxiv-newsletter --days 14
  
  # Generate HTML preview instead of PDF
  arxiv-newsletter --html
  
  # Specify output path
  arxiv-newsletter --output my_newsletter.pdf
  
  # Cache management
  arxiv-newsletter --cache-info         # Show cache info
  arxiv-newsletter --clear-cache        # Clear all cached data
  arxiv-newsletter --no-cache           # Ignore cache, fetch fresh data
  
  # Quick PDF styling iterations (no API calls)
  arxiv-newsletter --pdf-only           # Regenerate PDF from cached data
        """
    )
    
    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Path to configuration YAML file (default: config.yaml)"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file path (overrides config setting)"
    )
    
    parser.add_argument(
        "-d", "--days",
        type=int,
        help="Number of days to look back for papers (overrides config)"
    )
    
    parser.add_argument(
        "--max-papers",
        type=int,
        help="Maximum number of papers to include (overrides config)"
    )
    
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML preview instead of PDF"
    )
    
    parser.add_argument(
        "--no-similarity",
        action="store_true",
        help="Disable semantic similarity computation (faster)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print verbose output"
    )
    
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Use cached data if available (default: True unless --no-cache specified)"
    )
    
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore cache and fetch fresh data"
    )
    
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear cache and exit"
    )
    
    parser.add_argument(
        "--cache-info",
        action="store_true",
        help="Show cache information and exit"
    )
    
    parser.add_argument(
        "--pdf-only",
        action="store_true",
        help="Only regenerate PDF from cached filtered papers (for styling iterations)"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize cache
        cache = NewsletterCache()
        
        # Handle cache commands
        if args.clear_cache:
            cache.clear()
            return 0
        
        if args.cache_info:
            info = cache.get_info()
            print("\nCache Information:")
            print(f"  Valid: {info['valid']}")
            if info.get('metadata'):
                meta = info['metadata']
                print(f"  Timestamp: {meta.get('timestamp', 'N/A')}")
                print(f"  Papers: {meta.get('paper_count', 'N/A')}")
                print(f"  Days back: {meta.get('days_back', 'N/A')}")
                print(f"  Config hash: {meta.get('config_hash', 'N/A')[:8]}...")
            if 'papers_size_kb' in info:
                print(f"  Papers cache: {info['papers_size_kb']:.1f} KB")
            if 'reference_size_kb' in info:
                print(f"  Reference cache: {info['reference_size_kb']:.1f} KB")
            if 'filtered_size_kb' in info:
                print(f"  Filtered cache: {info['filtered_size_kb']:.1f} KB")
            return 0
        
        # Load configuration
        print("Loading configuration...")
        config = Config(config_path=args.config)
        
        # Apply command-line overrides
        if args.days is not None:
            config.config["days_back"] = args.days
        
        if args.max_papers is not None:
            config.config["max_papers"] = args.max_papers
        
        if args.no_similarity:
            config.config["advanced"]["use_semantic_similarity"] = False
        
        # Print configuration summary
        print(f"\nConfiguration:")
        print(f"  Authors: {len(config.authors)}")
        print(f"  Categories: {len(config.categories)}")
        print(f"  Keywords: {len(config.keywords)}")
        print(f"  Days back: {config.days_back}")
        print(f"  Max papers: {config.max_papers}")
        print(f"  Use similarity: {config.use_semantic_similarity}")
        
        # Initialize components
        fetcher = ArxivFetcher(config)
        paper_filter = PaperFilter(config)
        
        # Choose generator based on latex_style setting
        if config.latex_style:
            generator = LaTeXNewsletterGenerator(config)
        else:
            generator = NewsletterGenerator(config)
        
        # Determine if we should use cache
        use_cache = not args.no_cache  # Default to True unless --no-cache specified
        
        # PDF-only mode: just regenerate PDF from cached filtered papers
        if args.pdf_only:
            print(f"\n{'='*60}")
            print("PDF-ONLY MODE: Loading filtered papers from cache")
            print('='*60)
            
            cached_filtered = cache.load_filtered_papers()
            if not cached_filtered:
                print("Error: No filtered papers in cache. Run without --pdf-only first.")
                return 1
            
            # Convert cached data back to Paper objects
            filtered_papers = [Paper(from_dict=p) for p in cached_filtered]
            print(f"Loaded {len(filtered_papers)} papers from cache")
            
            # Skip to PDF generation
            print(f"\n{'='*60}")
            print("Generating newsletter from cached data")
            print('='*60)
            
            if args.html:
                html_content = generator.generate_html_preview(filtered_papers)
                output_path = args.output or config.get_output_path().replace('.pdf', '.html')
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"HTML preview saved to: {output_path}")
            else:
                output_path = args.output or config.get_output_path()
                generator.generate(filtered_papers, output_path)
            
            return 0
        
        # Check cache validity
        cache_valid = use_cache and cache.is_valid(config, max_age_hours=24)
        
        # STEP 1: Fetch or load papers
        print(f"\n{'='*60}")
        print("STEP 1: Fetching papers from arXiv")
        print('='*60)
        
        if cache_valid:
            print("Loading papers from cache...")
            cached_papers = cache.load_papers()
            all_papers = [Paper(from_dict=p) for p in cached_papers]
        else:
            print("Fetching fresh papers from arXiv...")
            all_papers = fetcher.fetch_all_papers()
            
            if not all_papers:
                print("\nNo papers found matching your criteria.")
                print("Try adjusting your configuration (authors, categories, keywords, or days_back).")
                return 1
            
            # Save to cache
            cache.save_papers(all_papers, config)
        
        # STEP 2: Fetch or load reference papers
        reference_papers = []
        if config.use_semantic_similarity and config.authors:
            print(f"\n{'='*60}")
            print("STEP 2: Fetching reference papers for similarity comparison")
            print('='*60)
            
            if cache_valid:
                print("Loading reference papers from cache...")
                cached_ref = cache.load_reference_papers()
                if cached_ref:
                    reference_papers = [Paper(from_dict=p) for p in cached_ref]
                else:
                    print("No cached reference papers, fetching...")
                    reference_papers = fetcher.fetch_reference_papers()
                    cache.save_reference_papers(reference_papers)
            else:
                print("Fetching reference papers...")
                reference_papers = fetcher.fetch_reference_papers()
                cache.save_reference_papers(reference_papers)
        
        # STEP 3: Filter and rank papers
        print(f"\n{'='*60}")
        print("STEP 3: Filtering and ranking papers")
        print('='*60)
        
        filtered_papers = paper_filter.filter_and_rank(all_papers, reference_papers)
        
        if not filtered_papers:
            print("\nNo papers passed the relevance threshold.")
            print("Try lowering min_similarity_score in your config.")
            return 1
        
        # Save filtered papers to cache
        cache.save_filtered_papers(filtered_papers)
        
        # Print top papers
        if args.verbose:
            print(f"\nTop {min(5, len(filtered_papers))} papers:")
            for i, paper in enumerate(filtered_papers[:5], 1):
                print(f"\n{i}. {paper.title}")
                print(f"   Score: {paper.score:.2f} | {paper.match_reason}")
        
        # Generate newsletter
        print(f"\n{'='*60}")
        print("STEP 4: Generating newsletter")
        print('='*60)
        
        if args.html:
            # Generate HTML preview
            html_content = generator.generate_html_preview(filtered_papers)
            output_path = args.output or config.get_output_path().replace('.pdf', '.html')
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"HTML preview saved to: {output_path}")
        else:
            # Generate PDF
            output_path = args.output or config.get_output_path()
            generator.generate(filtered_papers, output_path)
        
        # Print statistics
        stats = paper_filter.get_statistics(filtered_papers)
        print(f"\n{'='*60}")
        print("Statistics")
        print('='*60)
        print(f"Total papers included: {stats['total']}")
        print(f"Average relevance score: {stats['avg_score']:.2f}")
        
        if stats['categories']:
            print(f"\nPapers by category:")
            for cat, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {cat}: {count}")
        
        if stats['authors']:
            print(f"\nPapers by followed authors:")
            for author, count in sorted(stats['authors'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {author}: {count}")
        
        print(f"\n{'='*60}")
        print("✓ Newsletter generated successfully!")
        print('='*60)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        return 130
    
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
