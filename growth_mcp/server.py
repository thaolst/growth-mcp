"""Growth MCP Server — campaign design, retention analysis, churn prediction."""

import json
from mcp.server import FastMCP

from growth_mcp.tools import campaign, retention, experiment

mcp = FastMCP("growth-mcp", instructions="Growth marketing tools for campaign design, retention analysis, and A/B testing")


@mcp.tool()
def design_campaign(level: str, objective: str, target_segment: str,
                    channels: str | None = None,
                    budget: str | None = None) -> str:
    """Design a growth campaign brief based on level (S/M/L) and constraints.

    Args:
        level: Campaign level — S (small, in-app only), M (medium, some paid), or L (large, full funnel)
        objective: What the campaign aims to achieve
        target_segment: Who the campaign targets
        channels: Optional comma-separated channel list
        budget: Optional budget estimate
    """
    channel_list = channels.split(",") if channels else None
    result = campaign.design_campaign(level, objective, target_segment, channel_list, budget)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def suggest_voucher(segment: str, objective: str,
                    budget_level: str = "S") -> str:
    """Suggest voucher design by user segment.

    Args:
        segment: User segment type (new_user, active, lapsed, high_spender)
        objective: Campaign objective
        budget_level: S (cheap) or M (moderate budget)
    """
    result = campaign.suggest_voucher(segment, objective, budget_level)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def analyze_retention(cohort_data: str, campaign_level: str = "S") -> str:
    """Analyze retention cohort data and identify churn points.

    Args:
        cohort_data: JSON string of retention data
                     e.g. '{"week_0": 1.0, "week_1": 0.68, "week_2": 0.45, "week_3": 0.32}'
        campaign_level: Campaign level for suggesting feasible interventions
    """
    data = json.loads(cohort_data)
    result = retention.analyze_cohort(data, campaign_level)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def predict_churn_risk(days_since_last_active: float, total_users: int,
                       avg_points_balance: float = 0,
                       redemption_rate: float = 0.0) -> str:
    """Predict churn risk and recommend re-engagement strategy.

    Args:
        days_since_last_active: Average days since last user activity
        total_users: Number of users in the segment
        avg_points_balance: Average unused loyalty points
        redemption_rate: Percentage of users who redeemed recently
    """
    result = retention.predict_churn(days_since_last_active, total_users,
                                     avg_points_balance, redemption_rate)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def analyze_experiment(control_metric: float, treatment_metric: float,
                       control_sample: int, treatment_sample: int,
                       metric_name: str = "conversion") -> str:
    """Analyze A/B test results with statistical significance.

    Args:
        control_metric: Control count (not rate)
        treatment_metric: Treatment count (not rate)
        control_sample: Control sample size
        treatment_sample: Treatment sample size
        metric_name: Name of the metric
    """
    result = experiment.analyze_test(control_metric, treatment_metric,
                                     control_sample, treatment_sample,
                                     metric_name)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def estimate_sample_size(baseline_rate: float,
                         minimum_detectable_effect: float) -> str:
    """Calculate required sample size for an A/B test.

    Args:
        baseline_rate: Current conversion rate (0-1, e.g. 0.05 for 5%)
        minimum_detectable_effect: Minimum lift to detect (0-1, e.g. 0.1 for 10%)
    """
    result = experiment.calculate_sample_size(baseline_rate, minimum_detectable_effect)
    return json.dumps(result, indent=2, ensure_ascii=False)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
