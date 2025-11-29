"""
arXiv paper fetcher module.

Fetches papers from arXiv API based on authors, categories, and keywords.
"""

import arxiv
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser


class Paper:
    """Represents an arXiv paper with metadata."""
    
    def __init__(self, arxiv_result=None, from_dict=None):
        """
        Initialize from arxiv API result or dictionary.
        
        Args:
            arxiv_result: Result object from arxiv.Search (optional)
            from_dict: Dictionary with paper data (for cache loading)
        """
        if from_dict:
            # Load from cached dictionary
            self.id = from_dict["id"]
            self.title = from_dict["title"]
            self.authors = from_dict["authors"]
            self.abstract = from_dict["abstract"]
            self.categories = from_dict["categories"]
            self.primary_category = from_dict["primary_category"]
            self.published = datetime.fromisoformat(from_dict["published"]) if from_dict.get("published") else None
            self.updated = datetime.fromisoformat(from_dict["updated"]) if from_dict.get("updated") else None
            self.pdf_url = from_dict["pdf_url"]
            self.arxiv_url = from_dict["arxiv_url"]
            self.ads_url = from_dict.get("ads_url", f"https://ui.adsabs.harvard.edu/abs/arXiv:{self.id}")
            self.score = from_dict.get("score", 0.0)
            self.match_reason = from_dict.get("match_reason", "")
        elif arxiv_result:
            # Load from arXiv API result
            self.id = arxiv_result.entry_id.split("/")[-1]
            self.title = arxiv_result.title
            self.authors = [author.name for author in arxiv_result.authors]
            self.abstract = arxiv_result.summary
            self.categories = arxiv_result.categories
            self.primary_category = arxiv_result.primary_category
            self.published = arxiv_result.published
            self.updated = arxiv_result.updated
            self.pdf_url = arxiv_result.pdf_url
            self.arxiv_url = arxiv_result.entry_id
            
            # Generate ADS link
            # ADS uses arXiv ID format: arXiv:YYMM.NNNNN
            self.ads_url = f"https://ui.adsabs.harvard.edu/abs/arXiv:{self.id}"
            
            # These will be set by the filter
            self.score = 0.0
            self.match_reason = ""
        else:
            raise ValueError("Must provide either arxiv_result or from_dict")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "categories": self.categories,
            "primary_category": self.primary_category,
            "published": self.published.isoformat() if self.published else None,
            "updated": self.updated.isoformat() if self.updated else None,
            "pdf_url": self.pdf_url,
            "arxiv_url": self.arxiv_url,
            "score": self.score,
            "match_reason": self.match_reason,
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Paper(id={self.id}, title={self.title[:50]}...)"


class ArxivFetcher:
    """Fetches papers from arXiv API."""
    
    def __init__(self, config):
        """
        Initialize fetcher with configuration.
        
        Args:
            config: Config object with search parameters
        """
        self.config = config
        self.client = arxiv.Client()
    
    def fetch_papers_by_authors(self, days_back: Optional[int] = None) -> List[Paper]:
        """
        Fetch recent papers by specified authors.
        
        Args:
            days_back: Number of days to look back (uses config if None)
        
        Returns:
            List of Paper objects
        """
        if not self.config.authors:
            return []
        
        days = days_back or self.config.days_back
        papers = []
        
        print(f"Fetching papers by {len(self.config.authors)} authors...")
        
        for author in self.config.authors:
            # Build search query for author
            query = f'au:"{author}"'
            
            try:
                search = arxiv.Search(
                    query=query,
                    max_results=100,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                    sort_order=arxiv.SortOrder.Descending,
                )
                
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                
                for result in self.client.results(search):
                    # Check if paper is within date range
                    if result.published < cutoff_date:
                        break
                    
                    paper = Paper(result)
                    papers.append(paper)
                    
            except Exception as e:
                print(f"Error fetching papers for author '{author}': {e}")
        
        print(f"Found {len(papers)} papers by followed authors")
        return papers
    
    def fetch_papers_by_categories(self, days_back: Optional[int] = None) -> List[Paper]:
        """
        Fetch recent papers in specified categories.
        
        Args:
            days_back: Number of days to look back (uses config if None)
        
        Returns:
            List of Paper objects
        """
        if not self.config.categories:
            return []
        
        days = days_back or self.config.days_back
        papers = []
        
        print(f"Fetching papers from {len(self.config.categories)} categories...")
        
        for category in self.config.categories:
            # Build search query for category
            query = f'cat:{category}'
            
            try:
                search = arxiv.Search(
                    query=query,
                    max_results=200,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                    sort_order=arxiv.SortOrder.Descending,
                )
                
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                
                for result in self.client.results(search):
                    # Check if paper is within date range
                    if result.published < cutoff_date:
                        break
                    
                    paper = Paper(result)
                    papers.append(paper)
                    
            except Exception as e:
                print(f"Error fetching papers for category '{category}': {e}")
        
        print(f"Found {len(papers)} papers in specified categories")
        return papers
    
    def fetch_papers_by_keywords(self, days_back: Optional[int] = None) -> List[Paper]:
        """
        Fetch recent papers matching keywords.
        
        Args:
            days_back: Number of days to look back (uses config if None)
        
        Returns:
            List of Paper objects
        """
        if not self.config.keywords:
            return []
        
        days = days_back or self.config.days_back
        papers = []
        
        print(f"Fetching papers matching {len(self.config.keywords)} keywords...")
        
        # Build combined query with OR for keywords
        keyword_queries = []
        for keyword in self.config.keywords:
            keyword_queries.append(f'(ti:"{keyword}" OR abs:"{keyword}")')
        
        query = " OR ".join(keyword_queries)
        
        try:
            search = arxiv.Search(
                query=query,
                max_results=200,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            for result in self.client.results(search):
                # Check if paper is within date range
                if result.published < cutoff_date:
                    break
                
                paper = Paper(result)
                papers.append(paper)
                
        except Exception as e:
            print(f"Error fetching papers by keywords: {e}")
        
        print(f"Found {len(papers)} papers matching keywords")
        return papers
    
    def fetch_all_papers(self) -> List[Paper]:
        """
        Fetch all papers based on config (authors, categories, keywords).
        
        Returns:
            List of unique Paper objects
        """
        all_papers = []
        seen_ids = set()
        
        # Fetch by authors
        author_papers = self.fetch_papers_by_authors()
        for paper in author_papers:
            if paper.id not in seen_ids:
                all_papers.append(paper)
                seen_ids.add(paper.id)
        
        # Fetch by categories
        category_papers = self.fetch_papers_by_categories()
        for paper in category_papers:
            if paper.id not in seen_ids:
                all_papers.append(paper)
                seen_ids.add(paper.id)
        
        # Fetch by keywords
        keyword_papers = self.fetch_papers_by_keywords()
        for paper in keyword_papers:
            if paper.id not in seen_ids:
                all_papers.append(paper)
                seen_ids.add(paper.id)
        
        # Sort by publication date (newest first)
        all_papers.sort(key=lambda p: p.published, reverse=True)
        
        print(f"\nTotal unique papers found: {len(all_papers)}")
        return all_papers
    
    def fetch_reference_papers(self, limit: Optional[int] = None) -> List[Paper]:
        """
        Fetch reference papers from followed authors for similarity comparison.
        
        Args:
            limit: Maximum number of papers to fetch (uses config if None)
        
        Returns:
            List of Paper objects from followed authors
        """
        if not self.config.authors:
            return []
        
        max_papers = limit or self.config.reference_papers_limit
        papers = []
        
        print(f"Fetching reference papers from followed authors...")
        
        for author in self.config.authors:
            query = f'au:"{author}"'
            
            try:
                search = arxiv.Search(
                    query=query,
                    max_results=max_papers // len(self.config.authors) + 1,
                    sort_by=arxiv.SortCriterion.Relevance,
                )
                
                for result in self.client.results(search):
                    paper = Paper(result)
                    papers.append(paper)
                    
                    if len(papers) >= max_papers:
                        break
                        
            except Exception as e:
                print(f"Error fetching reference papers for '{author}': {e}")
            
            if len(papers) >= max_papers:
                break
        
        print(f"Fetched {len(papers)} reference papers")
        return papers
