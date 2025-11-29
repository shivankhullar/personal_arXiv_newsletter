#!/usr/bin/env python3
"""
Example script showing how to use the arXiv newsletter package programmatically.
"""

from datetime import datetime
from arxiv_newsletter import Config, ArxivFetcher, PaperFilter, NewsletterGenerator


def main():
    """Example of programmatic usage."""
    
    # Load configuration
    config = Config("config.yaml")
    
    # Or create config programmatically
    # config = Config()
    # config.config["authors"] = ["Albert Einstein", "Marie Curie"]
    # config.config["categories"] = ["physics.hist-ph"]
    # config.config["days_back"] = 14
    
    # Initialize components
    fetcher = ArxivFetcher(config)
    paper_filter = PaperFilter(config)
    generator = NewsletterGenerator(config)
    
    # Fetch papers
    print("Fetching papers...")
    all_papers = fetcher.fetch_all_papers()
    print(f"Found {len(all_papers)} papers")
    
    # Get reference papers for similarity
    reference_papers = []
    if config.use_semantic_similarity:
        print("Fetching reference papers...")
        reference_papers = fetcher.fetch_reference_papers()
    
    # Filter and rank
    print("Filtering and ranking...")
    filtered_papers = paper_filter.filter_and_rank(all_papers, reference_papers)
    print(f"Selected {len(filtered_papers)} papers")
    
    # Print top 5
    print("\nTop 5 papers:")
    for i, paper in enumerate(filtered_papers[:5], 1):
        print(f"{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}")
        print(f"   Score: {paper.score:.2f} - {paper.match_reason}")
        print()
    
    # Generate newsletter
    output_path = config.get_output_path()
    print(f"Generating newsletter: {output_path}")
    generator.generate(filtered_papers, output_path)
    
    # Generate HTML preview too
    html_path = output_path.replace('.pdf', '.html')
    html_content = generator.generate_html_preview(filtered_papers)
    with open(html_path, 'w') as f:
        f.write(html_content)
    print(f"HTML preview: {html_path}")
    
    # Get statistics
    stats = paper_filter.get_statistics(filtered_papers)
    print("\nStatistics:")
    print(f"  Total papers: {stats['total']}")
    print(f"  Average score: {stats['avg_score']:.2f}")
    print(f"  Categories: {len(stats['categories'])}")
    print(f"  Papers by followed authors: {sum(stats['authors'].values())}")


if __name__ == "__main__":
    main()
