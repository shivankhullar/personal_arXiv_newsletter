"""
LaTeX-based PDF newsletter generator module.

Generates formatted PDF newsletters from filtered papers using LaTeX for proper math rendering.
"""

from datetime import datetime
from typing import List
import subprocess
import tempfile
import shutil
from pathlib import Path


class LaTeXNewsletterGenerator:
    """Generates PDF newsletters using LaTeX."""
    
    def __init__(self, config):
        """
        Initialize generator with configuration.
        
        Args:
            config: Config object with output settings
        """
        self.config = config
    
    def _escape_latex(self, text: str) -> str:
        """
        Escape special LaTeX characters except for math mode delimiters.
        
        Args:
            text: Input text
            
        Returns:
            Text with LaTeX special chars escaped, preserving math mode
        """
        if not text:
            return text
        
        # Ensure text is properly decoded and clean
        try:
            # Replace problematic Unicode characters
            text = text.encode('utf-8', errors='replace').decode('utf-8')
        except Exception:
            text = str(text)
        
        # Characters that need escaping in LaTeX (outside math mode)
        # We'll handle this more carefully to preserve math
        replacements = {
            '\\': r'\textbackslash{}',
            '&': r'\&',
            '%': r'\%',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
        }
        
        # Split text into math and non-math parts
        import re
        parts = []
        last_end = 0
        
        # Find all math expressions (both $ and $$)
        pattern = r'(\$\$[^\$]+\$\$|\$[^\$]+\$)'
        
        for match in re.finditer(pattern, text):
            # Add non-math part (escaped)
            non_math = text[last_end:match.start()]
            for char, repl in replacements.items():
                non_math = non_math.replace(char, repl)
            parts.append(non_math)
            
            # Add math part (not escaped)
            parts.append(match.group(0))
            last_end = match.end()
        
        # Add remaining non-math part
        non_math = text[last_end:]
        for char, repl in replacements.items():
            non_math = non_math.replace(char, repl)
        parts.append(non_math)
        
        return ''.join(parts)
    
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
            author_list = ", ".join(self._escape_latex(a) for a in authors)
        else:
            shown = [self._escape_latex(a) for a in authors[:max_authors]]
            remaining = len(authors) - max_authors
            author_list = f"{', '.join(shown)}, \\ldots\\ (+{remaining} more)"
        
        return author_list
    
    def _create_latex_document(self, papers: List, date: datetime = None) -> str:
        """
        Create LaTeX document content.
        
        Args:
            papers: List of Paper objects
            date: Newsletter date
            
        Returns:
            LaTeX document as string
        """
        if date is None:
            date = datetime.now()
        
        # Document preamble
        latex = [
            r'\documentclass[10pt,letterpaper]{article}',
            r'\usepackage[utf8]{inputenc}',
            r'\usepackage[T1]{fontenc}',
            r'\usepackage{lmodern}',
            r'\usepackage[margin=0.75in]{geometry}',
            r'\usepackage{hyperref}',
            r'\usepackage{amsmath}',
            r'\usepackage{amssymb}',
            r'\usepackage{graphicx}',
            r'\usepackage{parskip}',
            r'',
            r'% Hyperlink colors',
            r'\hypersetup{',
            r'    colorlinks=true,',
            r'    linkcolor=blue,',
            r'    urlcolor=blue,',
            r'    citecolor=blue',
            r'}',
            r'',
            r'\begin{document}',
            r'',
            r'% Title',
            r'\begin{center}',
            r'{\Huge\bfseries arXiv Newsletter}\\[0.3cm]',
            f'{{\\large Personalized Paper Recommendations --- {date.strftime("%B %d, %Y")}}}\\\\[0.5cm]',
            f'{{\\normalsize Found \\textbf{{{len(papers)}}} papers matching your interests}}',
            r'\end{center}',
            r'',
            r'\vspace{0.5cm}',
            r'',
        ]
        
        # Add papers
        for i, paper in enumerate(papers, 1):
            # Paper title
            title_escaped = self._escape_latex(paper.title)
            latex.append(f'\\subsection*{{{i}. {title_escaped}}}')
            latex.append('')
            
            # Authors
            authors_text = self._format_authors(paper.authors)
            latex.append(f'\\textbf{{Authors:}} {authors_text}')
            latex.append('')
            
            # Publication date and categories
            pub_date = paper.published.strftime("%Y-%m-%d")
            categories = ", ".join(self._escape_latex(c) for c in paper.categories)
            latex.append(f'\\textbf{{Published:}} {pub_date} | \\textbf{{Categories:}} {categories}')
            latex.append('')
            
            # Match reason and score
            if paper.match_reason:
                reason_escaped = self._escape_latex(paper.match_reason)
                latex.append(f'\\textbf{{Match:}} {reason_escaped} (Score: {paper.score:.2f})')
                latex.append('')
            
            # Abstract
            if self.config.include_abstracts:
                abstract = paper.abstract
                # Truncate only if full_abstracts is False
                if not self.config.full_abstracts and len(abstract) > 1000:
                    abstract = abstract[:1000] + "..."
                
                # Escape abstract but preserve math mode
                abstract_escaped = self._escape_latex(abstract)
                latex.append(f'\\textbf{{Abstract:}} {abstract_escaped}')
                latex.append('')
            
            # Links
            if self.config.include_links:
                links = [
                    f'\\href{{{paper.arxiv_url}}}{{arXiv}}',
                    f'\\href{{{paper.pdf_url}}}{{PDF}}',
                ]
                
                # Add ADS link if enabled
                if self.config.include_ads_links:
                    links.append(f'\\href{{{paper.ads_url}}}{{ADS}}')
                
                latex.append(' | '.join(links))
                latex.append('')
            
            # Separator
            latex.append(r'\vspace{0.3cm}')
            latex.append('')
        
        # Document end
        latex.append(r'\end{document}')
        
        return '\n'.join(latex)
    
    def generate(self, papers: List, output_path: str, date: datetime = None) -> str:
        """
        Generate PDF newsletter using LaTeX.
        
        Args:
            papers: List of Paper objects to include
            output_path: Path to save PDF file
            date: Newsletter date (uses current date if None)
        
        Returns:
            Path to generated PDF file
        """
        if not papers:
            raise ValueError("No papers to include in newsletter")
        
        print(f"\nGenerating LaTeX newsletter with {len(papers)} papers...")
        
        # Check if pdflatex is available
        if not shutil.which('pdflatex'):
            raise RuntimeError(
                "pdflatex not found. Please install a LaTeX distribution:\n"
                "  macOS: brew install --cask mactex-no-gui\n"
                "  Linux: sudo apt-get install texlive-latex-base texlive-latex-extra\n"
                "  Or use the ReportLab generator by setting latex_style=false in config"
            )
        
        # Create LaTeX document
        latex_content = self._create_latex_document(papers, date)
        
        # Create temporary directory for LaTeX compilation
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            tex_file = tmpdir_path / "newsletter.tex"
            
            # Write LaTeX file
            print("Writing LaTeX source...")
            with open(tex_file, 'w', encoding='utf-8', errors='replace') as f:
                f.write(latex_content)
            
            # Compile with pdflatex (run twice for proper references)
            print("Compiling with pdflatex (this may take a moment)...")
            for run in [1, 2]:
                try:
                    result = subprocess.run(
                        ['pdflatex', '-interaction=nonstopmode', 'newsletter.tex'],
                        cwd=tmpdir,
                        capture_output=True,
                        encoding='utf-8',
                        errors='replace',
                        timeout=60
                    )
                    
                    if result.returncode != 0 and run == 2:
                        # Only show error on second run
                        print(f"LaTeX compilation warnings/errors:")
                        print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
                        
                except subprocess.TimeoutExpired:
                    raise RuntimeError("LaTeX compilation timed out after 60 seconds")
            
            # Check if PDF was created
            pdf_file = tmpdir_path / "newsletter.pdf"
            if not pdf_file.exists():
                # Try to find the log file for more details
                log_file = tmpdir_path / "newsletter.log"
                if log_file.exists():
                    with open(log_file, 'r') as f:
                        log_content = f.read()
                    print("LaTeX log (last 1000 chars):")
                    print(log_content[-1000:])
                raise RuntimeError("LaTeX compilation failed to produce PDF")
            
            # Copy PDF to output location
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(pdf_file, output_path)
        
        print(f"Newsletter saved to: {output_path}")
        return output_path
