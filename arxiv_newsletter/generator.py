"""
PDF newsletter generator module.

Generates formatted PDF newsletters from filtered papers.
"""

from datetime import datetime
from typing import List
from html import escape
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY


def escape_preserve_latex(text: str) -> str:
    """
    Escape HTML special characters and format LaTeX math for better readability.
    
    Math expressions in $...$ (inline) or $$...$$ (display) are converted to
    italic text without the $ delimiters for cleaner appearance, while other 
    HTML special characters like <, >, &, etc. are escaped.
    
    Args:
        text: Input text possibly containing LaTeX math
        
    Returns:
        Text with HTML escaped and LaTeX math formatted in italics
    """
    if not text:
        return text
    
    # Find all math expressions and replace with placeholders
    math_expressions = []
    
    # Match display math $$...$$ first (to avoid confusion with inline)
    display_pattern = r'\$\$([^\$]+)\$\$'
    def replace_display(match):
        math_content = match.group(1)  # Get content without $$
        math_expressions.append(('display', math_content))
        return f"__MATH_PLACEHOLDER_{len(math_expressions)-1}__"
    text = re.sub(display_pattern, replace_display, text)
    
    # Match inline math $...$
    inline_pattern = r'\$([^\$]+)\$'
    def replace_inline(match):
        math_content = match.group(1)  # Get content without $
        math_expressions.append(('inline', math_content))
        return f"__MATH_PLACEHOLDER_{len(math_expressions)-1}__"
    text = re.sub(inline_pattern, replace_inline, text)
    
    # Escape HTML in the remaining text
    text = escape(text)
    
    # Restore math expressions with ReportLab formatting (italic, no $ signs)
    for i, (math_type, math_content) in enumerate(math_expressions):
        placeholder = f"__MATH_PLACEHOLDER_{i}__"
        # Escape the math content too (it may contain < > &)
        math_escaped = escape(math_content)
        # Format as italic without the $ delimiters
        formatted = f'<i>{math_escaped}</i>'
        text = text.replace(placeholder, formatted)
    
    return text


class NewsletterGenerator:
    """Generates PDF newsletters from papers."""
    
    def __init__(self, config):
        """
        Initialize generator with configuration.
        
        Args:
            config: Config object with output settings
        """
        self.config = config
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles for the newsletter."""
        
        # Choose style based on config
        if self.config.latex_style:
            self._setup_latex_styles()
        else:
            self._setup_default_styles()
    
    def _setup_default_styles(self):
        """Set up default (modern) styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='NewsletterTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER,
        ))
        
        # Category heading style
        self.styles.add(ParagraphStyle(
            name='CategoryHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=10,
            spaceBefore=20,
        ))
        
        # Paper title style
        self.styles.add(ParagraphStyle(
            name='PaperTitle',
            parent=self.styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=6,
            fontName='Helvetica-Bold',
        ))
        
        # Paper metadata style
        self.styles.add(ParagraphStyle(
            name='PaperMeta',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            spaceAfter=6,
        ))
        
        # Abstract style
        self.styles.add(ParagraphStyle(
            name='Abstract',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            alignment=TA_JUSTIFY,
        ))
        
        # Link style
        self.styles.add(ParagraphStyle(
            name='Link',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=15,
        ))
    
    def _setup_latex_styles(self):
        """Set up LaTeX-inspired academic styles."""
        # Title style - LaTeX article title
        self.styles.add(ParagraphStyle(
            name='NewsletterTitle',
            parent=self.styles['Title'],
            fontSize=18,
            fontName='Times-Bold',
            textColor=colors.black,
            spaceAfter=6,
            alignment=TA_CENTER,
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Times-Italic',
            textColor=colors.black,
            spaceAfter=24,
            alignment=TA_CENTER,
        ))
        
        # Category heading style - LaTeX section
        self.styles.add(ParagraphStyle(
            name='CategoryHeading',
            parent=self.styles['Heading1'],
            fontSize=14,
            fontName='Times-Bold',
            textColor=colors.black,
            spaceAfter=8,
            spaceBefore=16,
        ))
        
        # Paper title style - LaTeX subsection
        self.styles.add(ParagraphStyle(
            name='PaperTitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            fontName='Times-Bold',
            textColor=colors.black,
            spaceAfter=4,
        ))
        
        # Paper metadata style
        self.styles.add(ParagraphStyle(
            name='PaperMeta',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Times-Roman',
            textColor=colors.black,
            spaceAfter=4,
        ))
        
        # Abstract style - LaTeX body text
        self.styles.add(ParagraphStyle(
            name='Abstract',
            parent=self.styles['BodyText'],
            fontSize=10,
            fontName='Times-Roman',
            textColor=colors.black,
            spaceAfter=10,
            alignment=TA_JUSTIFY,
            leading=12,
        ))
        
        # Link style
        self.styles.add(ParagraphStyle(
            name='Link',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Times-Roman',
            textColor=colors.blue,
            spaceAfter=12,
        ))
    
    def _format_authors(self, authors: List[str], max_authors: int = 10) -> str:
        """
        Format author list for display.
        
        Args:
            authors: List of author names
            max_authors: Maximum number of authors to show
        
        Returns:
            Formatted author string
        """
        if len(authors) <= max_authors:
            return ", ".join(authors)
        else:
            shown = authors[:max_authors]
            remaining = len(authors) - max_authors
            return f"{', '.join(shown)}, ... (+{remaining} more)"
    
    def _create_paper_content(self, paper, index: int) -> List:
        """
        Create content elements for a single paper.
        
        Args:
            paper: Paper object
            index: Paper index number
        
        Returns:
            List of Platypus elements
        """
        elements = []
        
        # Paper number and title (escape HTML but preserve LaTeX)
        title_text = f"{index}. {escape_preserve_latex(paper.title)}"
        elements.append(Paragraph(title_text, self.styles['PaperTitle']))
        
        # Authors
        authors_text = self._format_authors(paper.authors)
        elements.append(Paragraph(f"<b>Authors:</b> {escape(authors_text)}", self.styles['PaperMeta']))
        
        # Publication date and categories
        pub_date = paper.published.strftime("%Y-%m-%d")
        categories = ", ".join(paper.categories)
        meta_text = f"<b>Published:</b> {pub_date} | <b>Categories:</b> {escape(categories)}"
        elements.append(Paragraph(meta_text, self.styles['PaperMeta']))
        
        # Match reason and score
        if paper.match_reason:
            reason_text = f"<b>Match:</b> {escape(paper.match_reason)} (Score: {paper.score:.2f})"
            elements.append(Paragraph(reason_text, self.styles['PaperMeta']))
        
        # Abstract
        if self.config.include_abstracts:
            abstract = paper.abstract
            # Truncate only if full_abstracts is False
            if not self.config.full_abstracts and len(abstract) > 1000:
                abstract = abstract[:1000] + "..."
            # Escape HTML but preserve LaTeX math expressions
            abstract_formatted = escape_preserve_latex(abstract)
            elements.append(Paragraph(f"<b>Abstract:</b> {abstract_formatted}", self.styles['Abstract']))
        
        # Links
        if self.config.include_links:
            links = [
                f'<a href="{paper.arxiv_url}" color="blue">arXiv</a>',
                f'<a href="{paper.pdf_url}" color="blue">PDF</a>',
            ]
            
            # Add ADS link if enabled
            if self.config.include_ads_links:
                links.append(f'<a href="{paper.ads_url}" color="blue">ADS</a>')
            
            link_text = " | ".join(links)
            elements.append(Paragraph(link_text, self.styles['Link']))
        
        # Spacer
        elements.append(Spacer(1, 0.15 * inch))
        
        return elements
    
    def _create_header(self, date: datetime = None) -> List:
        """
        Create newsletter header.
        
        Args:
            date: Newsletter date
        
        Returns:
            List of Platypus elements
        """
        if date is None:
            date = datetime.now()
        
        elements = []
        
        # Title
        elements.append(Paragraph("arXiv Newsletter", self.styles['NewsletterTitle']))
        
        # Subtitle with date
        subtitle = f"Personalized Paper Recommendations — {date.strftime('%B %d, %Y')}"
        elements.append(Paragraph(subtitle, self.styles['Subtitle']))
        
        # Separator line
        elements.append(Spacer(1, 0.1 * inch))
        
        return elements
    
    def _create_summary(self, papers: List, stats: dict) -> List:
        """
        Create summary section.
        
        Args:
            papers: List of papers
            stats: Statistics dictionary
        
        Returns:
            List of Platypus elements
        """
        elements = []
        
        summary_text = (
            f"Found <b>{len(papers)}</b> papers matching your interests. "
            f"Average relevance score: <b>{stats['avg_score']:.2f}</b>"
        )
        elements.append(Paragraph(summary_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def generate(self, papers: List, output_path: str, date: datetime = None) -> str:
        """
        Generate PDF newsletter.
        
        Args:
            papers: List of Paper objects to include
            date: Newsletter date (uses current date if None)
            output_path: Path to save PDF file
        
        Returns:
            Path to generated PDF file
        """
        if not papers:
            raise ValueError("No papers to include in newsletter")
        
        print(f"\nGenerating newsletter with {len(papers)} papers...")
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )
        
        # Build content
        content = []
        
        # Add header
        content.extend(self._create_header(date))
        
        # Add summary (compute stats)
        from .filter import PaperFilter
        paper_filter = PaperFilter(self.config)
        stats = paper_filter.get_statistics(papers)
        content.extend(self._create_summary(papers, stats))
        
        # Group papers by category if enabled
        if self.config.group_by_category:
            grouped_papers = paper_filter.group_by_category(papers)
            
            for category, cat_papers in sorted(grouped_papers.items()):
                # Category heading
                content.append(Paragraph(
                    f"{category} ({len(cat_papers)} papers)",
                    self.styles['CategoryHeading']
                ))
                content.append(Spacer(1, 0.1 * inch))
                
                # Sort papers within category by similarity score (highest first)
                cat_papers_sorted = sorted(cat_papers, key=lambda p: p.score, reverse=True)
                
                # Add papers in this category
                for i, paper in enumerate(cat_papers_sorted, 1):
                    paper_content = self._create_paper_content(paper, i)
                    # Keep paper content together when possible
                    content.extend(paper_content)
        else:
            # Add all papers without grouping (already sorted by score from filter_and_rank)
            for i, paper in enumerate(papers, 1):
                paper_content = self._create_paper_content(paper, i)
                content.extend(paper_content)
        
        # Build PDF
        doc.build(content)
        
        print(f"Newsletter saved to: {output_path}")
        return output_path
    
    def generate_html_preview(self, papers: List, date: datetime = None) -> str:
        """
        Generate HTML preview of newsletter (optional feature).
        
        Args:
            papers: List of Paper objects
            date: Newsletter date
        
        Returns:
            HTML string
        """
        if date is None:
            date = datetime.now()
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<meta charset="UTF-8">',
            '<title>arXiv Newsletter</title>',
            '<style>',
            'body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }',
            'h1 { color: #1a1a1a; text-align: center; }',
            'h2 { color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 5px; }',
            '.paper { margin-bottom: 30px; padding: 15px; background: #f9f9f9; border-left: 4px solid #2c5aa0; }',
            '.paper-title { font-size: 1.1em; font-weight: bold; margin-bottom: 10px; }',
            '.meta { color: #666; font-size: 0.9em; margin-bottom: 5px; }',
            '.abstract { text-align: justify; margin-top: 10px; }',
            '.links { margin-top: 10px; }',
            '.links a { margin-right: 15px; color: #2c5aa0; }',
            '</style>',
            '</head>',
            '<body>',
            f'<h1>arXiv Newsletter</h1>',
            f'<p style="text-align: center; color: #666;">Personalized Paper Recommendations — {date.strftime("%B %d, %Y")}</p>',
            f'<p><strong>{len(papers)}</strong> papers found</p>',
        ]
        
        for i, paper in enumerate(papers, 1):
            html_parts.extend([
                '<div class="paper">',
                f'<div class="paper-title">{i}. {paper.title}</div>',
                f'<div class="meta"><strong>Authors:</strong> {self._format_authors(paper.authors)}</div>',
                f'<div class="meta"><strong>Published:</strong> {paper.published.strftime("%Y-%m-%d")} | ',
                f'<strong>Categories:</strong> {", ".join(paper.categories)}</div>',
            ])
            
            if paper.match_reason:
                html_parts.append(f'<div class="meta"><strong>Match:</strong> {paper.match_reason} (Score: {paper.score:.2f})</div>')
            
            if self.config.include_abstracts:
                abstract = paper.abstract
                if not self.config.full_abstracts and len(abstract) > 1000:
                    abstract = abstract[:1000] + "..."
                html_parts.append(f'<div class="abstract"><strong>Abstract:</strong> {abstract}</div>')
            
            if self.config.include_links:
                links_html = [
                    f'<a href="{paper.arxiv_url}">arXiv</a>',
                    f'<a href="{paper.pdf_url}">PDF</a>',
                ]
                if self.config.include_ads_links:
                    links_html.append(f'<a href="{paper.ads_url}">ADS</a>')
                
                html_parts.append('<div class="links">')
                html_parts.extend(links_html)
                html_parts.append('</div>')
            
            html_parts.append('</div>')
        
        html_parts.extend([
            '</body>',
            '</html>',
        ])
        
        return '\n'.join(html_parts)
