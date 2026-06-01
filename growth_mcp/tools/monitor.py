"""
Campaign monitoring tool — track ongoing campaign KPIs and recommend adjustments.
Monitored metrics: reach, redemption, cost efficiency, schedule adherence.
"""

# Campaign level benchmarks (SEA fintech)
CAMPAIGN_BENCHMARKS = {
    "S": {
        "reach": {"target": 200000, "min": 50000},
        "redemption_rate": {"target": 0.25, "min": 0.10},
        "cost_per_engagement": {"target": 3000, "max": 8000},
        "typical_days": 7,
    },
    "M": {
        "reach": {"target": 1000000, "min": 200000},
        "redemption_rate": {"target": 0.20, "min": 0.08},
        "cost_per_engagement": {"target": 5000, "max": 15000},
        "typical_days": 14,
    },
    "L": {
        "reach": {"target": 5000000, "min": 1000000},
        "redemption_rate": {"target": 0.15, "min": 0.05},
        "cost_per_engagement": {"target": 10000, "max": 30000},
        "typical_days": 30,
    }
}


def assess_campaign(run_days: float, current_reach: int,
                    current_redemptions: int, total_vouchers: int,
                    total_budget: float = 0.0,
                    planned_days: float = 7.0,
                    target_reach: float = 0) -> dict:
    """Assess campaign health and recommend real-time adjustments.

    Args:
        run_days: Days the campaign has been running
        current_reach: Number of users reached so far
        current_redemptions: Number of redemptions so far
        total_vouchers: Total vouchers allocated
        total_budget: Total campaign budget in VND
        planned_days: Planned campaign duration in days
        target_reach: Optional reach target override (0 = auto-detect from level)

    Returns:
        dict: Campaign status, health indicators, and recommendations
    """

    # Auto-detect level based on target_reach or provide generic
    redemption_rate = current_redemptions / max(current_reach, 1)
    cost_per = total_budget / max(current_redemptions, 1)
    progress_pct = min(run_days / max(planned_days, 1), 1.0)

    # Level-appropriate benchmarks
    level = "S"
    if target_reach > 1000000:
        level = "M"
    if target_reach > 5000000:
        level = "L"

    benchmarks = CAMPAIGN_BENCHMARKS.get(level, CAMPAIGN_BENCHMARKS["S"])

    # Health assessments
    health_issues = []

    # Reach check
    projected_reach = current_reach / max(progress_pct, 0.01)
    if projected_reach < benchmarks["reach"]["min"]:
        health_issues.append({
            "severity": "critical",
            "metric": "reach",
            "detail": f"Projected reach ({projected_reach:.0f}) below minimum ({benchmarks['reach']['min']})",
            "action": "Expand channels or increase budget mid-flight"
        })
    elif projected_reach < benchmarks["reach"]["target"]:
        health_issues.append({
            "severity": "warning",
            "metric": "reach",
            "detail": f"Projected reach ({projected_reach:.0f}) below target ({benchmarks['reach']['target']})",
            "action": "Consider boosting top-performing channels"
        })

    # Redemption rate check
    if redemption_rate < benchmarks["redemption_rate"]["min"]:
        health_issues.append({
            "severity": "critical",
            "metric": "redemption_rate",
            "detail": f"Redemption rate ({redemption_rate:.1%}) below minimum ({benchmarks['redemption_rate']['min']:.0%})",
            "action": "Review voucher value, T&C complexity, and delivery channel"
        })
    elif redemption_rate < benchmarks["redemption_rate"]["target"]:
        health_issues.append({
            "severity": "warning",
            "metric": "redemption_rate",
            "detail": f"Redemption rate ({redemption_rate:.1%}) below target ({benchmarks['redemption_rate']['target']:.0%})",
            "action": "A/B test voucher creative or add urgency (countdown)"
        })

    # Budget burn check
    if total_budget > 0:
        budget_used = (run_days / max(planned_days, 1)) * total_budget
        spent_so_far = current_redemptions * cost_per
        burn_rate = spent_so_far / max(budget_used, 1)

        if burn_rate > 1.3:
            health_issues.append({
                "severity": "warning",
                "metric": "budget_burn",
                "detail": f"Budget burning {burn_rate:.0%} faster than planned",
                "action": "Review cost per redemption, consider caps per user"
            })
        elif burn_rate < 0.5 and progress_pct > 0.3:
            health_issues.append({
                "severity": "info",
                "metric": "budget_underspend",
                "detail": f"Budget spending {burn_rate:.0%} of planned pace",
                "action": "Consider boosting distribution or extending campaign"
            })

    # Voucher exhaustion
    if total_vouchers > 0 and current_redemptions > 0:
        exhaustion_rate = current_redemptions / max(total_vouchers, 1)
        projected_exhaustion = exhaustion_rate / max(progress_pct, 0.01)
        if projected_exhaustion > 0.8:
            health_issues.append({
                "severity": "warning",
                "metric": "voucher_exhaustion",
                "detail": f"Projected {projected_exhaustion:.0%} voucher usage — risk of running out",
                "action": "Top up voucher pool or add fallback mechanics"
            })

    # Overall health
    criticals = [h for h in health_issues if h["severity"] == "critical"]
    warnings = [h for h in health_issues if h["severity"] == "warning"]
    infos = [h for h in health_issues if h["severity"] == "info"]

    if criticals:
        overall = "critical"
    elif warnings:
        overall = "needs_attention"
    else:
        overall = "healthy"

    return {
        "campaign_overview": {
            "run_days": run_days,
            "planned_days": planned_days,
            "progress": f"{progress_pct:.0%}",
            "current_reach": current_reach,
            "current_redemptions": current_redemptions,
            "redemption_rate": round(redemption_rate, 4),
            "cost_per_redemption": round(cost_per) if total_budget > 0 else None,
        },
        "health": overall,
        "issues": {
            "critical": criticals,
            "warnings": warnings,
            "info": infos
        },
        "recommendations": [
            h["action"] for h in health_issues[:3]
        ],
        "benchmarks_applied": level
    }
