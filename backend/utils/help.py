import re
from urllib.parse import urlparse

def clean_text(text: str) -> str:
    """Remove extra whitespace and weird characters."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_domain(url: str) -> str:
    """Robustly extract the domain name from a URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return ""