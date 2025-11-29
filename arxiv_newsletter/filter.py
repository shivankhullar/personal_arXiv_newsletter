"""
Paper filtering and ranking module.

Filters and ranks papers based on author matching and content similarity.
"""

import re
from typing import List, Set, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class PaperFilter:
    """Filters and ranks papers based on relevance."""
    
    def __init__(self, config):
        """
        Initialize filter with configuration.
        
        Args:
            config: Config object with filtering parameters
        """
        self.config = config
        self.vectorizer = None
        self.reference_vectors = None
    
    def _normalize_author_name(self, name: str) -> str:
        """
        Normalize author name for comparison.
        
        Args:
            name: Author name
        
        Returns:
            Normalized name (lowercase, no punctuation)
        """
        # Remove punctuation and extra spaces
        name = re.sub(r'[^\w\s]', ' ', name.lower())
        name = re.sub(r'\s+', ' ', name).strip()
        return name
    
    def _author_matches(self, paper_authors: List[str], target_authors: List[str]) -> Tuple[bool, str]:
        """
        Check if any paper author matches target authors.
        
        Args:
            paper_authors: List of paper author names
            target_authors: List of target author names to match
        
        Returns:
            Tuple of (match_found, matched_author_name)
        """
        normalized_targets = {self._normalize_author_name(a) for a in target_authors}
        
        for author in paper_authors:
            normalized = self._normalize_author_name(author)
            
            # Check for exact match or substring match
            for target in normalized_targets:
                if target in normalized or normalized in target:
                    return True, author
        
        return False, ""
    
    def _keyword_matches(self, text: str, keywords: List[str]) -> Tuple[int, List[str]]:
        """
        Count keyword matches in text.
        
        Args:
            text: Text to search (title + abstract)
            keywords: List of keywords to search for
        
        Returns:
            Tuple of (match_count, list_of_matched_keywords)
        """
        text_lower = text.lower()
        matched = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)
        
        return len(matched), matched
    
    def _apply_exclusions(self, papers: List) -> List:
        """
        Apply exclusion criteria to filter out unwanted papers.
        
        Args:
            papers: List of Paper objects
        
        Returns:
            Filtered list of Paper objects
        """
        filtered = []
        excluded_count = {"max_authors": 0, "min_authors": 0, "keywords": 0, "categories": 0}
        
        for paper in papers:
            # Check max authors
            if self.config.max_authors > 0 and len(paper.authors) > self.config.max_authors:
                excluded_count["max_authors"] += 1
                continue
            
            # Check min authors
            if self.config.min_authors > 0 and len(paper.authors) < self.config.min_authors:
                excluded_count["min_authors"] += 1
                continue
            
            # Check exclude keywords
            if self.config.exclude_keywords:
                search_text = f"{paper.title} {paper.abstract}".lower()
                excluded = False
                for keyword in self.config.exclude_keywords:
                    if keyword.lower() in search_text:
                        excluded_count["keywords"] += 1
                        excluded = True
                        break
                if excluded:
                    continue
            
            # Check exclude categories
            if self.config.exclude_categories:
                excluded = False
                for category in paper.categories:
                    for exclude_cat in self.config.exclude_categories:
                        if category.startswith(exclude_cat):
                            excluded_count["categories"] += 1
                            excluded = True
                            break
                    if excluded:
                        break
                if excluded:
                    continue
            
            filtered.append(paper)
        
        # Print exclusion stats
        total_excluded = sum(excluded_count.values())
        if total_excluded > 0:
            print(f"Excluded {total_excluded} papers:")
            if excluded_count["max_authors"] > 0:
                print(f"  - {excluded_count['max_authors']} papers (too many authors)")
            if excluded_count["min_authors"] > 0:
                print(f"  - {excluded_count['min_authors']} papers (too few authors)")
            if excluded_count["keywords"] > 0:
                print(f"  - {excluded_count['keywords']} papers (excluded keywords)")
            if excluded_count["categories"] > 0:
                print(f"  - {excluded_count['categories']} papers (excluded categories)")
        
        return filtered
    
    def compute_similarity_scores(self, papers: List, reference_papers: List) -> np.ndarray:
        """
        Compute semantic similarity scores between papers and reference papers.
        
        Args:
            papers: List of Paper objects to score
            reference_papers: List of reference Paper objects (from followed authors)
        
        Returns:
            Array of similarity scores for each paper
        """
        if not reference_papers or not papers:
            return np.zeros(len(papers))
        
        print("Computing semantic similarity scores...")
        
        # Combine title and abstract for text representation
        def get_text(paper):
            return f"{paper.title} {paper.abstract}"
        
        reference_texts = [get_text(p) for p in reference_papers]
        paper_texts = [get_text(p) for p in papers]
        
        # Use TF-IDF vectorization
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
        )
        
        # Fit on reference papers and transform both
        try:
            self.reference_vectors = self.vectorizer.fit_transform(reference_texts)
            paper_vectors = self.vectorizer.transform(paper_texts)
            
            # Compute cosine similarity
            similarities = cosine_similarity(paper_vectors, self.reference_vectors)
            
            # Take max similarity to any reference paper
            max_similarities = similarities.max(axis=1)
            
            return max_similarities
            
        except Exception as e:
            print(f"Error computing similarities: {e}")
            return np.zeros(len(papers))
    
    def filter_and_rank(self, papers: List, reference_papers: List = None) -> List:
        """
        Filter and rank papers based on relevance.
        
        Args:
            papers: List of Paper objects to filter and rank
            reference_papers: Optional list of reference papers for similarity
        
        Returns:
            Filtered and ranked list of Paper objects
        """
        if not papers:
            return []
        
        print(f"\nFiltering and ranking {len(papers)} papers...")
        
        # Apply exclusion criteria first
        papers = self._apply_exclusions(papers)
        
        if not papers:
            print("No papers remain after applying exclusion criteria")
            return []
        
        print(f"{len(papers)} papers after exclusions")
        
        # Compute similarity scores if enabled
        similarity_scores = None
        if self.config.use_semantic_similarity and reference_papers:
            similarity_scores = self.compute_similarity_scores(papers, reference_papers)
        
        # Score each paper
        scored_papers = []
        
        for i, paper in enumerate(papers):
            score = 0.0
            reasons = []
            
            # Check for author match
            author_match, matched_author = self._author_matches(
                paper.authors, self.config.authors
            )
            if author_match:
                score += self.config.author_weight
                reasons.append(f"Author: {matched_author}")
            
            # Check for keyword matches
            search_text = f"{paper.title} {paper.abstract}"
            keyword_count, matched_keywords = self._keyword_matches(
                search_text, self.config.keywords
            )
            if keyword_count > 0:
                # Boost score based on number of keyword matches
                keyword_score = min(keyword_count * 0.2, 0.5)
                score += keyword_score
                reasons.append(f"Keywords: {', '.join(matched_keywords)}")
            
            # Add semantic similarity score
            if similarity_scores is not None:
                sim_score = similarity_scores[i]
                # Weight similarity by (1 - author_weight) to balance with author matching
                score += sim_score * (1 - self.config.author_weight)
                if sim_score > 0.3:
                    reasons.append(f"Similarity: {sim_score:.2f}")
            
            # Store score and reason
            paper.score = score
            paper.match_reason = "; ".join(reasons) if reasons else "Category match"
            
            # Apply selection based on mode
            if self.config.selection_mode == "threshold":
                # Threshold mode: only include if above threshold OR author match
                if score >= self.config.min_similarity_score or author_match:
                    scored_papers.append(paper)
            else:
                # Fill mode: include all papers (will limit by max_papers later)
                scored_papers.append(paper)
        
        # Sort by score (highest first)
        scored_papers.sort(key=lambda p: p.score, reverse=True)
        
        # Limit to max_papers
        filtered_papers = scored_papers[:self.config.max_papers]
        
        mode_str = self.config.selection_mode
        print(f"Selected {len(filtered_papers)} papers (mode: {mode_str}, threshold: {self.config.min_similarity_score})")
        
        return filtered_papers
    
    def group_by_category(self, papers: List) -> dict:
        """
        Group papers by their primary category.
        
        Args:
            papers: List of Paper objects
        
        Returns:
            Dictionary mapping category to list of papers
        """
        grouped = {}
        
        for paper in papers:
            category = paper.primary_category
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(paper)
        
        return grouped
    
    def get_statistics(self, papers: List) -> dict:
        """
        Get statistics about filtered papers.
        
        Args:
            papers: List of Paper objects
        
        Returns:
            Dictionary with statistics
        """
        if not papers:
            return {
                "total": 0,
                "avg_score": 0,
                "categories": {},
                "authors": {},
            }
        
        categories = {}
        authors = {}
        
        for paper in papers:
            # Count categories
            cat = paper.primary_category
            categories[cat] = categories.get(cat, 0) + 1
            
            # Count authors
            for author in paper.authors:
                if author in self.config.authors:
                    authors[author] = authors.get(author, 0) + 1
        
        return {
            "total": len(papers),
            "avg_score": np.mean([p.score for p in papers]),
            "categories": categories,
            "authors": authors,
        }
