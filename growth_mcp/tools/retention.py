"""Retention analysis tools."""

INTERVENTIONS = {
    "S": [
        "In-app push reminder with personalized offer",
        "Time-based trigger (X days since last visit)",
        "Simple streak mechanic (visit 3 days = reward)",
    ],
    "M": [
        "S interventions + paid retargeting",
        "Segment-specific comm sequence",
        "Limited-time challenge with tiered rewards",
    ],
}

CHURN_OFFERS = {
    "high": "High-value personalized voucher, 48h expiry",
    "medium": "Reminder + moderate incentive",
    "low": "Content-driven retention (feature highlights, tips)",
    "healthy": "Maintain engagement, no intervention needed",
}


def analyze_cohort(cohort_data: dict[str, float], campaign_level: str = "S") -> dict:
    """Analyze retention cohort data and identify intervention points."""
    level = campaign_level.upper().strip()
    if level not in INTERVENTIONS:
        level = "S"

    if not isinstance(cohort_data, dict) or len(cohort_data) < 2:
        return {"error": "cohort_data must be a dict with at least 2 period keys."}

    for k, v in cohort_data.items():
        if not isinstance(v, (int, float)) or not (0.0 <= v <= 1.0):
            return {
                "error": (
                    f'Retention values must be between 0.0 and 1.0. '
                    f'Got "{k}": {v!r}'
                )
            }

    periods = sorted(cohort_data.keys())

    drops: dict[str, float] = {}
    for i in range(1, len(periods)):
        prev, curr = periods[i - 1], periods[i]
        prev_val = cohort_data[prev]
        if prev_val == 0:
            continue
        drop = (prev_val - cohort_data[curr]) / prev_val
        drops[f"{prev}->{curr}"] = round(drop * 100, 1)

    if not drops:
        return {"error": "Could not compute drop rates. Check that week_0 retention is > 0."}

    biggest_drop_period = max(drops, key=drops.__getitem__)
    biggest_drop_pct = drops[biggest_drop_period]
    latest_retention = round(cohort_data[periods[-1]] * 100, 1)

    critical_phase = (
        "W0→W1 (early activation)"
        if biggest_drop_period.startswith("week_0") or biggest_drop_period.startswith("week_1")
        else "Later stage"
    )

    return {
        "cohort_summary": {
            "periods": len(periods),
            "latest_retention_pct": latest_retention,
            "biggest_drop": {"period": biggest_drop_period, "drop_pct": biggest_drop_pct},
            "all_drops": drops,
            "data": cohort_data,
        },
        "analysis": {
            "biggest_drop_period": biggest_drop_period,
            "drop_percentage": biggest_drop_pct,
            "critical_phase": critical_phase,
        },
        "interventions": INTERVENTIONS[level],
        "recommended_prompt": (
            "https://github.com/thaolst/ai-growth-prompts/tree/main/02-segment-analysis"
        ),
    }


def predict_churn(
    avg_last_active_days: float,
    total_users: int,
    avg_points_balance: float = 0.0,
    redemption_rate: float = 0.0,
) -> dict:
    """Identify churn risk segments based on activity data."""
    if avg_last_active_days < 0:
        return {"error": "avg_last_active_days must be >= 0."}
    if total_users <= 0:
        return {"error": "total_users must be a positive integer."}
    if not (0.0 <= redemption_rate <= 1.0):
        return {"error": "redemption_rate must be between 0.0 and 1.0."}

    if avg_last_active_days > 60:
        risk, risk_reason = "high", "Users inactive >60 days"
    elif avg_last_active_days > 30:
        risk, risk_reason = "medium", "Users inactive >30 days, approaching churn threshold"
    elif avg_last_active_days > 14:
        risk, risk_reason = "low", "Slight decline in activity"
    else:
        risk, risk_reason = "healthy", "Users are active"

    channel = (
        "in-app push" if risk in ("low", "healthy") else "in-app push + SMS/email"
    )
    points_message = (
        f"Average {avg_points_balance:.0f} points unused — use as re-engagement hook"
        if avg_points_balance > 0
        else "No point balance data"
    )

    return {
        "segment_size": total_users,
        "days_since_last_active": avg_last_active_days,
        "churn_risk": risk,
        "risk_reason": risk_reason,
        "suggested_offer": CHURN_OFFERS[risk],
        "reengagement": {"channel": channel, "urgency": "high" if risk == "high" else "medium"},
        "points_leverage": {"has_unused_points": avg_points_balance > 0, "message": points_message},
        "redemption_rate_pct": round(redemption_rate * 100, 1),
        "prompt_reference": (
            "https://github.com/thaolst/ai-growth-prompts/tree/main/06-retention-strategy"
        ),
    }
