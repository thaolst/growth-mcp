"""Growth MCP Server — campaign design, retention analysis, churn prediction."""

import json
from typing import Literal
from mcp.server import FastMCP

from growth_mcp.tools import campaign, retention, experiment, growth

mcp = FastMCP(
    "growth-mcp",
    instructions=(
        "Growth marketing tools for campaign design, retention analysis, and A/B testing. "
        "Use these tools when the user asks about marketing campaigns, user retention, churn, "
        "or A/B experiment analysis. Do NOT use for general financial forecasting or unrelated analytics."
    ),
)


def _ok(result: dict) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False)


def _err(message: str) -> str:
    return json.dumps({"error": message}, indent=2, ensure_ascii=False)


@mcp.tool()
def design_campaign(
    level: Literal["S", "M", "L"],
    objective: str,
    target_segment: str,
    channels: str | None = None,
    budget: str | None = None,
) -> str:
    """Design a growth campaign brief based on level (S/M/L) and constraints.

    Args:
        level: Campaign level — S (small, in-app only), M (medium, some paid), L (large, full funnel)
        objective: What the campaign aims to achieve (e.g. "increase MAU by 10%")
        target_segment: Who the campaign targets (e.g. "lapsed users, inactive >30 days")
        channels: Optional comma-separated channel list (e.g. "push,email,paid_social")
        budget: Optional budget estimate (e.g. "100M VND")
    """
    try:
        channel_list = [c.strip() for c in channels.split(",") if c.strip()] if channels else None
        result = campaign.design_campaign(level, objective, target_segment, channel_list, budget)
        return _ok(result)
    except Exception as e:
        return _err(f"design_campaign failed: {e}")


@mcp.tool()
def suggest_voucher(
    segment: Literal["new_user", "active", "lapsed", "high_spender"],
    objective: str,
    budget_level: Literal["S", "M"] = "S",
) -> str:
    """Suggest voucher design by user segment.

    Args:
        segment: User segment — new_user, active, lapsed, or high_spender
        objective: Campaign objective (e.g. "drive first order", "win back churned users")
        budget_level: S (low cost) or M (moderate budget)
    """
    try:
        result = campaign.suggest_voucher(segment, objective, budget_level)
        return _ok(result)
    except Exception as e:
        return _err(f"suggest_voucher failed: {e}")


@mcp.tool()
def analyze_retention(cohort_data: str, campaign_level: Literal["S", "M"] = "S") -> str:
    """Analyze retention cohort data and identify the biggest churn drop point.

    Args:
        cohort_data: JSON string mapping period keys to retention rates (0.0–1.0).
                     e.g. '{"week_0": 1.0, "week_1": 0.68, "week_2": 0.45, "week_3": 0.32}'
        campaign_level: S or M — used to suggest feasible interventions
    """
    try:
        data = json.loads(cohort_data)
    except json.JSONDecodeError as e:
        return _err(
            f"cohort_data must be valid JSON. Example: "
            f'{{"week_0": 1.0, "week_1": 0.68}}. Parse error: {e}'
        )

    if not isinstance(data, dict) or len(data) < 2:
        return _err("cohort_data must be a JSON object with at least 2 period keys.")

    for k, v in data.items():
        if not isinstance(v, (int, float)) or not (0.0 <= v <= 1.0):
            return _err(
                f"All retention values must be numbers between 0.0 and 1.0. "
                f'Got "{k}": {v!r}'
            )

    try:
        result = retention.analyze_cohort(data, campaign_level)
        return _ok(result)
    except Exception as e:
        return _err(f"analyze_retention failed: {e}")


@mcp.tool()
def predict_churn_risk(
    days_since_last_active: float,
    total_users: int,
    avg_points_balance: float = 0.0,
    redemption_rate: float = 0.0,
) -> str:
    """Predict churn risk level and recommend a re-engagement strategy.

    Args:
        days_since_last_active: Average days since last user activity (must be >= 0)
        total_users: Number of users in the segment (must be > 0)
        avg_points_balance: Average unused loyalty points balance (default 0)
        redemption_rate: Fraction of users who redeemed recently, 0.0–1.0 (default 0.0)
    """
    if days_since_last_active < 0:
        return _err("days_since_last_active must be >= 0.")
    if total_users <= 0:
        return _err("total_users must be a positive integer.")
    if not (0.0 <= redemption_rate <= 1.0):
        return _err("redemption_rate must be between 0.0 and 1.0.")

    try:
        result = retention.predict_churn(
            days_since_last_active, total_users, avg_points_balance, redemption_rate
        )
        return _ok(result)
    except Exception as e:
        return _err(f"predict_churn_risk failed: {e}")


@mcp.tool()
def analyze_experiment(
    control_metric: float,
    treatment_metric: float,
    control_sample: int,
    treatment_sample: int,
    metric_name: str = "conversion",
) -> str:
    """Analyze A/B test results with statistical significance (z-test).

    Args:
        control_metric: Number of conversions/events in control group (count, NOT a rate like 0.05)
        treatment_metric: Number of conversions/events in treatment group (count, NOT a rate)
        control_sample: Total users in control group
        treatment_sample: Total users in treatment group
        metric_name: Human-readable name for the metric (e.g. "checkout_conversion")
    """
    # Detect accidental rate input (e.g. 0.05 instead of 50)
    if 0 < control_metric <= 1 and 0 < treatment_metric <= 1:
        return _err(
            "control_metric and treatment_metric look like rates (values between 0 and 1). "
            "These fields expect raw counts — e.g. 120 conversions out of 1000 users, not 0.12. "
            "Please pass the actual event counts."
        )
    if control_metric < 0 or treatment_metric < 0:
        return _err("control_metric and treatment_metric must be >= 0.")
    if control_sample <= 0 or treatment_sample <= 0:
        return _err("Sample sizes must be positive integers.")
    if control_metric > control_sample:
        return _err(
            f"control_metric ({control_metric}) cannot exceed control_sample ({control_sample})."
        )
    if treatment_metric > treatment_sample:
        return _err(
            f"treatment_metric ({treatment_metric}) cannot exceed treatment_sample ({treatment_sample})."
        )

    try:
        result = experiment.analyze_test(
            control_metric, treatment_metric,
            control_sample, treatment_sample,
            metric_name,
        )
        return _ok(result)
    except Exception as e:
        return _err(f"analyze_experiment failed: {e}")


@mcp.tool()
def estimate_sample_size(
    baseline_rate: float,
    minimum_detectable_effect: float,
    significance: float = 0.05,
    power: float = 0.80,
) -> str:
    """Calculate required sample size per variant for an A/B test.

    Args:
        baseline_rate: Current conversion rate as a decimal (0.0–1.0, e.g. 0.05 for 5%)
        minimum_detectable_effect: Minimum relative lift to detect (0.0–1.0, e.g. 0.10 for 10% lift)
        significance: Type I error rate, default 0.05 (5%)
        power: Statistical power, default 0.80 (80%)
    """
    if not (0.0 < baseline_rate < 1.0):
        return _err("baseline_rate must be between 0 and 1 exclusive (e.g. 0.05 for 5%).")
    if not (0.0 < minimum_detectable_effect < 1.0):
        return _err(
            "minimum_detectable_effect must be between 0 and 1 exclusive "
            "(e.g. 0.10 to detect a 10% relative lift)."
        )
    if not (0.0 < significance < 0.5):
        return _err("significance must be between 0 and 0.5 (e.g. 0.05).")
    if not (0.5 < power < 1.0):
        return _err("power must be between 0.5 and 1.0 (e.g. 0.80).")

    try:
        result = experiment.calculate_sample_size(
            baseline_rate, minimum_detectable_effect, significance, power
        )
        return _ok(result)
    except Exception as e:
        return _err(f"estimate_sample_size failed: {e}")


def main():
    mcp.run()



@mcp.tool()
def suggest_channel_mix(
    objective: str,
    budget_level: str,
    available_channels: str | None = None,
) -> str:
    """Suggest channel allocation for a growth campaign.

    Args:
        objective: Campaign objective — acquisition, activation, retention, reactivation, monetization
        budget_level: S (< 50M VND), M (50-200M VND), L (200M+ VND)
        available_channels: Optional comma-separated list of available channels
    """
    try:
        channels = [c.strip() for c in available_channels.split(",") if c.strip()] if available_channels else None
        result = growth.suggest_channel_mix(objective, budget_level, channels)
        return _ok(result)
    except Exception as e:
        return _err(f"suggest_channel_mix failed: {e}")


@mcp.tool()
def forecast_cohort(
    cohort_data: str,
    forecast_periods: int = 3,
) -> str:
    """Forecast future retention periods based on historical cohort data.

    Args:
        cohort_data: JSON string of period->retention dict. E.g. '{"D1": 0.6, "D7": 0.4, "D30": 0.22}'
        forecast_periods: Number of future periods to forecast (default 3)
    """
    try:
        import json as _json
        data = _json.loads(cohort_data)
        result = growth.forecast_cohort(data, forecast_periods)
        return _ok(result)
    except Exception as e:
        return _err(f"forecast_cohort failed: {e}")


@mcp.tool()
def segment_users(
    objective: str,
    context: str | None = None,
) -> str:
    """Suggest user segmentation framework based on campaign objective.

    Args:
        objective: Campaign objective — acquisition, retention, reactivation, monetization
        context: Optional context about your product or user base
    """
    try:
        result = growth.segment_users(objective, context)
        return _ok(result)
    except Exception as e:
        return _err(f"segment_users failed: {e}")

if __name__ == "__main__":
    main()
