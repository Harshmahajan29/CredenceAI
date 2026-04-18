# backend/services/scraper.py
from typing import List, Dict, Optional
import asyncio
import os
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

try:
    import tldextract
except Exception:
    tldextract = None

try:
    from crawl4ai import AsyncWebCrawler
except Exception:
    AsyncWebCrawler = None

import httpx
from bs4 import BeautifulSoup

# Import your Pydantic Source model if available
# from app.models.schemas import Source  # uncomment if Source is a Pydantic model
# For portability, we return plain dicts that match Source fields

MAX_SNIPPET = int(os.getenv("SCRAPER_MAX_SNIPPET", "5000"))
SCRAPE_TIMEOUT = float(os.getenv("SCRAPE_TIMEOUT", "10.0"))
CONCURRENCY = int(os.getenv("SCRAPE_CONCURRENCY", "6"))

def _extract_domain(url: str) -> str:
    """Robust domain extraction using tldextract if available."""
    try:
        if tldextract:
            ext = tldextract.extract(url)
            if ext.domain:
                return f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain
        # fallback
        parsed = urlparse(url)
        host = parsed.hostname or ""
        # strip leading www.
        return host.removeprefix("www.")
    except Exception:
        return ""

async def _fetch_with_httpx(client: httpx.AsyncClient, url: str) -> Dict[str, Optional[str]]:
    try:
        r = await client.get(url, timeout=SCRAPE_TIMEOUT, follow_redirects=True)
        r.raise_for_status()
        text = r.text or ""
        # lightweight extraction
        soup = BeautifulSoup(text, "html.parser")
        # prefer article/body text
        article = soup.find("article")
        if article:
            body = article.get_text(separator=" ", strip=True)
        else:
            body = soup.get_text(separator=" ", strip=True)
        snippet = body[:MAX_SNIPPET]
        return {"url": url, "domain": _extract_domain(url), "text_snippet": snippet, "fetched_at": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        # log in real code
        return {"url": url, "domain": _extract_domain(url), "text_snippet": "", "fetched_at": None}

async def _fetch_with_crawl4ai(crawler, url: str) -> Dict[str, Optional[str]]:
    try:
        result = await crawler.arun(url=url)
        if getattr(result, "success", False):
            md = getattr(result, "markdown", "") or getattr(result, "text", "")
            snippet = md[:MAX_SNIPPET]
            return {"url": url, "domain": _extract_domain(url), "text_snippet": snippet, "fetched_at": datetime.now(timezone.utc).isoformat()}
        return {"url": url, "domain": _extract_domain(url), "text_snippet": "", "fetched_at": None}
    except Exception:
        return {"url": url, "domain": _extract_domain(url), "text_snippet": "", "fetched_at": None}

async def scrape_urls(urls: List[str]) -> List[Dict]:
    """
    Scrape a list of URLs and return a list of dicts matching your Source model:
    {url, domain, text_snippet, fetched_at}
    """
    results = []
    sem = asyncio.Semaphore(CONCURRENCY)

    async def guarded_fetch(fetch_coro):
        async with sem:
            return await fetch_coro

    if AsyncWebCrawler:
        # use crawl4ai
        async with AsyncWebCrawler(verbose=False) as crawler:
            tasks = [asyncio.create_task(guarded_fetch(_fetch_with_crawl4ai(crawler, u))) for u in urls]
            for coro in asyncio.as_completed(tasks):
                res = await coro
                results.append(res)
    else:
        # fallback to httpx + BeautifulSoup
        async with httpx.AsyncClient(headers={"User-Agent": "VerifierBot/1.0"}, verify=True) as client:
            tasks = [asyncio.create_task(guarded_fetch(_fetch_with_httpx(client, u))) for u in urls]
            for coro in asyncio.as_completed(tasks):
                res = await coro
                results.append(res)

    return results

def build_scraper_payload(claim_id: str, claim_text: str, scraped_sources: List[Dict], entities: Optional[List[str]] = None, context: Optional[Dict] = None) -> Dict:
    """
    Build the ScraperInput dict matching the Pydantic model used by the agent.
    """
    payload = {
        "claim_id": claim_id,
        "claim_text": claim_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "initial_urls": [],
        "entities": entities or [],
        "context": context or {},
        "source_meta": {"producer": "scraper_v2", "scrape_time": datetime.now(timezone.utc).isoformat()}
    }
    for s in scraped_sources:
        payload["initial_urls"].append({
            "url": s.get("url"),
            "domain": s.get("domain"),
            "snippet": s.get("text_snippet"),
            "fetched_at": s.get("fetched_at"),
            "metadata": {}
        })
    return payload

# Two helper submission methods: direct queue put (in-process) and HTTP POST (out-of-process)

async def submit_to_queue(app_queue, payload: Dict, timeout: float = 2.0) -> bool:
    """
    Put payload into an asyncio.Queue (app.state.agent_queue).
    Returns True if accepted.
    """
    try:
        await asyncio.wait_for(app_queue.put(payload), timeout=timeout)
        return True
    except asyncio.TimeoutError:
        return False

async def submit_via_http(ingest_url: str, payload: Dict, timeout: float = 5.0) -> Dict:
    """
    POST payload to the FastAPI ingest endpoint. Returns response JSON or raises.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(ingest_url, json=payload)
        r.raise_for_status()
        return r.json()

# Example high-level helper that scrapes and returns the payload
async def scrape_and_build(claim_id: str, claim_text: str, candidate_urls: List[str], entities: Optional[List[str]] = None, context: Optional[Dict] = None) -> Dict:
    scraped = await scrape_urls(candidate_urls)
    payload = build_scraper_payload(claim_id, claim_text, scraped, entities=entities, context=context)
    return payload

# Example usage (not executed at import)
# payload = asyncio.run(scrape_and_build("uuid-1", "Company X files for bankruptcy", ["https://reuters.com/..."]))
# asyncio.run(submit_via_http("http://localhost:8000/ingest/scraper", payload))
