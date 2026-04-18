"""
verification_agent/scoring/aggregator.py
==========================================
Bayesian log-odds aggregation of all evidence units into a single P_true
with confidence interval and plain-English explanation.

This variant:
- normalizes unit fields (polarity → type, ensures numeric lr and independence_weight)
- uses a safe cluster-id fallback so units without cluster ids are not collapsed together
- returns deterministic ordering for traceability
- exposes small tunables (no extra dependencies)
"""
from __future__ import annotations
import math
import uuid
from collections import Counter
from typing import List, Dict, Any

# Tunables (easy to adjust)
LOG_LR_SIGMA_SCALE = 0.3
DEFAULT_LOG_ODDS_VAR = 0.25


def aggregate_evidence(
    units: List[Dict[str, Any]],
    prior: float = 0.5,
) -> Dict[str, Any]:
    """
    Parameters
    ----------
    units   : list of evidence unit dicts (may have lr, independence_weight, type, cluster_id, content_hash, id)
    prior   : P(claim is true) before seeing any evidence

    Returns
    -------
    {
      "p_true":             float,
      "confidence_interval": [float, float],
      "explanation":        str,
      "log_odds_trace":     list[dict],
    }
    """
    # Defensive copy / normalization
    units = list(units or [])
    _normalize_unit_fields(units)

    # Collapse units to one per cluster (keep max |LR| per cluster)
    deduplicated = _deduplicate_by_cluster(units)

    # Start from prior
    prior_clamped = max(1e-6, min(1 - 1e-6, prior))
    log_odds = _to_log_odds(prior_clamped)
    trace = [{"step": "prior", "log_odds": round(log_odds, 4), "p": round(prior, 4)}]

    variances = []  # for CI computation

    for unit in deduplicated:
        lr = float(unit.get("lr", 1.0))
        w = float(unit.get("independence_weight", 1.0))
        lr = max(1e-4, lr)  # guard log(0)
        adj = w * math.log(lr)
        log_odds += adj
        # Variance contribution (heuristic)
        variances.append((abs(adj) * LOG_LR_SIGMA_SCALE) ** 2)
        trace.append({
            "step": f"unit_{str(unit.get('id') or unit.get('content_hash') or '')[:8]}",
            "domain": unit.get("domain", ""),
            "type": unit.get("type", ""),
            "lr": round(lr, 6),
            "weight": round(w, 4),
            "adj_log_odds": round(adj, 6),
            "cumulative_log_odds": round(log_odds, 6),
        })

    p_true = _from_log_odds(log_odds)

    # CI: Gaussian approx on log-odds
    total_var = sum(variances) if variances else DEFAULT_LOG_ODDS_VAR
    std = math.sqrt(total_var)
    lo_lower = log_odds - 1.96 * std
    lo_upper = log_odds + 1.96 * std
    ci = [
        round(_from_log_odds(lo_lower), 4),
        round(_from_log_odds(lo_upper), 4),
    ]

    explanation = _build_explanation(p_true, ci, deduplicated, units)

    return {
        "p_true": round(p_true, 4),
        "confidence_interval": ci,
        "explanation": explanation,
        "log_odds_trace": trace,
    }


# ── Normalization ────────────────────────────────────────────────────────────

def _normalize_unit_fields(units: List[Dict[str, Any]]) -> None:
    """
    Mutate units in-place to ensure expected fields and types:
    - map 'polarity' -> 'type' (support | contradict | neutral)
    - coerce lr to float, default 1.0
    - ensure independence_weight is float in [0,1], default 1.0
    - ensure id/content_hash exist where possible
    """
    for idx, u in enumerate(units):
        # map polarity synonyms to type
        if "type" not in u:
            pol = (u.get("polarity") or "").lower()
            if pol in ("support", "supporting", "pro", "for"):
                u["type"] = "support"
            elif pol in ("contradict", "contradicting", "contra", "oppose", "against"):
                u["type"] = "contradict"
            else:
                # if polarity absent, try to infer from a numeric 'score' field
                score = u.get("score")
                try:
                    s = float(score)
                    if s > 0.1:
                        u["type"] = "support"
                    elif s < -0.1:
                        u["type"] = "contradict"
                    else:
                        u["type"] = "neutral"
                except Exception:
                    u["type"] = u.get("type") or "neutral"

        # lr coercion
        try:
            u["lr"] = float(u.get("lr", 1.0))
        except Exception:
            u["lr"] = 1.0

        # independence weight
        try:
            iw = float(u.get("independence_weight", 1.0))
            # clamp to [0,1]
            u["independence_weight"] = max(0.0, min(1.0, iw))
        except Exception:
            u["independence_weight"] = 1.0

        # ensure id/content_hash presence for traceability
        if not u.get("content_hash") and not u.get("id"):
            # create a stable-ish fallback using snippet+url if available, else a short uuid
            base = (u.get("snippet") or "") + "|" + (u.get("url") or "")
            if base.strip():
                # deterministic short hash without extra libs: use uuid5-like via uuid.uuid3 with namespace
                try:
                    u["content_hash"] = uuid.uuid5(uuid.NAMESPACE_URL, base).hex[:16]
                except Exception:
                    u["content_hash"] = uuid.uuid4().hex[:16]
            else:
                u["content_hash"] = uuid.uuid4().hex[:16]
        # ensure id mirrors content_hash if id missing
        if not u.get("id"):
            u["id"] = u.get("content_hash")


# ── De-duplication ────────────────────────────────────────────────────────────

def _deduplicate_by_cluster(units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    For each cluster, keep only the most informative unit
    (highest absolute LR deviation from 1.0).

    Safe cluster key selection:
    - prefer explicit cluster_id
    - else prefer content_hash or id
    - else fall back to a unique per-unit token so units without ids are not collapsed
    """
    clusters: Dict[str, Dict[str, Any]] = {}
    for idx, u in enumerate(units):
        cid = u.get("cluster_id")
        if not cid:
            cid = u.get("content_hash") or u.get("id")
        if not cid:
            # unique fallback per unit to avoid accidental collapsing
            cid = f"__unit__{idx}__{uuid.uuid4().hex[:8]}"
        lr = float(u.get("lr", 1.0))
        best = clusters.get(cid)
        if best is None or abs(lr - 1.0) > abs(float(best.get("lr", 1.0)) - 1.0):
            clusters[cid] = u
    # Return deterministic ordering: highest |lr-1| first
    return sorted(clusters.values(), key=lambda x: -abs(float(x.get("lr", 1.0)) - 1.0))


# ── Math helpers ──────────────────────────────────────────────────────────────

def _to_log_odds(p: float) -> float:
    p = max(1e-9, min(1 - 1e-9, p))
    return math.log(p / (1 - p))


def _from_log_odds(lo: float) -> float:
    lo = max(-500, min(500, lo))
    return 1.0 / (1.0 + math.exp(-lo))


# ── Explanation builder ───────────────────────────────────────────────────────

def _build_explanation(
    p_true: float,
    ci: List[float],
    deduped: List[Dict[str, Any]],
    all_units: List[Dict[str, Any]],
) -> str:
    n_total = len(all_units)
    n_unique = len(deduped)
    n_support = sum(1 for u in deduped if (u.get("type") or "").lower() == "support")
    n_contra = sum(1 for u in deduped if (u.get("type") or "").lower() == "contradict")
    n_clusters = len({u.get("cluster_id") or u.get("content_hash") or u.get("id") for u in deduped})

    provenances = Counter(u.get("provenance", "unknown") for u in all_units)
    prov_str = ", ".join(f"{k}={v}" for k, v in provenances.most_common(4))

    ci_width = ci[1] - ci[0]
    confidence_label = (
        "high confidence" if ci_width <= 0.20 else
        "moderate confidence" if ci_width <= 0.35 else
        "low confidence"
    )

    verdict = (
        "strongly supported" if p_true >= 0.80 else
        "likely true" if p_true >= 0.65 else
        "uncertain" if p_true >= 0.45 else
        "likely false" if p_true >= 0.25 else
        "strongly contradicted"
    )

    return (
        f"Claim is {verdict} (P_true={p_true:.2f}, {confidence_label}, "
        f"CI=[{ci[0]:.2f},{ci[1]:.2f}]). "
        f"Processed {n_total} raw evidence units collapsed to {n_unique} independent units "
        f"across {n_clusters} clusters. "
        f"{n_support} unit(s) support the claim; {n_contra} contradict it. "
        f"Evidence sources: {prov_str}."
    )
