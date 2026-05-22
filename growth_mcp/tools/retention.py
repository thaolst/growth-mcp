"""Retention analysis tools."""


def analyze_cohort(cohort_data: dict[str, float],
                   campaign_level: str = "S") -> dict:
    """Analyze retention cohort data and identify intervention points.

    Args:
        cohort_data: Dict mapping period to retention rate
                     e.g. {"week_0": 1.0, "week_1": 0.68, "week_2": 0.45}
        campaign_level: Campaign level for intervention feasibility
    """
    periods = sorted(cohort_data.keys())
    drops = {}

    for i in range(1, len(periods)):
        prev = periods[i - 1]
        curr = periods[i]
        drop = (cohort_data[prev] - cohort_data[curr]) / cohort_data[prev]
        drops[f"{prev}->{curr}"] = round(drop * 100, 1)

    # Find the biggest drop
    biggest_drop_period = max(drops, key=drops.get)
    biggest_drop_pct = drops[biggest_drop_period]

    # Determine phase
    latest_period = periods[-1]
    latest_retention = cohort_data[latest_period]
    overall_retention = round(latest_retention * 100, 1)

    # Intervention suggestions by level
    interventions = {
        "S": [
            "In-app push reminder with personalized offer",
            "Time-based trigger (X days since last visit)",
            "Simple streak mechanic (visit 3 days = reward)"
        ],
        "M": [
            "S interventions + paid retargeting",
            "Segment-specific comm sequence",
            "Limited-time challenge with tiered rewards"
        ]
    }

    return {
        "cohort_summary": {
            "periods": len(periods),
            "latest_retention": overall_retention,
            "biggest_drop": {
                "period": biggest_drop_period,
                "drop_pct": biggest_drop_pct
            },
            "data": cohort_data
        },
        "analysis": {
            "biggest_drop_period": biggest_drop_period,
            "drop_percentage": biggest_drop_pct,
            "critical_phase": "W0->W1" if biggest_drop_period.startswith("week_0") or biggest_drop_period.startswith("week_1") else "Later stage"
        },
        "interventions": interventions.get(campaign_level.upper(), interventions["S"]),
        "recommended_prompt": "https://github.com/thaolst/ai-growth-prompts/tree/main/02-segment-analysis"
    }


def predict_churn(avg_last_active_days: float,
                  total_users: int,
                  avg_points_balance: float = 0,
                  redemption_rate: float = 0.0) -> dict:
    """Identify churn risk segments based on activity data.

    Args:
        avg_last_active_days: Average days since last active
        total_users: Total users in segment
        avg_points_balance: Average point balance
        redemption_rate: Percentage of users who redeemed in last 30 days
    """
    if avg_last_active_days > 60:
        risk = "high"
        risk_reason = "Users inactive >60 days"
    elif avg_last_active_days > 30:
        risk = "medium"
        risk_reason = "Users inactive >30 days, approaching churn threshold"
    elif avg_last_active_days > 14:
        risk = "low"
        risk_reason = "Slight decline in activity"
    else:
        risk = "healthy"
        risk_reason = "Users are active"

    offers = {
        "high": "High-value personalized voucher, 48h expiry",
        "medium": "Reminder + moderate incentive",
        "low": "Content-driven retention (feature highlights, tips)",
        "healthy": "Maintain engagement, no intervention needed"
    }

    return {
        "segment_size": total_users,
        "days_since_last_active": avg_last_active_days,
        "churn_risk": risk,
        "risk_reason": risk_reason,
        "suggested_offer": offers.get(risk, ""),
        "reengagement": {
            "channel": "in-app push" if risk in ("low", "healthy") else "in-app push + SMS/email",
            "urgency": "high" if risk == "high" else "medium",
        },
        "points_leverage": {
            "has_unused_points": avg_points_balance > 0,
            "message": f"Average {avg_points_balance:.0f} points unused — use as re-engagement hook" if avg_points_balance > 0 else "No point balance data"
        },
        "prompt_reference": "https://github.com/thaolst/ai-growth-prompts/tree/main/06-retention-strategy"
    }
