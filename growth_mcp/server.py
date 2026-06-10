"""Growth MCP Server — campaign design, retention analysis, churn prediction."""

import json
from typing import Literal
from mcp.server import FastMCP

from growth_mcp.tools import campaign, retention, experiment, growth, monitor, segment, voucher, datasource, bigquery_source

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
def inspect_csv(file_path: str) -> str:
    """Inspect a local CSV file: columns, inferred types, row count, sample rows.

    Run this first before any *_from_csv tool to discover column names.

    Args:
        file_path: Absolute or relative path to a local CSV file
    """
    try:
        return _ok(datasource.inspect_csv(file_path))
    except Exception as e:
        return _err(f"inspect_csv failed: {e}")


@mcp.tool()
def analyze_experiment_from_csv(
    file_path: str,
    group_col: str,
    converted_col: str,
    control_label: str = "control",
    treatment_label: str = "treatment",
    metric_name: str = "conversion",
) -> str:
    """Run an A/B test analysis directly from a raw CSV (one row per user).

    Aggregates conversions per group and runs a two-proportion z-test.
    Use analyze_experiment instead if you already have aggregated counts.

    Args:
        file_path: Path to CSV with one row per user
        group_col: Column holding the experiment group label
        converted_col: Column holding conversion flag (1/0, true/false, yes/no)
        control_label: Value in group_col marking the control group
        treatment_label: Value in group_col marking the treatment group
        metric_name: Name of the metric for reporting
    """
    try:
        return _ok(datasource.analyze_experiment_from_csv(
            file_path, group_col, converted_col,
            control_label, treatment_label, metric_name,
        ))
    except Exception as e:
        return _err(f"analyze_experiment_from_csv failed: {e}")


@mcp.tool()
def analyze_retention_from_csv(
    file_path: str,
    period_col: str,
    value_col: str,
    campaign_level: Literal["S", "M"] = "S",
) -> str:
    """Run retention cohort analysis from a CSV of periods and rates or counts.

    Accepts retention rates (0.0-1.0) or active user counts per period
    (counts are auto-normalized against the first period).

    Args:
        file_path: Path to CSV with one row per period
        period_col: Column holding the period label (e.g. week_0, week_1)
        value_col: Column holding retention rate or active user count
        campaign_level: Intervention budget level, S or M
    """
    try:
        return _ok(datasource.analyze_retention_from_csv(
            file_path, period_col, value_col, campaign_level,
        ))
    except Exception as e:
        return _err(f"analyze_retention_from_csv failed: {e}")


@mcp.tool()
def summarize_segments_from_csv(
    file_path: str,
    segment_col: str,
    value_col: str,
) -> str:
    """Per-segment statistics (count, sum, mean, min, max, share) from raw CSV rows.

    Useful for segmented balance or spend analysis, e.g. loyalty point
    balances or voucher redemption value by user segment.

    Args:
        file_path: Path to CSV with one row per user or transaction
        segment_col: Column holding the segment label
        value_col: Numeric column to aggregate
    """
    try:
        return _ok(datasource.summarize_segments_from_csv(
            file_path, segment_col, value_col,
        ))
    except Exception as e:
        return _err(f"summarize_segments_from_csv failed: {e}")


@mcp.tool()
def analyze_experiment_from_bigquery(
    sql: str,
    group_col: str,
    converted_col: str,
    project: str | None = None,
    control_label: str = "control",
    treatment_label: str = "treatment",
    metric_name: str = "conversion",
) -> str:
    """Run an A/B test analysis on the result of a BigQuery SELECT query.

    Requires: pip install "growth-mcp[bigquery]" and Google ADC auth.
    The query must return 1 row per user with a group column and a
    conversion flag column. Read-only: only SELECT/WITH queries allowed.

    Args:
        sql: SELECT query returning 1 row per user
        group_col: Result column holding the experiment group label
        converted_col: Result column holding conversion flag (1/0, true/false)
        project: Optional GCP project ID (defaults to ADC project)
        control_label: Value marking the control group
        treatment_label: Value marking the treatment group
        metric_name: Metric name for reporting
    """
    try:
        return _ok(bigquery_source.analyze_experiment_from_bigquery(
            sql, group_col, converted_col, project,
            control_label, treatment_label, metric_name,
        ))
    except Exception as e:
        return _err(f"analyze_experiment_from_bigquery failed: {e}")


@mcp.tool()
def analyze_retention_from_bigquery(
    sql: str,
    period_col: str,
    value_col: str,
    project: str | None = None,
    campaign_level: Literal["S", "M"] = "S",
) -> str:
    """Run retention cohort analysis on a BigQuery query result.

    Requires: pip install "growth-mcp[bigquery]" and Google ADC auth.
    The query must return 1 row per period with a period label and a
    retention rate (0-1) or active user count (auto-normalized).

    Args:
        sql: SELECT query returning 1 row per period
        period_col: Result column holding the period label
        value_col: Result column holding retention rate or user count
        project: Optional GCP project ID
        campaign_level: Intervention budget level, S or M
    """
    try:
        return _ok(bigquery_source.analyze_retention_from_bigquery(
            sql, period_col, value_col, project, campaign_level,
        ))
    except Exception as e:
        return _err(f"analyze_retention_from_bigquery failed: {e}")


@mcp.tool()
def summarize_segments_from_bigquery(
    sql: str,
    segment_col: str,
    value_col: str,
    project: str | None = None,
) -> str:
    """Per-segment statistics on a BigQuery query result.

    Requires: pip install "growth-mcp[bigquery]" and Google ADC auth.
    Useful for segmented balance or spend analysis on warehouse data.

    Args:
        sql: SELECT query returning 1 row per user or transaction
        segment_col: Result column holding the segment label
        value_col: Numeric result column to aggregate
        project: Optional GCP project ID
    """
    try:
        return _ok(bigquery_source.summarize_segments_from_bigquery(
            sql, segment_col, value_col, project,
        ))
    except Exception as e:
        return _err(f"summarize_segments_from_bigquery failed: {e}")


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
def optimize_voucher(
    avg_order_value_vnd: int,
    target_conversion_lift_pct: float,
    budget_per_user_vnd: int,
    voucher_type: Literal["fixed", "percentage"] = "fixed",
) -> str:
    """Design an optimized voucher ladder with tiered thresholds and abuse risk assessment.

    Use this when you have concrete numbers (AOV, budget per user, target lift).
    Use suggest_voucher instead when you only know the segment.

    Args:
        avg_order_value_vnd: Current average order value in VND
        target_conversion_lift_pct: Target conversion lift in percent (e.g. 20 = +20%)
        budget_per_user_vnd: Maximum budget per user in VND
        voucher_type: "fixed" (VND cashback) or "percentage" (% discount, capped at 25%)
    """
    try:
        result = voucher.optimize_voucher(
            avg_order_value_vnd, target_conversion_lift_pct,
            budget_per_user_vnd, voucher_type,
        )
        return _ok(result)
    except Exception as e:
        return _err(f"optimize_voucher failed: {e}")


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


@mcp.tool()
def monitor_campaign(run_days: float, current_reach: int,
                     current_redemptions: int, total_vouchers: int,
                     total_budget: float = 0.0,
                     planned_days: float = 7.0,
                     target_reach: float = 0) -> str:
    """Monitor an ongoing campaign — assess health and recommend real-time adjustments.

    Tracks reach pace, redemption rate, budget burn, and voucher exhaustion.
    Returns critical/warning/info alerts and prioritized actions.

    Args:
        run_days: Days the campaign has been running
        current_reach: Number of users reached so far
        current_redemptions: Number of redemptions so far
        total_vouchers: Total vouchers allocated for the campaign
        total_budget: Total campaign budget in VND (0 if unknown)
        planned_days: Planned campaign duration in days
        target_reach: Expected total reach (0 = auto-detect)
    """
    result = monitor.assess_campaign(
        run_days, current_reach, current_redemptions,
        total_vouchers, total_budget, planned_days, target_reach
    )
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def analyze_segment(segment_type: str, segment_size: int = 0,
                    current_retention: float = 0.0,
                    current_redemption_rate: float = 0.0,
                    compare_segments: str = "") -> str:
    """Analyze a user segment — profile, performance vs benchmarks, and targeting recommendations.

    Compares current segment metrics against fintech benchmarks and recommends
    the best mechanic, channel, and strategy for that segment.

    Supported segments: new_user, active, lapsed, churned, high_spender, voucher_hunter

    Args:
        segment_type: Segment type (new_user, active, lapsed, churned, high_spender, voucher_hunter)
        segment_size: Current segment size
        current_retention: Current D7 retention (0-1, e.g. 0.3 for 30%)
        current_redemption_rate: Current campaign redemption rate (0-1, e.g. 0.2 for 20%)
        compare_segments: Optional comma-separated segments to compare against
    """
    result = segment.analyze_segment(
        segment_type, segment_size, current_retention,
        current_redemption_rate, compare_segments
    )
    return json.dumps(result, indent=2, ensure_ascii=False)


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
