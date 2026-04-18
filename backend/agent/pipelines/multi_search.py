"""
verification_agent/pipelines/multi_search.py
=============================================
Pipeline 1 — Zero-trust multi-source frequency analysis.

Steps
-----
1. Generate up to 6 paraphrase queries from claim_text.
2. Run searches via configured backend (DuckDuckGo by default).
3. Fetch page content via crawl4ai or httpx fallback.
4. Compute semantic similarity against claim_text.
5. Cluster near-duplicates by embedding distance.
6. Return independent cluster list + evidence units.

PLACEHOLDERS in this file
--------------------------
  - Search backend credentials (see config/settings.py)
  - Paraphrase model: uses simple heuristic by default;
    swap _generate_paraphrases() for an LLM call if desired.
  - Crawl4ai fetch: requires `pip install crawl4ai` and Playwright
"""

from __future__ import annotations
import asyncio
import hashlib
import re
import uuid
from datetime import datetime
from urllib.parse import urlparse

from config.settings import AgentSettings
from utils.schema    import ClaimInput
from utils.embeddings import get_embeddings, cosine_similarity
from utils.logger    import get_logger

logger = get_logger(__name__)


async def run_multi_search(
    claim: ClaimInput,
    settings: AgentSettings,
    retry: int = 0,
) -> dict:
    """
    Returns:
        {
          "evidence_units": [...],
          "searches_performed": int,
          "independent_clusters": int,
          "propagation_velocity": float,
        }
    """
    queries = _generate_paraphrases(claim.claim_text, n=settings.max_searches, retry=retry)
    logger.info("MultiSearch: generated %d queries for claim_id=%s", len(queries), claim.claim_id)

    # Run searches
    search_results: list[dict] = []
    for q in queries:
        hits = await _search(q, settings)
        search_results.extend(hits)

    # Deduplicate by URL
    seen_urls: set[str] = {u.url for u in claim.initial_urls}
    unique_results = []
    for r in search_results:
        if r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            unique_results.append(r)

    # Fetch page content
    fetched = await _fetch_pages(unique_results[:20], settings)  # cap at 20 pages

    # Compute similarities
    if fetched:
        snippets  = [p["text"][:1000] for p in fetched]
        all_texts = [claim.claim_text] + snippets
        try:
            embeddings = get_embeddings(all_texts, settings)
            claim_vec  = embeddings[0]
            page_vecs  = embeddings[1:]
        except Exception as exc:
            logger.warning("Embedding failed: %s; using token overlap", exc)
            claim_vec = None
            page_vecs = [None] * len(fetched)
    else:
        fetched, claim_vec, page_vecs = [], None, []

    # Build raw evidence units
    raw_units = []
    for i, page in enumerate(fetched):
        vec = page_vecs[i] if i < len(page_vecs) else None
        if claim_vec is not None and vec is not None:
            sim = cosine_similarity(claim_vec, vec)
        else:
            sim = _token_overlap(claim.claim_text, page["text"])

        lr = _sim_to_lr(sim, settings)
        raw_units.append({
            "id":                 str(uuid.uuid4()),
            "type":               "support" if sim > 0.5 else "noise",
            "domain":             page.get("domain", ""),
            "url":                page["url"],
            "timestamp":          page.get("published_at"),
            "similarity":         round(sim, 4),
            "lr":                 lr,
            "independence_weight": 1.0,
            "cluster_id":         None,
            "provenance":         "multi_search",
            "raw_snippet":        page["text"][:500],
        })

    # Cluster near-duplicates
    units_with_clusters = _cluster_units(raw_units, claim_vec, fetched, settings)

    # Propagation velocity: how many sources published within 6h of claim timestamp
    velocity = _estimate_velocity(units_with_clusters, claim.timestamp)

    independent_clusters = len({u["cluster_id"] for u in units_with_clusters if u["cluster_id"]})

    return {
        "evidence_units":      units_with_clusters,
        "searches_performed":  len(queries),
        "independent_clusters": independent_clusters,
        "propagation_velocity": velocity,
    }


# ── Query generation ──────────────────────────────────────────────────────────

def _generate_paraphrases(claim_text: str, n: int = 6, retry: int = 0) -> list[str]:
    """
    Simple heuristic paraphraser. For production, replace this with an LLM
    call (e.g. OpenAI chat completion asking for N paraphrases).  # ← PLACEHOLDER
    """
    base = claim_text.strip()
    queries = [base]

    # Entity extraction heuristic: capitalised words
    entities = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', base)
    if entities:
        queries.append(" ".join(entities[:4]))

    # Remove filler words
    stopwords = {"the","a","an","is","are","was","were","has","have","that","this","in","of","to","and"}
    tokens = [t for t in base.lower().split() if t not in stopwords]
    queries.append(" ".join(tokens[:8]))

    # Key noun phrases (very rough)
    queries.append(base[:60] + " verified")
    queries.append(base[:60] + " fact check")

    if retry > 0:
        # Expand with negation check and date window
        queries.append(f"{base[:50]} debunked OR confirmed")
        queries.append(f"{base[:50]} latest news")

    return list(dict.fromkeys(queries))[:n]  # dedup, cap at n


# ── Search backends ───────────────────────────────────────────────────────────

async def _search(query: str, settings: AgentSettings) -> list[dict]:
    backend = settings.search_backend
    try:
        if backend == "duckduckgo":
            return await _ddg_search(query)
        elif backend == "serper":
            return await _serper_search(query, settings.serper_api_key)
        else:
            logger.warning("Unknown search backend %r; falling back to DuckDuckGo", backend)
            return await _ddg_search(query)
    except Exception as exc:
        logger.warning("Search failed for query %r: %s", query, exc)
        return []


async def _ddg_search(query: str) -> list[dict]:
    """DuckDuckGo search via duckduckgo_search library."""
    try:
        from duckduckgo_search import DDGS       # pip install duckduckgo-search
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=10):
                results.append({
                    "url":    r.get("href", ""),
                    "domain": urlparse(r.get("href", "")).netloc,
                    "title":  r.get("title", ""),
                    "snippet": r.get("body", ""),
                })
        return results
    except ImportError:
        logger.warning("duckduckgo-search not installed; returning empty results")
        return []


async def _serper_search(query: str, api_key: str) -> list[dict]:
    """Serper.dev Google search proxy.  # ← PLACEHOLDER: requires SERPER_API_KEY"""
    import httpx
    if api_key.startswith("YOUR_"):
        logger.warning("Serper API key not set")
        return []
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": 10},
        )
        data = resp.json()
    return [
        {
            "url":    r.get("link", ""),
            "domain": urlparse(r.get("link", "")).netloc,
            "title":  r.get("title", ""),
            "snippet": r.get("snippet", ""),
        }
        for r in data.get("organic", [])
    ]


# ── Page fetching ─────────────────────────────────────────────────────────────

async def _fetch_pages(results: list[dict], settings: AgentSettings) -> list[dict]:
    tasks = [_fetch_one(r, settings) for r in results]
    fetched = await asyncio.gather(*tasks, return_exceptions=True)
    return [f for f in fetched if isinstance(f, dict) and f.get("text")]


async def _fetch_one(result: dict, settings: AgentSettings) -> dict | None:
    url = result.get("url", "")
    if not url:
        return None

    # Try crawl4ai first
    try:
        from crawl4ai import AsyncWebCrawler          # pip install crawl4ai
        async with AsyncWebCrawler(headless=settings.crawl4ai_headless) as crawler:
            r = await crawler.arun(url=url, bypass_cache=True,
                                   timeout=settings.crawl4ai_timeout)
            text = r.markdown or r.cleaned_html or ""
            return {**result, "text": text[:3000], "published_at": None}
    except ImportError:
        pass
    except Exception as exc:
        logger.debug("crawl4ai failed for %s: %s", url, exc)

    # Fallback: plain httpx GET
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            text = resp.text[:3000]
            return {**result, "text": text, "published_at": None}
    except Exception as exc:
        logger.debug("httpx fetch failed for %s: %s", url, exc)
        # Fall back to snippet only
        return {**result, "text": result.get("snippet", ""), "published_at": None}


# ── Clustering ────────────────────────────────────────────────────────────────

def _cluster_units(
    units: list[dict],
    claim_vec,
    fetched: list[dict],
    settings: AgentSettings,
    sim_threshold: float = 0.92,
) -> list[dict]:
    """
    Assign cluster_ids by grouping units whose snippets are very similar
    (syndicated / copy-paste content). Units in the same cluster count as
    ONE independent evidence source.
    """
    if len(units) <= 1:
        for u in units:
            u["cluster_id"] = u["domain"] or str(uuid.uuid4())
        return units

    cluster_map: dict[int, str] = {}
    for i, unit_i in enumerate(units):
        if i in cluster_map:
            continue
        cid = f"cluster_{hashlib.md5(unit_i['url'].encode()).hexdigest()[:8]}"
        cluster_map[i] = cid
        for j, unit_j in enumerate(units):
            if j <= i or j in cluster_map:
                continue
            if _snippet_overlap(unit_i["raw_snippet"], unit_j["raw_snippet"]) > sim_threshold:
                cluster_map[j] = cid  # same cluster = same source

    for i, unit in enumerate(units):
        unit["cluster_id"] = cluster_map.get(i, f"cluster_{i}")
        # Reduce independence weight for syndicated clusters
        cluster_size = sum(1 for v in cluster_map.values() if v == unit["cluster_id"])
        if cluster_size > 1:
            unit["independence_weight"] = round(1.0 / cluster_size, 3)

    return units


def _snippet_overlap(a: str, b: str) -> float:
    """Jaccard overlap on 4-grams as a cheap syndication detector."""
    def ngrams(text, n=4):
        tokens = text.lower().split()
        return set(tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1))
    ng_a, ng_b = ngrams(a), ngrams(b)
    if not ng_a or not ng_b:
        return 0.0
    return len(ng_a & ng_b) / len(ng_a | ng_b)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sim_to_lr(sim: float, settings: AgentSettings) -> float:
    m = settings.lr_mapping
    if sim >= 0.85:
        return m["high"]
    elif sim >= 0.65:
        return m["medium"]
    elif sim >= 0.40:
        return m["low"]
    return m["noise"]


def _token_overlap(a: str, b: str) -> float:
    ta = set(a.lower().split())
    tb = set(b.lower().split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _estimate_velocity(units: list[dict], claim_ts: datetime) -> float:
    """
    Fraction of supporting units that appeared within 6 h of claim timestamp.
    High velocity + low independence = coordinated amplification signal.
    """
    supporting = [u for u in units if u["type"] == "support"]
    if not supporting:
        return 0.0
    within_6h = 0
    for u in supporting:
        ts = u.get("timestamp")
        if ts and isinstance(ts, datetime):
            delta_h = abs((ts - claim_ts).total_seconds()) / 3600
            if delta_h <= 6:
                within_6h += 1
    return round(within_6h / len(supporting), 3)
