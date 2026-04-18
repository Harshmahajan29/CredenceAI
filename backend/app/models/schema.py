from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator
import hashlib


class InitialURL(BaseModel):
    url: HttpUrl
    domain: Optional[str] = Field(None, description="Canonical domain (e.g., example.com)")
    snippet: Optional[str] = Field(None, description="Truncated, redacted text snippet")
    fetched_at: Optional[datetime] = Field(None, description="ISO timestamp when scraped")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator("domain", pre=True, always=True)
    def ensure_domain(cls, v, values):
        # If domain not provided, derive from url
        if v:
            return v
        try:
            return values.get("url").host if hasattr(values.get("url"), "host") else None
        except Exception:
            # best-effort fallback: parse netloc
            from urllib.parse import urlparse
            try:
                return urlparse(str(values.get("url"))).hostname or None
            except Exception:
                return None


class ScraperInput(BaseModel):
    claim_id: str = Field(..., description="Unique identifier for the claim")
    claim_text: str = Field(..., description="Natural language claim to verify")
    timestamp: Optional[datetime] = Field(None, description="When the claim was observed/created")
    initial_urls: List[InitialURL] = Field(default_factory=list, description="Scraped candidate sources")
    entities: Optional[List[str]] = Field(default_factory=list, description="Canonical entity aliases")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional context (time window, tags)")
    source_meta: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Producer metadata")

    @validator("claim_text")
    def non_empty_claim(cls, v):
        if not v or not v.strip():
            raise ValueError("claim_text must be a non-empty string")
        return v.strip()


class EvidenceUnit(BaseModel):
    id: str = Field(..., description="Unique id for the evidence unit (e.g., content hash or uuid)")
    domain: Optional[str] = None
    url: Optional[HttpUrl] = None
    snippet: Optional[str] = None
    fetched_at: Optional[datetime] = None
    content_hash: Optional[str] = None
    similarity: Optional[float] = Field(None, ge=0.0, le=1.0)
    polarity: Optional[str] = Field(None, description="support | contradict | neutral")
    independence_weight: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator("content_hash", pre=True, always=True)
    def compute_hash_if_missing(cls, v, values):
        if v:
            return v
        snippet = values.get("snippet") or ""
        if snippet:
            # short deterministic hash
            return hashlib.sha256(snippet.encode("utf-8", errors="ignore")).hexdigest()[:16]
        return None


class AgentMeta(BaseModel):
    searches_performed: int = 0
    retries: int = 0
    elapsed_ms: Optional[int] = None
    plan_trace: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class AgentOutput(BaseModel):
    claim_id: str
    P_true: float = Field(..., ge=0.0, le=1.0)
    credibilityScore: int = Field(..., ge=0, le=100)
    confidenceInterval: Optional[List[float]] = Field(None, description="[low, high] in 0..1")
    explanation: Optional[str] = None
    evidence_units: List[EvidenceUnit] = Field(default_factory=list)
    risk_proxy: Optional[float] = Field(None, ge=0.0, le=1.0)
    actions: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    meta: Optional[AgentMeta] = Field(default_factory=AgentMeta)
    zeroTrustMode: bool = True
    dashboardTrustedSources: Optional[List[str]] = Field(default_factory=list)
