"""
Segment analysis tool — analyze user segments, compare performance, and recommend targeting.
"""

# Segment archetypes with baseline characteristics
SEGMENT_PROFILES = {
    "new_user": {
        "description": "Signed up < 30 days, exploring features",
        "typical_retention_d7": 0.30,
        "typical_redemption_rate": 0.40,
        "best_mechanic": "first_action_bonus",
        "sensitivity": "high_offer",
        "channel_preference": ["in-app push", "welcome email", "onboarding banner"]
    },
    "active": {
        "description": "Uses app 3+ times/week, transacts regularly",
        "typical_retention_d7": 0.75,
        "typical_redemption_rate": 0.15,
        "best_mechanic": "loyalty_streak",
        "sensitivity": "low_offer",
        "channel_preference": ["in-app push", "in-app banner", "personalized offer"]
    },
    "lapsed": {
        "description": "No activity for 30-90 days, declining engagement",
        "typical_retention_d7": 0.10,
        "typical_redemption_rate": 0.30,
        "best_mechanic": "winback_voucher",
        "sensitivity": "high_offer",
        "channel_preference": ["push", "sms", "email"]
    },
    "churned": {
        "description": "No activity > 90 days, effectively lost",
        "typical_retention_d7": 0.03,
        "typical_redemption_rate": 0.20,
        "best_mechanic": "high_value_retention",
        "sensitivity": "very_high_offer",
        "channel_preference": ["sms", "email", "paid_retargeting"]
    },
    "high_spender": {
        "description": "Top 10% by transaction volume/value",
        "typical_retention_d7": 0.85,
        "typical_redemption_rate": 0.10,
        "best_mechanic": "exclusive_perk",
        "sensitivity": "experience",
        "channel_preference": ["personalized", "vip_communication", "dedicated_support"]
    },
    "voucher_hunter": {
        "description": "Only transacts with voucher, high churn post-promo",
        "typical_retention_d7": 0.12,
        "typical_redemption_rate": 0.60,
        "best_mechanic": "gradual_unlock",
        "sensitivity": "high_offer",
        "channel_preference": ["push", "sms"]
    }
}


def analyze_segment(segment_type: str, segment_size: int = 0,
                    current_retention: float = 0.0,
                    current_redemption_rate: float = 0.0,
                    compare_segments: str = "") -> dict:
    """Analyze a user segment and recommend targeting.

    Args:
        segment_type: Segment type (new_user, active, lapsed, churned, high_spender, voucher_hunter)
        segment_size: Current segment size (optional, for growth assessment)
        current_retention: Current D7 retention (0-1) for this segment
        current_redemption_rate: Current campaign redemption rate (0-1)
        compare_segments: Optional comma-separated list of segments to compare against

    Returns:
        dict: Segment profile, performance comparison, and targeting recommendations
    """
    seg = segment_type.lower().replace(" ", "_")
    profile = SEGMENT_PROFILES.get(seg, {
        "description": "Custom segment — no predefined profile",
        "typical_retention_d7": 0.5,
        "typical_redemption_rate": 0.2,
        "best_mechanic": "test_multiple",
        "sensitivity": "medium",
        "channel_preference": ["in-app push"]
    })

    # Retention gap analysis
    benchmark = profile["typical_retention_d7"]
    retention_gap = None
    if current_retention > 0 and benchmark > 0:
        retention_gap = round(((current_retention - benchmark) / benchmark) * 100, 1)

    # Redemption rate comparison
    redemption_gap = None
    if current_redemption_rate > 0 and profile["typical_redemption_rate"] > 0:
        redemption_gap = round(((current_redemption_rate - profile["typical_redemption_rate"])
                                 / profile["typical_redemption_rate"]) * 100, 1)

    # Priority and action
    if retention_gap is not None and retention_gap < -20:
        priority = "high"
        action = "Urgent intervention needed — retention significantly below benchmark"
    elif retention_gap is not None and retention_gap < 0:
        priority = "medium"
        action = "Room for improvement — consider targeted retention campaign"
    elif retention_gap is not None and retention_gap >= 0:
        priority = "maintain"
        action = "Segment performing at or above benchmark — maintain current strategy"
    else:
        priority = "unknown"
        action = "Provide retention data for better analysis"

    # Segment size opportunity
    size_note = ""
    if segment_size > 0:
        if seg in ("lapsed", "churned"):
            recovery_opportunity = f"Recovering {int(segment_size * 0.05)} users at {profile['typical_retention_d7']:.0%} D7 retention"
            size_note = f"Large dormant pool ({segment_size:,}) — {recovery_opportunity}"
        elif seg == "voucher_hunter":
            size_note = f"Redemption-heavy segment ({segment_size:,}) — can convert to loyal with tiered mechanics"
        else:
            size_note = f"Active base of {segment_size:,} — focus on retention and upsell"

    # Comparison against other segments
    comparison = None
    if compare_segments:
        comparison = []
        for other in compare_segments.split(","):
            other = other.strip().lower().replace(" ", "_")
            other_profile = SEGMENT_PROFILES.get(other)
            if other_profile:
                comparison.append({
                    "segment": other,
                    "description": other_profile["description"],
                    "retention_benchmark": other_profile["typical_retention_d7"],
                    "redemption_benchmark": other_profile["typical_redemption_rate"],
                })

    return {
        "segment": {
            "type": segment_type,
            "size": segment_size if segment_size > 0 else "unknown",
            "profile": profile,
        },
        "performance": {
            "current_retention": current_retention if current_retention > 0 else None,
            "retention_benchmark": benchmark,
            "retention_gap": f"{retention_gap}%" if retention_gap is not None else "no data",
            "current_redemption_rate": current_redemption_rate if current_redemption_rate > 0 else None,
            "redemption_benchmark": profile["typical_redemption_rate"],
            "redemption_gap": f"{redemption_gap}%" if redemption_gap is not None else "no data",
        },
        "priority": priority,
        "action": action,
        "recommended_mechanic": profile["best_mechanic"],
        "recommended_channel": profile["channel_preference"][0],
        "secondary_channel": profile["channel_preference"][1] if len(profile["channel_preference"]) > 1 else None,
        "size_opportunity": size_note,
        "comparison": comparison,
        "prompt_reference": "https://github.com/thaolst/ai-growth-prompts/tree/main/02-segment-analysis"
    }
