"""Tests for new growth tools: suggest_channel_mix, forecast_cohort, segment_users."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from growth_mcp.tools.growth import suggest_channel_mix, forecast_cohort, segment_users


class TestSuggestChannelMix:
    def test_retention_budget_m(self):
        r = suggest_channel_mix("retention", "M")
        assert "error" not in r
        assert r["budget_level"] == "M"
        assert r["budget_split"]["owned_channels_pct"] == 60
        assert r["budget_split"]["paid_channels_pct"] == 40

    def test_acquisition_budget_s(self):
        r = suggest_channel_mix("acquisition", "S")
        assert "error" not in r
        assert r["budget_split"]["paid_channels_pct"] == 0

    def test_reactivation_budget_l(self):
        r = suggest_channel_mix("reactivation", "L")
        assert "error" not in r
        assert r["budget_split"]["owned_channels_pct"] == 40

    def test_available_channels_filters(self):
        r = suggest_channel_mix("retention", "M", ["push", "email"])
        assert "error" not in r
        # primary should only include matched channels
        for ch in r["recommended_channels"]["primary"]:
            assert any(a in ch for a in ["push", "email"])

    def test_unknown_objective_returns_error(self):
        r = suggest_channel_mix("unknown_obj", "M")
        assert "error" in r

    def test_invalid_budget_level_returns_error(self):
        r = suggest_channel_mix("retention", "XL")
        assert "error" in r

    def test_lowercase_objective_normalised(self):
        r = suggest_channel_mix("RETENTION", "M")
        assert "error" not in r

    def test_all_objectives_work(self):
        for obj in ["acquisition", "activation", "retention", "reactivation", "monetization"]:
            r = suggest_channel_mix(obj, "M")
            assert "error" not in r, f"Failed for objective: {obj}"

    def test_strategy_note_present(self):
        r = suggest_channel_mix("retention", "S")
        assert "strategy_note" in r
        assert len(r["strategy_note"]) > 0


class TestForecastCohort:
    SAMPLE = {"D1": 0.65, "D7": 0.42, "D14": 0.30, "D30": 0.22}

    def test_basic_forecast(self):
        r = forecast_cohort(self.SAMPLE)
        assert "error" not in r
        assert "forecast" in r
        assert len(r["forecast"]) == 3

    def test_custom_forecast_periods(self):
        r = forecast_cohort(self.SAMPLE, forecast_periods=5)
        assert len(r["forecast"]) == 5

    def test_sorted_correctly(self):
        r = forecast_cohort(self.SAMPLE)
        keys = list(r["historical_sorted"].keys())
        assert keys == ["D1", "D7", "D14", "D30"]

    def test_drop_rates_present(self):
        r = forecast_cohort(self.SAMPLE)
        assert "drop_rates" in r
        assert len(r["drop_rates"]) == 3

    def test_steepest_drop_identified(self):
        r = forecast_cohort(self.SAMPLE)
        assert r["steepest_drop"]["period"] is not None
        assert r["steepest_drop"]["drop"] is not None

    def test_forecasted_values_in_range(self):
        r = forecast_cohort(self.SAMPLE)
        for v in r["forecast"].values():
            assert 0.0 <= v <= 1.0

    def test_too_few_points_returns_error(self):
        r = forecast_cohort({"D1": 0.6, "D7": 0.4})
        assert "error" in r

    def test_invalid_retention_value_returns_error(self):
        r = forecast_cohort({"D1": 1.5, "D7": 0.4, "D14": 0.3})
        assert "error" in r

    def test_confidence_low_with_few_points(self):
        r = forecast_cohort({"D1": 0.6, "D7": 0.4, "D14": 0.3})
        assert r["confidence"] == "low"

    def test_confidence_medium_with_more_points(self):
        data = {"D1": 0.65, "D7": 0.45, "D14": 0.32, "D30": 0.22, "D60": 0.15}
        r = forecast_cohort(data)
        assert r["confidence"] == "medium"


class TestSegmentUsers:
    def test_reactivation_has_segments(self):
        r = segment_users("reactivation")
        assert "error" not in r
        assert len(r["segments"]) >= 2

    def test_churned_with_balance_first_in_reactivation(self):
        r = segment_users("reactivation")
        assert r["segments"][0]["name"] == "Churned with balance"

    def test_retention_has_at_risk_segment(self):
        r = segment_users("retention")
        names = [s["name"] for s in r["segments"]]
        assert any("risk" in n.lower() or "at-risk" in n.lower() for n in names)

    def test_context_propagated(self):
        r = segment_users("reactivation", context="fintech mobile payment")
        assert r["context"] == "fintech mobile payment"

    def test_unknown_objective_returns_error(self):
        r = segment_users("unknown_objective")
        assert "error" in r

    def test_all_objectives_work(self):
        for obj in ["acquisition", "retention", "reactivation", "monetization"]:
            r = segment_users(obj)
            assert "error" not in r, f"Failed for: {obj}"

    def test_primary_signal_present(self):
        r = segment_users("retention")
        assert "primary_signal" in r
        assert len(r["primary_signal"]) > 0

    def test_next_steps_present(self):
        r = segment_users("monetization")
        assert "next_steps" in r
        assert len(r["next_steps"]) >= 2

    def test_each_segment_has_required_fields(self):
        r = segment_users("retention")
        for seg in r["segments"]:
            assert "name" in seg
            assert "definition" in seg
            assert "approach" in seg
