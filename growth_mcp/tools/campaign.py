"""Campaign planning tools."""

VALID_LEVELS = {"S", "M", "L"}
VALID_SEGMENTS = {"new_user", "active", "lapsed", "high_spender"}
VALID_BUDGET_LEVELS = {"S", "M"}

CAMPAIGN_LEVELS = {
    "S": {
        "name": "Small",
        "channels": ["in-app push", "in-app banner", "owned out-app"],
        "budget_range": "< 50M VND",
        "timeline": "1-2 weeks",
        "description": "Single segment, 1-2 creatives, no paid media",
    },
    "M": {
        "name": "Medium",
        "channels": ["S channels", "paid social", "paid search"],
        "budget_range": "50-200M VND",
        "timeline": "2-4 weeks",
        "description": "Multi-segment, comm planning, limited paid reach",
    },
    "L": {
        "name": "Large",
        "channels": ["M channels", "TV", "OOH", "KOL"],
        "budget_range": "200M - 1B+ VND",
        "timeline": "4-8 weeks",
        "description": "Full funnel, cross-team, research-backed",
    },
}

VOUCHER_TEMPLATES = {
    "new_user": {
        "type": "fixed_discount",
        "value": "20-30% off first order",
        "min_spend": "None",
        "expiry": "7 days",
    },
    "active": {
        "type": "cashback",
        "value": "10% cashback up to 50K",
        "min_spend": "200K",
        "expiry": "3 days",
    },
    "lapsed": {
        "type": "fixed_discount",
        "value": "40-50% off",
        "min_spend": "None or low",
        "expiry": "48 hours",
    },
    "high_spender": {
        "type": "free_item_or_large_cashback",
        "value": "Free gift or 15% cashback",
        "min_spend": "500K+",
        "expiry": "7 days",
    },
}


def design_campaign(
    level: str,
    objective: str,
    target_segment: str,
    channels: list[str] | None = None,
    budget: str | None = None,
) -> dict:
    """Design a campaign brief based on level and constraints."""
    level = level.upper().strip()
    if level not in VALID_LEVELS:
        return {
            "error": f"Invalid level '{level}'. Must be one of: {sorted(VALID_LEVELS)}."
        }

    level_info = CAMPAIGN_LEVELS[level]
    effective_channels = channels or level_info["channels"]

    return {
        "level": level,
        "level_info": level_info,
        "objective": objective,
        "target": target_segment,
        "channels": effective_channels,
        "budget": budget or level_info["budget_range"],
        "timeline": level_info["timeline"],
        "key_considerations": [
            f"Design {objective} tactics within {level} constraints",
            f"Primary channel: {effective_channels[0]}",
            f"Segment: {target_segment}",
        ],
        "prompt_reference": "https://github.com/thaolst/ai-growth-prompts/tree/main/00-campaign-level",
    }


def suggest_voucher(segment: str, objective: str, budget_level: str = "S") -> dict:
    """Suggest voucher design by segment."""
    seg = segment.lower().strip().replace(" ", "_")
    budget_level = budget_level.upper().strip()

    if seg not in VALID_SEGMENTS:
        return {
            "error": (
                f"Unknown segment '{segment}'. "
                f"Valid options: {sorted(VALID_SEGMENTS)}."
            )
        }
    if budget_level not in VALID_BUDGET_LEVELS:
        return {
            "error": (
                f"Invalid budget_level '{budget_level}'. "
                f"Valid options: {sorted(VALID_BUDGET_LEVELS)}."
            )
        }

    suggestion = VOUCHER_TEMPLATES[seg]

    return {
        "segment": seg,
        "objective": objective,
        "budget_level": budget_level,
        "suggested_voucher": suggestion,
        "note": "Adjust voucher value based on margin and campaign budget",
        "prompt_reference": "https://github.com/thaolst/ai-growth-prompts/tree/main/01-voucher-design",
    }
