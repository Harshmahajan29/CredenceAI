"""
verification_agent/tests/test_agent_integration.py
====================================================
Integration test: runs the full agent pipeline end-to-end with all
external calls mocked out so no real network access is needed.

Run with: pytest tests/test_agent_integration.py -v
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch

SAMPLE_CLAIM = {
    "claim_id":   "integ-001",
    "claim_text": "Company X announced a major acquisition of Company Y for $5 billion.",
    "timestamp":  "2026-04-18T10:00:00Z",
    "initial_urls": [
        {
            "url":        "https://example-news.com/article-1",
            "domain":     "example-news.com",
            "snippet":    "Company X has agreed to acquire Company Y...",
            "fetched_at": "2026-04-18T10:01:00Z",
            "metadata":   {"content_hash": "hash1", "source_type": "news"},
        }
    ],
    "entities":    ["Company X", "Company Y"],
    "context":     {"time_window_hours": 72},
    "source_meta": {"producer": "scraper_v2", "scrape_time": "2026-04-18T10:00:00Z"},
}

# Canned pipeline return values
MOCK_MULTI_SEARCH = {
    "evidence_units": [
        {"id": "ms1", "type": "support", "domain": "news-a.com",
         "url": "https://news-a.com/1", "timestamp": None, "similarity": 0.82,
         "lr": 3.0, "independence_weight": 1.0, "cluster_id": "c1",
         "provenance": "multi_search", "raw_snippet": "Company X acquires Company Y"},
        {"id": "ms2", "type": "support", "domain": "news-b.com",
         "url": "https://news-b.com/1", "timestamp": None, "similarity": 0.78,
         "lr": 2.5, "independence_weight": 1.0, "cluster_id": "c2",
         "provenance": "multi_search", "raw_snippet": "X buys Y for 5B"},
        {"id": "ms3", "type": "support", "domain": "news-c.com",
         "url": "https://news-c.com/1", "timestamp": None, "similarity": 0.75,
         "lr": 2.0, "independence_weight": 1.0, "cluster_id": "c3",
         "provenance": "multi_search", "raw_snippet": "Acquisition confirmed"},
    ],
    "searches_performed": 4,
    "independent_clusters": 3,
    "propagation_velocity": 0.3,
}

MOCK_SOCIAL = {
    "evidence_units": [
        {"id": "soc1", "type": "support", "domain": "twitter",
         "url": "", "timestamp": None, "similarity": 0.6,
         "lr": 1.4, "independence_weight": 0.9, "cluster_id": "twitter",
         "provenance": "social_sentiment", "raw_snippet": "big deal",
         "sentiment_score": 0.5, "bot_score": 0.05},
    ],
    "searches_performed": 2,
    "social_clusters": [{"platform": "twitter", "count": 1}],
    "sentiment_strength": 0.5,
    "bot_score": 0.05,
    "propagation_velocity": 0.3,
}

MOCK_MODEL = {
    "evidence_units": [
        {"id": "fc1", "type": "support", "domain": "factcheck.org",
         "url": "https://factcheck.org/1", "timestamp": None, "similarity": 0.9,
         "lr": 3.5, "independence_weight": 1.0, "cluster_id": "factcheck_google",
         "provenance": "google_factcheck", "raw_snippet": "Confirmed: X acquires Y"},
    ],
    "searches_performed": 3,
    "fact_check_hits": [{"source": "factcheck.org", "rating": "true", "url": "", "is_primary": True}],
    "primary_documents": [{"source": "factcheck.org"}],
    "market_signals": {"price_change_pct": 3.5, "anomaly": False},
    "risk_proxy": 0.17,
}

MOCK_SOURCE = {
    "evidence_units": [],
    "searches_performed": 0,
    "independence_weights": {"example-news.com": 0.9},
    "source_behavior_metrics": {},
    "recommended_ttls": {},
}


class TestAgentIntegration:
    @pytest.fixture
    def mock_pipelines(self):
        with (
            patch("agent.run_multi_search",    new=AsyncMock(return_value=MOCK_MULTI_SEARCH)),
            patch("agent.run_social_sentiment", new=AsyncMock(return_value=MOCK_SOCIAL)),
            patch("agent.run_model_validation", new=AsyncMock(return_value=MOCK_MODEL)),
            patch("agent.run_source_behavior",  new=AsyncMock(return_value=MOCK_SOURCE)),
        ):
            yield

    def test_output_structure(self, mock_pipelines):
        from CredenceAI.backend.agent.agent import run_agent
        result = asyncio.run(run_agent(SAMPLE_CLAIM))
        required = [
            "claim_id", "p_true", "credibility_score", "bucket",
            "confidence_interval", "explanation", "evidence_units",
            "actions", "meta", "zero_trust_mode",
        ]
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_claim_id_preserved(self, mock_pipelines):
        from CredenceAI.backend.agent.agent import run_agent
        result = asyncio.run(run_agent(SAMPLE_CLAIM))
        assert result["claim_id"] == "integ-001"

    def test_p_true_in_range(self, mock_pipelines):
        from CredenceAI.backend.agent.agent import run_agent
        result = asyncio.run(run_agent(SAMPLE_CLAIM))
        assert 0.0 <= result["p_true"] <= 1.0

    def test_credibility_score_in_range(self, mock_pipelines):
        from CredenceAI.backend.agent.agent import run_agent
        result = asyncio.run(run_agent(SAMPLE_CLAIM))
        assert 0 <= result["credibility_score"] <= 100

    def test_score_matches_p_true(self, mock_pipelines):
        from CredenceAI.backend.agent.agent import run_agent
        result = asyncio.run(run_agent(SAMPLE_CLAIM))
        assert result["credibility_score"] == round(result["p_true"] * 100)

    def test_ci_valid(self, mock_pipelines):
        from CredenceAI.backend.agent.agent import run_agent
        result = asyncio.run(run_agent(SAMPLE_CLAIM))
        ci = result["confidence_interval"]
        assert len(ci) == 2
        assert ci[0] <= result["p_true"] <= ci[1]

    def test_zero_trust_mode(self, mock_pipelines):
        from CredenceAI.backend.agent.agent import run_agent
        result = asyncio.run(run_agent(SAMPLE_CLAIM))
        assert result["zero_trust_mode"] is True

    def test_meta_fields_present(self, mock_pipelines):
        from CredenceAI.backend.agent.agent import run_agent
        result = asyncio.run(run_agent(SAMPLE_CLAIM))
        meta = result["meta"]
        assert "searches_performed" in meta
        assert "elapsed_ms" in meta
        assert "plan_trace" in meta
        assert isinstance(meta["plan_trace"], list)
        assert len(meta["plan_trace"]) > 0

    def test_evidence_units_collected(self, mock_pipelines):
        from CredenceAI.backend.agent.agent import run_agent
        result = asyncio.run(run_agent(SAMPLE_CLAIM))
        # 3 multi_search + 1 social + 1 model = 5 units
        assert len(result["evidence_units"]) >= 4

    def test_actions_not_empty(self, mock_pipelines):
        from CredenceAI.backend.agent.agent import run_agent
        result = asyncio.run(run_agent(SAMPLE_CLAIM))
        assert isinstance(result["actions"], list)
        assert len(result["actions"]) >= 1

    def test_strong_evidence_gives_high_score(self, mock_pipelines):
        from CredenceAI.backend.agent.agent import run_agent
        result = asyncio.run(run_agent(SAMPLE_CLAIM))
        # With 3 support LR=2-3.5 units, expect score > 80
        assert result["credibility_score"] > 70

    def test_invalid_claim_raises(self, mock_pipelines):
        from CredenceAI.backend.agent.agent import run_agent
        with pytest.raises((ValueError, Exception)):
            asyncio.run(run_agent({"bad": "input"}))

    def test_pipeline_failure_graceful(self):
        """Agent should not crash if one pipeline raises."""
        from CredenceAI.backend.agent.agent import run_agent
        with (
            patch("agent.run_multi_search",    new=AsyncMock(side_effect=RuntimeError("network down"))),
            patch("agent.run_social_sentiment", new=AsyncMock(return_value=MOCK_SOCIAL)),
            patch("agent.run_model_validation", new=AsyncMock(return_value=MOCK_MODEL)),
            patch("agent.run_source_behavior",  new=AsyncMock(return_value=MOCK_SOURCE)),
        ):
            result = asyncio.run(run_agent(SAMPLE_CLAIM))
            assert "p_true" in result   # still returns a verdict
            assert result["p_true"] >= 0.0

    def test_output_is_json_serialisable(self, mock_pipelines):
        from CredenceAI.backend.agent.agent import run_agent
        result = asyncio.run(run_agent(SAMPLE_CLAIM))
        serialised = json.dumps(result, default=str)
        assert len(serialised) > 100
