"""Experiment analysis tools."""

import math


def _erf(x: float) -> float:
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    p = 0.3275911
    sign = 1 if x >= 0 else -1
    x = abs(x)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t) * math.exp(-x * x)
    return sign * y


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + _erf(x / math.sqrt(2)))


def _rational_ppf(t: float) -> float:
    c = [2.515517, 0.802853, 0.010328]
    d = [1.432788, 0.189269, 0.001308]
    return t - (c[0] + c[1] * t + c[2] * t * t) / (1.0 + d[0] * t + d[1] * t * t + d[2] * t ** 3)


def _normal_ppf(p: float) -> float:
    if p <= 0 or p >= 1:
        raise ValueError(f"p must be in (0, 1), got {p}")
    if p < 0.5:
        return -_rational_ppf(math.sqrt(-2.0 * math.log(p)))
    return _rational_ppf(math.sqrt(-2.0 * math.log(1.0 - p)))


def analyze_test(
    control_metric: float,
    treatment_metric: float,
    control_sample: int,
    treatment_sample: int,
    metric_name: str = "conversion",
) -> dict:
    """Analyze A/B test results using a two-proportion z-test."""
    # --- Input validation ---
    if 0 < control_metric <= 1 and 0 < treatment_metric <= 1:
        return {
            "error": (
                "control_metric and treatment_metric look like rates (0–1). "
                "Pass raw counts instead — e.g. 120 conversions, not 0.12."
            )
        }
    if control_metric < 0 or treatment_metric < 0:
        return {"error": "control_metric and treatment_metric must be >= 0."}
    if control_sample <= 0 or treatment_sample <= 0:
        return {"error": "Sample sizes must be positive integers."}
    if control_metric > control_sample:
        return {"error": f"control_metric ({control_metric}) cannot exceed control_sample ({control_sample})."}
    if treatment_metric > treatment_sample:
        return {"error": f"treatment_metric ({treatment_metric}) cannot exceed treatment_sample ({treatment_sample})."}

    p_control = control_metric / control_sample if control_sample else 0.0
    p_treatment = treatment_metric / treatment_sample if treatment_sample else 0.0
    total = control_sample + treatment_sample
    p_pooled = (control_metric + treatment_metric) / total if total else 0.0

    absolute_lift = treatment_metric - control_metric
    relative_lift = (absolute_lift / control_metric * 100) if control_metric else 0.0

    if p_pooled > 0 and (1 - p_pooled) > 0 and control_sample and treatment_sample:
        se = math.sqrt(p_pooled * (1 - p_pooled) * (1 / control_sample + 1 / treatment_sample))
        z = (p_treatment - p_control) / se if se > 0 else 0.0
    else:
        se, z = 0.0, 0.0

    p_value = round(2 * (1 - _normal_cdf(abs(z))), 4) if z != 0 else 1.0
    significant = p_value < 0.05

    if significant and relative_lift > 0:
        verdict, next_action = "Treatment wins", "Launch treatment variant"
    elif significant and relative_lift < 0:
        verdict, next_action = "Control wins", "Keep control, iterate on treatment"
    else:
        verdict, next_action = "Not conclusive — run longer or increase sample size", "Increase sample size and re-run"

    return {
        "metric": metric_name,
        "control": {"value": round(control_metric, 2), "sample": control_sample, "rate_pct": round(p_control * 100, 2)},
        "treatment": {"value": round(treatment_metric, 2), "sample": treatment_sample, "rate_pct": round(p_treatment * 100, 2)},
        "lift": {"absolute": round(absolute_lift, 2), "relative_pct": round(relative_lift, 2)},
        "statistics": {"z_score": round(z, 4), "p_value": p_value, "significant_at_95": significant},
        "verdict": verdict,
        "next_steps": [
            next_action,
            "Segment analysis to check for Simpson's paradox",
            "Calculate novelty effect: compare new vs returning users",
        ],
        "prompt_reference": "https://github.com/thaolst/ai-growth-prompts/tree/main/07-experiment-design",
    }


def calculate_sample_size(
    baseline_rate: float,
    minimum_detectable_effect: float,
    significance: float = 0.05,
    power: float = 0.80,
) -> dict:
    """Estimate required sample size per variant."""
    if not (0.0 < baseline_rate < 1.0):
        return {"error": "baseline_rate must be between 0 and 1 exclusive (e.g. 0.05 for 5%)."}
    if not (0.0 < minimum_detectable_effect < 1.0):
        return {"error": "minimum_detectable_effect must be between 0 and 1 exclusive (e.g. 0.10 for 10% lift)."}
    if not (0.0 < significance < 0.5):
        return {"error": "significance must be between 0 and 0.5 (e.g. 0.05)."}
    if not (0.5 < power < 1.0):
        return {"error": "power must be between 0.5 and 1.0 (e.g. 0.80)."}

    z_alpha = _normal_ppf(1.0 - significance / 2)
    z_beta = _normal_ppf(power)

    p1 = baseline_rate
    p2 = min(baseline_rate * (1 + minimum_detectable_effect), 1.0)
    p_bar = (p1 + p2) / 2

    numerator = (
        z_alpha * math.sqrt(2 * p_bar * (1 - p_bar))
        + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    denominator = (p2 - p1) ** 2
    per_variant = math.ceil(numerator / denominator)

    return {
        "baseline_rate_pct": round(baseline_rate * 100, 2),
        "expected_treatment_rate_pct": round(p2 * 100, 2),
        "mde_relative_pct": round(minimum_detectable_effect * 100, 1),
        "required_per_variant": per_variant,
        "total_required": per_variant * 2,
        "assumptions": {
            "significance_level": significance,
            "statistical_power": power,
            "test_type": "two-tailed",
            "z_alpha": round(z_alpha, 4),
            "z_beta": round(z_beta, 4),
        },
    }
