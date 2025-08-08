"""HTML preprocessing tool for document preprocessing."""

import re
import logging
from typing import List, Optional
from dataclasses import dataclass

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
    logging.warning("BeautifulSoup not available, HTML cleaning will be limited")

logger = logging.getLogger(__name__)


@dataclass
class PreprocessingConfig:
    """HTML preprocessing configuration."""
    
    # Basic cleaning options
    remove_html_tags: bool = True
    remove_scripts: bool = True
    remove_styles: bool = True
    remove_comments: bool = True
    
    # Content extraction options
    preserve_links: bool = False
    preserve_images: bool = False
    preserve_tables: bool = False
    preserve_lists: bool = True
    
    # Text formatting options
    normalize_whitespace: bool = True
    convert_entities: bool = True
    preserve_line_breaks: bool = False
    
    # Advanced options
    remove_empty_paragraphs: bool = True
    minimum_text_length: int = 10


class HTMLPreprocessor:
    """HTML preprocessing tool for cleaning and extracting text from HTML documents."""
    
    def __init__(self, config: Optional[PreprocessingConfig] = None):
        """Initialize the HTML preprocessor with configuration."""
        self.config = config or PreprocessingConfig()
        
        # HTML entity mappings for common entities
        self.html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&apos;': "'",
            '&nbsp;': ' ',
            '&ndash;': '–',
            '&mdash;': '—',
            '&hellip;': '…',
            '&copy;': '©',
            '&reg;': '®',
            '&trade;': '™'
        }
    
    def preprocess(self, html_content: str) -> str:
        """
        Preprocess HTML content according to configuration.
        
        Args:
            html_content: Raw HTML content to preprocess
            
        Returns:
            Cleaned and processed text content
        """
        if not html_content or not html_content.strip():
            return ""
        
        try:
            text = html_content
            
            # Remove unwanted elements first
            if self.config.remove_scripts:
                text = self._remove_scripts(text)
            
            if self.config.remove_styles:
                text = self._remove_styles(text)
            
            if self.config.remove_comments:
                text = self._remove_comments(text)
            
            # Extract and preserve specific elements if requested
            if self.config.preserve_links:
                text = self._preserve_links(text)
            
            if self.config.preserve_images:
                text = self._preserve_images(text)
            
            if self.config.preserve_tables:
                text = self._preserve_tables(text)
            
            if self.config.preserve_lists:
                text = self._preserve_lists(text)
            
            # Remove remaining HTML tags
            if self.config.remove_html_tags:
                text = self._remove_html_tags(text)
            
            # Convert HTML entities
            if self.config.convert_entities:
                text = self._convert_html_entities(text)
            
            # Normalize text
            if self.config.normalize_whitespace:
                text = self._normalize_whitespace(text)
            
            if self.config.remove_empty_paragraphs:
                text = self._remove_empty_paragraphs(text)
            
            # Final cleanup
            text = text.strip()
            
            # Check minimum length requirement
            if len(text) < self.config.minimum_text_length:
                return ""
            
            return text
            
        except Exception as e:
            logger.warning(f"HTML preprocessing failed, using original text: {e}")
            return html_content
    
    def preprocess_batch(self, html_contents: List[str]) -> List[str]:
        """
        Preprocess multiple HTML contents.
        
        Args:
            html_contents: List of HTML content strings
            
        Returns:
            List of processed text contents
        """
        return [self.preprocess(html) for html in html_contents]
    
    def _remove_scripts(self, text: str) -> str:
        """Remove script tags and their content."""
        return re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    def _remove_styles(self, text: str) -> str:
        """Remove style tags and their content."""
        return re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    def _remove_comments(self, text: str) -> str:
        """Remove HTML comments."""
        return re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    def _preserve_links(self, text: str) -> str:
        """Convert links to readable format: [text](url)."""
        pattern = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
        
        def replace_link(match):
            url = match.group(1)
            link_text = self._clean_inner_html(match.group(2))
            if link_text.strip():
                return f"[{link_text}]({url})"
            else:
                return f"[{url}]({url})"
        
        return re.sub(pattern, replace_link, text, flags=re.DOTALL | re.IGNORECASE)
    
    def _preserve_images(self, text: str) -> str:
        """Convert images to readable format: ![alt](src)."""
        pattern = r'<img[^>]*src=["\']([^"\']+)["\'][^>]*(?:alt=["\']([^"\']*)["\'][^>]*)?/?>'
        
        def replace_image(match):
            src = match.group(1)
            alt = match.group(2) or "image"
            return f"![{alt}]({src})"
        
        return re.sub(pattern, replace_image, text, flags=re.IGNORECASE)
    
    def _preserve_tables(self, text: str) -> str:
        """Convert tables to a readable format."""
        # This is a simplified table conversion
        text = re.sub(r'</?table[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</?tr[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</?th[^>]*>', ' | ', text, flags=re.IGNORECASE)
        text = re.sub(r'</?td[^>]*>', ' | ', text, flags=re.IGNORECASE)
        return text
    
    def _preserve_lists(self, text: str) -> str:
        """Convert lists to readable format."""
        # Convert unordered list items
        text = re.sub(r'<li[^>]*>(.*?)</li>', r'• \1\n', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove list container tags
        text = re.sub(r'</?[uo]l[^>]*>', '\n', text, flags=re.IGNORECASE)
        
        return text
    
    def _remove_html_tags(self, text: str) -> str:
        """Remove all remaining HTML tags."""
        try:
            if BeautifulSoup is not None:
                # HTML 태그 제거
                soup = BeautifulSoup(text, 'html.parser')
                cleaned_text = soup.get_text(separator=' ', strip=True)
                return cleaned_text
            else:
                # BeautifulSoup 없이 기본적인 HTML 태그 제거
                return re.sub(r'<[^>]+>', ' ', text)
        except Exception as e:
            logger.warning(f"HTML tag removal failed: {e}")
            return re.sub(r'<[^>]+>', ' ', text)
    
    def _convert_html_entities(self, text: str) -> str:
        """Convert HTML entities to their corresponding characters."""
        # Use predefined entity mappings from scoring.py style
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&#39;', "'")
        text = text.replace('&quot;', '"')
        
        # Additional entities
        for entity, char in self.html_entities.items():
            text = text.replace(entity, char)
        
        # Handle numeric entities
        try:
            text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
            text = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), text)
        except Exception as e:
            logger.warning(f"Numeric entity conversion failed: {e}")
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text."""
        # 연속된 공백을 하나로 줄이기 (scoring.py 스타일)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _remove_empty_paragraphs(self, text: str) -> str:
        """Remove empty paragraphs and lines."""
        lines = text.split('\n')
        non_empty_lines = []
        
        for line in lines:
            if line.strip():
                non_empty_lines.append(line)
            elif non_empty_lines and non_empty_lines[-1] != '':
                non_empty_lines.append('')
        
        # Remove trailing empty line
        if non_empty_lines and non_empty_lines[-1] == '':
            non_empty_lines.pop()
        
        return '\n'.join(non_empty_lines)
    
    def _clean_inner_html(self, html: str) -> str:
        """Clean HTML from inner content while preserving text."""
        text = re.sub(r'<[^>]+>', '', html)
        return self._convert_html_entities(text).strip()


def clean_html_text(text: str) -> str:
    """Clean HTML tags and normalize text content (compatible with scoring.py)."""
    if not text:
        return ""
    
    try:
        if BeautifulSoup is not None:
            # HTML 태그 제거
            soup = BeautifulSoup(text, 'html.parser')
            cleaned_text = soup.get_text(separator=' ', strip=True)
        else:
            # BeautifulSoup 없이 기본적인 HTML 태그 제거
            cleaned_text = re.sub(r'<[^>]+>', ' ', text)
        
        # 연속된 공백을 하나로 줄이기
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        # 특수 HTML 엔티티 정규화
        cleaned_text = cleaned_text.replace('&nbsp;', ' ')
        cleaned_text = cleaned_text.replace('&lt;', '<')
        cleaned_text = cleaned_text.replace('&gt;', '>')
        cleaned_text = cleaned_text.replace('&amp;', '&')
        cleaned_text = cleaned_text.replace('&#39;', "'")
        cleaned_text = cleaned_text.replace('&quot;', '"')
        
        return cleaned_text.strip()
    except Exception as e:
        logger.warning(f"HTML cleaning failed, using original text: {e}")
        return text


# Convenience functions for common use cases
def clean_html(html_content: str, preserve_structure: bool = False) -> str:
    """
    Clean HTML content with default settings.
    
    Args:
        html_content: Raw HTML content
        preserve_structure: Whether to preserve some structural elements
        
    Returns:
        Cleaned text content
    """
    config = PreprocessingConfig(
        preserve_links=preserve_structure,
        preserve_lists=True,
        preserve_tables=preserve_structure
    )
    
    preprocessor = HTMLPreprocessor(config)
    return preprocessor.preprocess(html_content)


def extract_text_only(html_content: str) -> str:
    """
    Extract only text content from HTML, removing all formatting.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        Plain text content
    """
    config = PreprocessingConfig(
        preserve_links=False,
        preserve_images=False,
        preserve_tables=False,
        preserve_lists=False
    )
    
    preprocessor = HTMLPreprocessor(config)
    return preprocessor.preprocess(html_content)


def preprocess_for_chunking(html_content: str, min_length: int = 50) -> str:
    """
    Preprocess HTML for text chunking applications.
    
    Args:
        html_content: Raw HTML content
        min_length: Minimum text length to keep
        
    Returns:
        Preprocessed text suitable for chunking
    """
    config = PreprocessingConfig(
        preserve_links=False,
        preserve_images=False,
        preserve_tables=True,
        preserve_lists=True,
        normalize_whitespace=True,
        minimum_text_length=min_length
    )
    
    preprocessor = HTMLPreprocessor(config)
    return preprocessor.preprocess(html_content)