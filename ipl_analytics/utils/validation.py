"""
Input Validation and HTML Sanitization Utilities
"""

from typing import str
import re

try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False


def sanitize_html(content: str) -> str:
    """
    Sanitize raw HTML input using bleach to prevent XSS attacks while allowing safe tags.
    """
    if not content:
        return ""
        
    if BLEACH_AVAILABLE:
        allowed_tags = [
            'b', 'i', 'strong', 'em', 'p', 'br', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'thead', 'tbody', 'style', 'code', 'pre'
        ]
        allowed_attributes = {
            '*': ['class', 'style', 'id'],
            'a': ['href', 'title', 'target'],
        }
        return bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes)
    else:
        # Basic regex sanitization fallback if bleach is missing
        clean = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r'on\w+="[^"]*"', '', clean, flags=re.IGNORECASE)
        return clean
