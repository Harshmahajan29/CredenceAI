from typing import List, Dict
import asyncio
from app.models.schemas import Source

try:
    from crawl4ai import AsyncWebCrawler
except ImportError:
    AsyncWebCrawler = None

async def scrape_urls(urls: List[str]) -> List[Source]:
    sources = []
    if AsyncWebCrawler:
        async with AsyncWebCrawler(verbose=True) as crawler:
            for url in urls:
                try:
                    result = await crawler.arun(url=url)
                    if result.success:
                        sources.append(Source(
                            url=url,
                            domain=url.split("//")[-1].split("/")[0], # Very basic domain extraction
                            text_snippet=result.markdown
                        ))
                except Exception as e:
                    print(f"Error scraping {url}: {e}")
    else:
        import requests
        from bs4 import BeautifulSoup
        for url in urls:
            try:
                res = requests.get(url, timeout=5)
                soup = BeautifulSoup(res.text, "html.parser")
                sources.append(Source(
                    url=url,
                    domain=url.split("//")[-1].split("/")[0],
                    text_snippet=soup.get_text(separator=' ', strip=True)[:5000]
                ))
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                
    return sources