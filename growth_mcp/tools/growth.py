"""Growth marketing tools: suggest_channel_mix, forecast_cohort, segment_users."""

import math
import re


# === suggest_channel_mix ===

CHANNEL_PROFILES = {
    "acquisition": {
        "primary": ["paid_social", "paid_search", "referral"],
        "secondary": ["influencer", "app_store_ads"],
        "avoid": ["email"],
        "note": "Focus spend on high-intent channels. Referral has best CAC for fintech.",
    },
    "activation": {
        "primary": ["in_app_push", "in_app_banner", "onboarding_email"],
        "secondary": ["sms"],
        "avoid": ["paid_social"],
        "note": "User already installed — owned channels drive first transaction cheapest.",
    },
    "retention": {
        "primary": ["in_app_push", "email", "in_app_banner"],
        "secondary": ["sms", "paid_retargeting"],
        "avoid": ["paid_search", "influencer"],
        "note": "Owned channels first. Add paid retargeting only if owned CTR < 3%.",
    },
    "reactivation": {
        "primary": ["push", "email", "paid_retargeting"],
        "secondary": ["sms"],
        "avoid": [],
        "note": "Dormant users need stronger signal — combine owned + paid. Time-limited offer works best.",
    },
    "monetization": {
        "primary": ["in_app_banner", "in_app_push", "email"],
        "secondary": ["loyalty_program"],
        "avoid": ["paid_social"],
        "note": "High-value users respond to personalized upgrade offers, not broad paid spend.",
    },
}

BUDGET_SPLITS = {
    "S": {"owned": 100, "paid": 0, "note": "Under 50M VND — owned channels only"},
    "M": {"owned": 60, "paid": 40, "note": "50-200M VND — mix owned + limited paid"},
    "L": {"owned": 40, "paid": 60, "note": "200M+ VND — full funnel, heavy paid for scale"},
}


def suggest_channel_mix(
    objective: str,
    budget_level: str,
    available_channels: list[str] | None = None,
) -> dict:
    """Suggest channel allocation for a growth campaign.

    Args:
        objective: Campaign objective — acquisition, activation, retention, reactivation, monetization
        budget_level: S (< 50M VND), M (50-200M VND), L (200M+ VND)
        available_channels: Optional list of channels available to use
    """
    obj = objective.lower().strip()
    if obj not in CHANNEL_PROFILES:
        return {"error": f"Unknown objective \'{objective}\'. Use: {list(CHANNEL_PROFILES.keys())}"}

    lvl = budget_level.upper().strip()
    if lvl not in BUDGET_SPLITS:
        return {"error": f"budget_level must be S, M, or L. Got \'{budget_level}\'"}

    profile = CHANNEL_PROFILES[obj]
    split = BUDGET_SPLITS[lvl]

    primary = profile["primary"]
    secondary = profile["secondary"]

    if available_channels:
        available = [c.lower().strip() for c in available_channels]
        primary = [c for c in primary if any(a in c for a in available)]
        secondary = [c for c in secondary if any(a in c for a in available)]

    return {
        "objective": objective,
        "budget_level": lvl,
        "budget_split": {
            "owned_channels_pct": split["owned"],
            "paid_channels_pct": split["paid"],
            "note": split["note"],
        },
        "recommended_channels": {
            "primary": primary,
            "secondary": secondary,
            "avoid": profile["avoid"],
        },
        "strategy_note": profile["note"],
        "prioritization": (
            f"Start with {primary[0] if primary else 'owned channels'} to validate message. "
            f"Scale to secondary channels once primary CTR > 3%."
        ),
    }


# === forecast_cohort ===

def _period_to_days(period: str) -> int:
    """Convert period label to numeric days for sorting. D1->1, W1->7, M1->30."""
    m = re.match(r"([DWMdwm])(\d+)", period.strip())
    if not m:
        return 0
    unit, n = m.group(1).upper(), int(m.group(2))
    return n * {"D": 1, "W": 7, "M": 30}[unit]


def _erf(x: float) -> float:
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    p = 0.3275911
    sign = 1 if x >= 0 else -1
    x = abs(x)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t) * math.exp(-x * x)
    return sign * y


def _fit_decay(periods_days: list[int], values: list[float]) -> tuple[float, float]:
    xs, ys = [], []
    for i, (d, v) in enumerate(zip(periods_days, values)):
        if v > 0 and d > 0:
            xs.append(math.log(d))
            ys.append(math.log(v))
    if len(xs) < 2:
        return values[-1] if values else 0.3, -0.3
    n = len(xs)
    sx, sy = sum(xs), sum(ys)
    sxy = sum(x * y for x, y in zip(xs, ys))
    sxx = sum(x * x for x in xs)
    denom = n * sxx - sx * sx
    if abs(denom) < 1e-10:
        return math.exp(sy / n), -0.3
    b = (n * sxy - sx * sy) / denom
    a = math.exp((sy - b * sx) / n)
    return a, b


def forecast_cohort(cohort_data: dict[str, float], forecast_periods: int = 3) -> dict:
    """Forecast future retention based on historical cohort data.

    Args:
        cohort_data: Dict of period label -> retention rate (0.0-1.0).
                     Supports D (day), W (week), M (month) prefixes.
                     E.g. {"D1": 0.6, "D7": 0.4, "D14": 0.3, "D30": 0.22}
        forecast_periods: Number of future periods to forecast (default 3)
    """
    if not isinstance(cohort_data, dict) or len(cohort_data) < 3:
        return {"error": "Need at least 3 cohort data points to forecast."}

    for k, v in cohort_data.items():
        if not isinstance(v, (int, float)) or not (0.0 <= v <= 1.0):
            return {"error": f"Retention values must be 0.0-1.0. Got \'{k}\': {v}"}

    # Sort by actual days
    sorted_periods = sorted(cohort_data.keys(), key=_period_to_days)
    sorted_days = [_period_to_days(p) for p in sorted_periods]
    sorted_values = [cohort_data[p] for p in sorted_periods]

    # Fit power decay
    a, b = _fit_decay(sorted_days, sorted_values)

    # Forecast next periods — infer period spacing
    last_day = sorted_days[-1]
    spacing = sorted_days[-1] - sorted_days[-2] if len(sorted_days) >= 2 else 7
    forecasts = {}
    for i in range(1, forecast_periods + 1):
        next_day = last_day + spacing * i
        predicted = round(max(0.0, min(1.0, a * (next_day ** b))), 3)
        forecasts[f"D{next_day}"] = predicted

    # Drop rates between consecutive periods
    drops = {}
    for i in range(1, len(sorted_periods)):
        prev, curr = sorted_values[i - 1], sorted_values[i]
        drop = round((prev - curr) / prev * 100, 1) if prev > 0 else 0.0
        drops[f"{sorted_periods[i-1]}_to_{sorted_periods[i]}"] = f"{drop}%"

    worst = max(drops.items(), key=lambda x: float(x[1].strip("%"))) if drops else None

    return {
        "historical_sorted": {p: cohort_data[p] for p in sorted_periods},
        "drop_rates": drops,
        "steepest_drop": {
            "period": worst[0] if worst else None,
            "drop": worst[1] if worst else None,
            "recommendation": (
                f"Biggest retention loss at {worst[0]}. Focus re-engagement intervention here."
            ) if worst else None,
        },
        "forecast": forecasts,
        "model": "power_decay",
        "confidence": "medium" if len(cohort_data) >= 5 else "low",
        "note": "Accuracy improves with more historical data points.",
    }


# === segment_users ===

SEGMENT_FRAMEWORKS = {
    "acquisition": {
        "primary_signal": "Install source + first session behavior",
        "tool_note": "Segment by source quality before spending on broad re-engagement.",
        "segments": [
            {
                "name": "High-intent visitors",
                "definition": "Installed app, viewed product/feature page, no transaction yet",
                "size_estimate": "5-15% of installs",
                "approach": "Reduce friction — simplify onboarding, low-barrier first offer",
            },
            {
                "name": "Referred users",
                "definition": "Came from referral link or promo code",
                "size_estimate": "Depends on referral program scale",
                "approach": "High intent — fast-track to first transaction with welcome bonus",
            },
        ],
    },
    "retention": {
        "primary_signal": "Transaction frequency trend over 8 weeks",
        "tool_note": "At-risk actives are cheapest to retain — catch them before they need reactivation budget.",
        "segments": [
            {
                "name": "Power users",
                "definition": "Transaction frequency >= 4x/month, consistent 3+ months",
                "size_estimate": "5-15% of active base",
                "approach": "Loyalty tier upgrades, early access, status recognition",
            },
            {
                "name": "Casual users",
                "definition": "1-3 transactions/month, irregular pattern",
                "size_estimate": "30-50% of active base",
                "approach": "Habit-building mechanics — streak, milestone rewards, regular touchpoints",
            },
            {
                "name": "At-risk actives",
                "definition": "Was transacting regularly, frequency dropped last 2-4 weeks",
                "size_estimate": "10-20% of active base at any given time",
                "approach": "Early intervention — personalized offer before they go dormant",
            },
        ],
    },
    "reactivation": {
        "primary_signal": "Days since last transaction + wallet balance",
        "tool_note": "Churned with balance = highest ROI reactivation segment. Always start here.",
        "segments": [
            {
                "name": "Churned with balance",
                "definition": "Has wallet balance but no transaction in 30+ days",
                "size_estimate": "Subset of dormant — varies by product",
                "approach": "Easiest to reactivate — remind about unused balance with time-limited trigger",
            },
            {
                "name": "Recent dormant",
                "definition": "No transaction 30-60 days, had previous activity",
                "size_estimate": "15-30% of total base typically",
                "approach": "High-value time-limited offer, urgency framing",
            },
            {
                "name": "Long-term dormant",
                "definition": "No transaction 60-180 days",
                "size_estimate": "Varies",
                "approach": "Significant incentive or product update highlight — treat like new acquisition",
            },
        ],
    },
    "monetization": {
        "primary_signal": "Transaction frequency x average order value matrix",
        "tool_note": "High-frequency low-value users have highest upgrade potential — already have the habit.",
        "segments": [
            {
                "name": "High-frequency low-value",
                "definition": "Transacts often but low average order value",
                "size_estimate": "15-25% of active base",
                "approach": "Upgrade incentive — bonus for crossing spend threshold",
            },
            {
                "name": "Low-frequency high-value",
                "definition": "Transacts rarely but high value when they do",
                "size_estimate": "5-10% of active base",
                "approach": "Subscription or loyalty tier to increase frequency",
            },
            {
                "name": "Untapped feature users",
                "definition": "Active on one feature, never tried adjacent features",
                "size_estimate": "20-40% of active base",
                "approach": "Feature cross-sell — demonstrate adjacent value with low-risk trial",
            },
        ],
    },
}


def segment_users(objective: str, context: str | None = None) -> dict:
    """Suggest user segmentation framework based on campaign objective.

    Args:
        objective: Campaign objective — acquisition, retention, reactivation, monetization
        context: Optional context about your product or user base
    """
    obj = objective.lower().strip()
    if obj not in SEGMENT_FRAMEWORKS:
        return {"error": f"Unknown objective \'{objective}\'. Use: {list(SEGMENT_FRAMEWORKS.keys())}"}

    fw = SEGMENT_FRAMEWORKS[obj]

    return {
        "objective": objective,
        "context": context,
        "primary_signal": fw["primary_signal"],
        "segments": fw["segments"],
        "tool_note": fw["tool_note"],
        "next_steps": [
            f"Pull '{fw['primary_signal']}' from your analytics tool",
            "Size each segment — start with the highest ROI one first",
            "Design distinct mechanic per segment, not one-size-fits-all campaign",
        ],
    }
