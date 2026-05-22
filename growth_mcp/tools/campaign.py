"""Campaign planning tools."""

# Level definitions
CAMPAIGN_LEVELS = {
    "S": {
        "name": "Small",
        "channels": ["in-app push", "in-app banner", "owned out-app"],
        "budget_range": "< 50M VND",
        "timeline": "1-2 weeks",
        "description": "Single segment, 1-2 creatives, no paid media"
    },
    "M": {
        "name": "Medium",
        "channels": ["S channels", "paid social", "paid search"],
        "budget_range": "50-200M VND",
        "timeline": "2-4 weeks",
        "description": "Multi-segment, comm planning, limited paid reach"
    },
    "L": {
        "name": "Large",
        "channels": ["M channels", "TV", "OOH", "KOL"],
        "budget_range": "200M - 1B+ VND",
        "timeline": "4-8 weeks",
        "description": "Full funnel, cross-team, research-backed"
    }
}


def design_campaign(level: str, objective: str, target_segment: str,
                    channels: list[str] | None = None,
                    budget: str | None = None) -> dict:
    """Design a campaign brief based on level and constraints.

    Args:
        level: Campaign level (S/M/L)
        objective: Campaign objective (e.g. "increase MAU", "reactivate lapsed")
        target_segment: Target user segment description
        channels: Optional list of channels
        budget: Optional budget estimate
    """
    level_info = CAMPAIGN_LEVELS.get(level.upper(), CAMPAIGN_LEVELS["S"])

    return {
        "level": level.upper(),
        "level_info": level_info,
        "objective": objective,
        "target": target_segment,
        "channels": channels or level_info["channels"],
        "budget": budget or level_info["budget_range"],
        "timeline": level_info["timeline"],
        "key_considerations": [
            f"Design {objective} tactics within {level.upper()} constraints",
            f"Primary channel: {(channels or level_info['channels'])[0]}",
            f"Segment: {target_segment}"
        ],
        "prompt_reference": "https://github.com/thaolst/ai-growth-prompts/tree/main/00-campaign-level"
    }


def suggest_voucher(segment: str, objective: str,
                    budget_level: str = "S") -> dict:
    """Suggest voucher design by segment.

    Args:
        segment: Target segment type
        objective: Campaign objective
        budget_level: Budget level (S/M)
    """
    templates = {
        "new_user": {
            "type": "fixed_discount",
            "value": "20-30% off first order",
            "min_spend": "None",
            "expiry": "7 days"
        },
        "active": {
            "type": "cashback",
            "value": "10% cashback up to 50K",
            "min_spend": "200K",
            "expiry": "3 days"
        },
        "lapsed": {
            "type": "fixed_discount",
            "value": "40-50% off",
            "min_spend": "None or low",
            "expiry": "48 hours"
        },
        "high_spender": {
            "type": "free_item_or_large_cashback",
            "value": "Free gift or 15% cashback",
            "min_spend": "500K+",
            "expiry": "7 days"
        }
    }

    seg = segment.lower().replace(" ", "_")
    suggestion = templates.get(seg, templates["active"])

    return {
        "segment": segment,
        "objective": objective,
        "budget_level": budget_level,
        "suggested_voucher": suggestion,
        "note": "Adjust voucher value based on margin and campaign budget",
        "prompt_reference": "https://github.com/thaolst/ai-growth-prompts/tree/main/01-voucher-design"
    }
