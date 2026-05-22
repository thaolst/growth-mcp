"""Experiment analysis tools."""

import math


def analyze_test(control_metric: float, treatment_metric: float,
                 control_sample: int, treatment_sample: int,
                 metric_name: str = "conversion") -> dict:
    """Analyze A/B test results.

    Args:
        control_metric: Control group metric value
        treatment_metric: Treatment group metric value
        control_sample: Control group sample size
        treatment_sample: Treatment group sample size
        metric_name: Name of the metric being measured
    """
    absolute_lift = treatment_metric - control_metric
    relative_lift = (absolute_lift / control_metric * 100) if control_metric else 0

    # Simple z-test approximation for significance
    p_control = control_metric / control_sample if control_sample else 0
    p_treatment = treatment_metric / treatment_sample if treatment_sample else 0
    p_pooled = (control_metric + treatment_metric) / (control_sample + treatment_sample) if (control_sample + treatment_sample) else 0

    if p_pooled > 0 and (1 - p_pooled) > 0:
        se = math.sqrt(p_pooled * (1 - p_pooled) * (1/control_sample + 1/treatment_sample))
        z = (p_treatment - p_control) / se if se > 0 else 0
    else:
        se = 0
        z = 0

    # p-value approximation (two-tailed)
    p_value = round(2 * (1 - _normal_cdf(abs(z))), 4) if z != 0 else 1.0
    significant = p_value < 0.05

    return {
        "metric": metric_name,
        "control": {
            "value": round(control_metric, 2),
            "sample": control_sample,
            "rate": round(p_control * 100, 2) if control_sample else 0
        },
        "treatment": {
            "value": round(treatment_metric, 2),
            "sample": treatment_sample,
            "rate": round(p_treatment * 100, 2) if treatment_sample else 0
        },
        "lift": {
            "absolute": round(absolute_lift, 2),
            "relative_pct": round(relative_lift, 2)
        },
        "statistics": {
            "z_score": round(z, 4),
            "p_value": p_value,
            "significant_at_95": significant
        },
        "verdict": "Treatment wins" if significant and relative_lift > 0 else (
            "Control wins" if significant and relative_lift < 0 else
            "Not conclusive — run longer or increase sample size"
        ),
        "next_steps": [
            "Launch treatment" if significant and relative_lift > 0 else
            "Keep control, iterate on treatment" if significant else
            "Increase sample size and re-run",
            "Segment analysis to check for Simpson's paradox",
            "Calculate novelty effect: compare new vs returning users"
        ],
        "prompt_reference": "https://github.com/thaolst/ai-growth-prompts/tree/main/07-experiment-design"
    }


def _normal_cdf(x: float) -> float:
    """Approximate normal CDF using the error function approximation."""
    return 0.5 * (1 + _erf(x / math.sqrt(2)))


def _erf(x: float) -> float:
    """Approximation of the error function."""
    a1 = 0.254829592
    a2 = -0.284496736
    a3 = 1.421413741
    a4 = -1.453152027
    a5 = 1.061405429
    p = 0.3275911

    sign = 1 if x >= 0 else -1
    x = abs(x)

    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)

    return sign * y


def calculate_sample_size(baseline_rate: float,
                          minimum_detectable_effect: float,
                          significance: float = 0.05,
                          power: float = 0.8) -> dict:
    """Estimate required sample size for an experiment.

    Args:
        baseline_rate: Current conversion rate (0-1)
        minimum_detectable_effect: Minimum lift to detect (0-1)
        significance: Statistical significance level (default 0.05)
        power: Statistical power (default 0.8)
    """
    z_alpha = 1.96 if significance == 0.05 else 2.58
    z_beta = 0.84 if power == 0.8 else 1.28

    p1 = baseline_rate
    p2 = baseline_rate * (1 + minimum_detectable_effect)
    p_bar = (p1 + p2) / 2

    n = (z_alpha * math.sqrt(2 * p_bar * (1 - p_bar)) +
         z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 / (p2 - p1) ** 2

    return {
        "baseline_rate": baseline_rate,
        "expected_treatment_rate": round(p2, 4),
        "mde": minimum_detectable_effect,
        "required_per_variant": math.ceil(n),
        "total_required": math.ceil(n * 2),
        "assumptions": {
            "significance_level": significance,
            "statistical_power": power,
            "test_type": "two-tailed"
        }
    }
