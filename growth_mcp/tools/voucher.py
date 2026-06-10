"""Voucher ladder optimization tools.

Ported and developed from the original standalone tools/voucher.py.
Complements campaign.suggest_voucher: that one picks a template by segment,
this one computes a tiered voucher ladder with abuse risk assessment.
"""

MAX_PCT_DISCOUNT = 25  # practical hard cap in the VN market
VALID_VOUCHER_TYPES = {"fixed", "percentage"}


def optimize_voucher(
    avg_order_value_vnd: int,
    target_conversion_lift_pct: float,
    budget_per_user_vnd: int,
    voucher_type: str = "fixed",
) -> dict:
    """Design an optimized voucher ladder with abuse risk assessment.

    Args:
        avg_order_value_vnd: Current AOV in VND.
        target_conversion_lift_pct: Target conversion lift in percent (20 = +20%).
        budget_per_user_vnd: Max budget per user in VND.
        voucher_type: "fixed" (VND cashback) or "percentage" (% discount).
    """
    vtype = voucher_type.lower().strip()
    if vtype not in VALID_VOUCHER_TYPES:
        return {
            "error": (
                f"Invalid voucher_type '{voucher_type}'. "
                f"Valid options: {sorted(VALID_VOUCHER_TYPES)}."
            )
        }
    if avg_order_value_vnd <= 0:
        return {"error": "avg_order_value_vnd must be positive."}
    if budget_per_user_vnd <= 0:
        return {"error": "budget_per_user_vnd must be positive."}
    if target_conversion_lift_pct <= 0:
        return {"error": "target_conversion_lift_pct must be positive."}

    if vtype == "percentage":
        base = min(target_conversion_lift_pct * 0.6, MAX_PCT_DISCOUNT * 0.6)
        tiers = [
            {
                "spend_threshold_vnd": int(avg_order_value_vnd * 0.8),
                "discount": f"{base:.0f}%",
            },
            {
                "spend_threshold_vnd": int(avg_order_value_vnd * 1.0),
                "discount": f"{min(base * 1.4, MAX_PCT_DISCOUNT):.0f}%",
            },
            {
                "spend_threshold_vnd": int(avg_order_value_vnd * 1.5),
                "discount": f"{min(base * 1.7, MAX_PCT_DISCOUNT):.0f}%",
            },
        ]
    else:
        # Fixed: step from budget, even increments to keep incentive at each tier
        step = int(budget_per_user_vnd * 0.5)
        tiers = [
            {
                "spend_threshold_vnd": int(avg_order_value_vnd * 0.8),
                "discount_vnd": step,
            },
            {
                "spend_threshold_vnd": int(avg_order_value_vnd * 1.0),
                "discount_vnd": step * 2,
            },
            {
                "spend_threshold_vnd": int(avg_order_value_vnd * 1.5),
                "discount_vnd": step * 3,
            },
        ]

    ratio = budget_per_user_vnd / avg_order_value_vnd
    if ratio > 0.15:
        abuse_risk = "HIGH"
    elif ratio > 0.08:
        abuse_risk = "MEDIUM"
    else:
        abuse_risk = "LOW"

    abuse_flags = ["Limit 1 voucher per user per device"]
    if abuse_risk != "LOW":
        abuse_flags.append("Require phone verification before issuing")
    else:
        abuse_flags.append("Low risk: standard guardrails are sufficient")

    return {
        "voucher_type": vtype,
        "voucher_ladder": tiers,
        "budget_to_aov_ratio": round(ratio, 3),
        "abuse_risk": abuse_risk,
        "abuse_flags": abuse_flags,
        "estimated_cost_per_conversion_vnd": int(budget_per_user_vnd),
        "note": (
            "Percentage discounts are capped at "
            f"{MAX_PCT_DISCOUNT}% (practical VN market ceiling)."
        ),
    }
