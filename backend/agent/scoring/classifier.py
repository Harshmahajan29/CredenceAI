
from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional

def classify_score(
    p_true: float,
    ci: Optional[List[float]],
    entities: Optional[List[str]],
    market_signals: Optional[Dict[str, Any]],
    social_signals: Optional[Dict[str, Any]],
    independent_clusters: int,
) -> Tuple[int, str, List[Dict[str, Any]]]:
    """
    Returns (credibility_score, bucket, actions).
    Defensive: accepts None for optional inputs and coerces numeric fields.
    """
    # Defensive defaults
    p_true = float(p_true or 0.0)
    p_true = max(0.0, min(1.0, p_true))
    ci = ci or [max(0.0, p_true - 0.1), min(1.0, p_true + 0.1)]
    entities = entities or []
    market_signals = market_signals or {}
    social_signals = social_signals or {}

    # Score and bucket
    score = int(round(p_true * 100))
    score = max(0, min(100, score))
    bucket = _to_bucket(score)

    # CI width safe
    try:
        ci_width = float(ci[1]) - float(ci[0])
    except Exception:
        ci_width = 1.0

    actions: List[Dict[str, Any]] = []

    # Low credibility
    if bucket == "low":
        actions.append({
            "type": "recommend_human_review",
            "reason": "credibility_low",
            "detail": f"credibilityScore={score}, P_true={p_true:.2f}",
        })
        actions.append({
            "type": "block_automated_action",
            "reason": "claim_likely_false",
        })

    # Moderate or insufficient evidence
    elif bucket == "moderate" or ci_width > 0.30 or independent_clusters < 3:
        actions.append({
            "type": "recommend_human_review",
            "reason": "insufficient_evidence" if independent_clusters < 3 else "high_uncertainty",
            "detail": f"independent_clusters={independent_clusters}, CI_width={ci_width:.2f}",
        })

    # Social signals
    try:
        prop_velocity = float(social_signals.get("propagation_velocity", 0.0) or 0.0)
    except Exception:
        prop_velocity = 0.0
    try:
        bot_score = float(social_signals.get("bot_score", 0.0) or 0.0)
    except Exception:
        bot_score = 0.0

    if prop_velocity > 0.6 and independent_clusters < 3:
        actions.append({
            "type": "recommend_human_review",
            "reason": "viral_low_evidence",
            "detail": f"propagation_velocity={prop_velocity:.2f}, independent_clusters={independent_clusters}",
        })
    if bot_score > 0.5:
        actions.append({
            "type": "recommend_human_review",
            "reason": "bot_amplification_detected",
            "detail": f"bot_score={bot_score:.2f}",
        })

    # Financial risk
    try:
        risk_proxy = float(market_signals.get("risk_proxy")) if market_signals.get("risk_proxy") is not None else None
    except Exception:
        risk_proxy = None
    try:
        price_change = abs(float(market_signals.get("price_change_pct", 0.0) or 0.0))
    except Exception:
        price_change = 0.0

    if entities and ((risk_proxy is not None and risk_proxy > 0.15) or price_change > 5):
        actions.append({
            "type": "recommend_human_review",
            "reason": "financial_exposure_high",
            "detail": f"risk_proxy={risk_proxy}, price_change_pct={price_change:.2f}",
        })
        actions.append({
            "type": "block_automated_action",
            "reason": "market_moving_risk",
        })

    # Default
    if not actions:
        actions.append({
            "type": "log_only",
            "reason": "claim_verified_within_thresholds",
        })

    # Deduplicate actions (type + reason + detail)
    seen = set()
    deduped_actions: List[Dict[str, Any]] = []
    for a in actions:
        key = (a.get("type", ""), a.get("reason", ""), a.get("detail", ""))
        if key not in seen:
            seen.add(key)
            deduped_actions.append(a)

    return score, bucket, deduped_actions


def _to_bucket(score: int) -> str:
    if score < 40:
        return "low"
    elif score <= 65:
        return "moderate"
    elif score <= 85:
        return "high"
    return "critical"
