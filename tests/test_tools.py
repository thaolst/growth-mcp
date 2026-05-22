"""Tests for growth_mcp tools."""

import json
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from growth_mcp.tools import campaign, retention, experiment


# ===========================================================================
# campaign.design_campaign
# ===========================================================================

class TestDesignCampaign:
    def test_valid_level_s(self):
        r = campaign.design_campaign("S", "increase MAU", "new users")
        assert r["level"] == "S"
        assert "channels" in r
        assert "error" not in r

    def test_valid_level_m(self):
        r = campaign.design_campaign("M", "reactivate lapsed", "inactive >30d")
        assert r["level"] == "M"

    def test_valid_level_l(self):
        r = campaign.design_campaign("L", "brand awareness", "all users")
        assert r["level"] == "L"

    def test_lowercase_level_normalised(self):
        r = campaign.design_campaign("s", "objective", "segment")
        assert r["level"] == "S"
        assert "error" not in r

    def test_invalid_level_returns_error(self):
        r = campaign.design_campaign("XL", "objective", "segment")
        assert "error" in r

    def test_custom_channels_used(self):
        r = campaign.design_campaign("S", "obj", "seg", channels=["email", "sms"])
        assert r["channels"] == ["email", "sms"]

    def test_default_channels_used_when_none(self):
        r = campaign.design_campaign("S", "obj", "seg")
        assert r["channels"] == campaign.CAMPAIGN_LEVELS["S"]["channels"]

    def test_custom_budget_used(self):
        r = campaign.design_campaign("M", "obj", "seg", budget="80M VND")
        assert r["budget"] == "80M VND"


# ===========================================================================
# campaign.suggest_voucher
# ===========================================================================

class TestSuggestVoucher:
    def test_new_user_segment(self):
        r = campaign.suggest_voucher("new_user", "first order")
        assert r["segment"] == "new_user"
        assert "error" not in r
        assert "suggested_voucher" in r

    def test_lapsed_segment(self):
        r = campaign.suggest_voucher("lapsed", "win back")
        assert r["suggested_voucher"]["type"] == "fixed_discount"

    def test_high_spender_segment(self):
        r = campaign.suggest_voucher("high_spender", "upsell")
        assert "cashback" in r["suggested_voucher"]["type"] or "free" in r["suggested_voucher"]["type"]

    def test_unknown_segment_returns_error(self):
        r = campaign.suggest_voucher("vip_whale", "objective")
        assert "error" in r
        assert "new_user" in r["error"]  # hint at valid options

    def test_invalid_budget_level_returns_error(self):
        r = campaign.suggest_voucher("active", "obj", budget_level="XL")
        assert "error" in r

    def test_segment_with_spaces_normalised(self):
        r = campaign.suggest_voucher("new user", "first order")
        assert "error" not in r


# ===========================================================================
# retention.analyze_cohort
# ===========================================================================

class TestAnalyzeCohort:
    COHORT = {"week_0": 1.0, "week_1": 0.68, "week_2": 0.45, "week_3": 0.32}

    def test_basic_cohort(self):
        r = retention.analyze_cohort(self.COHORT)
        assert "error" not in r
        assert r["cohort_summary"]["periods"] == 4
        assert "biggest_drop" in r["cohort_summary"]

    def test_biggest_drop_is_correct(self):
        r = retention.analyze_cohort(self.COHORT)
        # week_0→week_1: (1.0-0.68)/1.0 = 32%
        # week_1→week_2: (0.68-0.45)/0.68 = 33.8%  ← biggest
        # week_2→week_3: (0.45-0.32)/0.45 = 28.9%
        assert r["cohort_summary"]["biggest_drop"]["period"] == "week_1->week_2"

    def test_latest_retention_correct(self):
        r = retention.analyze_cohort(self.COHORT)
        assert r["cohort_summary"]["latest_retention_pct"] == 32.0

    def test_only_one_period_returns_error(self):
        r = retention.analyze_cohort({"week_0": 1.0})
        assert "error" in r

    def test_empty_dict_returns_error(self):
        r = retention.analyze_cohort({})
        assert "error" in r

    def test_zero_first_period_skipped_gracefully(self):
        data = {"week_0": 0.0, "week_1": 0.5, "week_2": 0.3}
        r = retention.analyze_cohort(data)
        # week_0 is 0, no drop computable from it; week_1→week_2 drop should still work
        assert "error" not in r

    def test_campaign_level_m_gives_different_interventions(self):
        r_s = retention.analyze_cohort(self.COHORT, "S")
        r_m = retention.analyze_cohort(self.COHORT, "M")
        assert r_s["interventions"] != r_m["interventions"]

    def test_unknown_campaign_level_falls_back_to_s(self):
        r = retention.analyze_cohort(self.COHORT, "Z")
        assert r["interventions"] == retention.INTERVENTIONS["S"]


# ===========================================================================
# retention.predict_churn
# ===========================================================================

class TestPredictChurn:
    def test_high_risk(self):
        r = retention.predict_churn(90, 5000)
        assert r["churn_risk"] == "high"

    def test_medium_risk(self):
        r = retention.predict_churn(45, 3000)
        assert r["churn_risk"] == "medium"

    def test_low_risk(self):
        r = retention.predict_churn(20, 1000)
        assert r["churn_risk"] == "low"

    def test_healthy(self):
        r = retention.predict_churn(5, 10000)
        assert r["churn_risk"] == "healthy"

    def test_points_leverage_shown_when_balance_positive(self):
        r = retention.predict_churn(45, 1000, avg_points_balance=500)
        assert r["points_leverage"]["has_unused_points"] is True
        assert "500" in r["points_leverage"]["message"]

    def test_points_leverage_absent_when_zero(self):
        r = retention.predict_churn(45, 1000, avg_points_balance=0)
        assert r["points_leverage"]["has_unused_points"] is False

    def test_redemption_rate_reflected_in_output(self):
        r = retention.predict_churn(20, 1000, redemption_rate=0.35)
        assert r["redemption_rate_pct"] == 35.0


# ===========================================================================
# experiment.analyze_test
# ===========================================================================

class TestAnalyzeTest:
    def test_significant_treatment_win(self):
        # 150/1000 vs 120/1000 — clear treatment win
        r = experiment.analyze_test(150, 120, 1000, 1000)
        # relative lift is negative (treatment < control), so control wins
        assert r["statistics"]["significant_at_95"] is True

    def test_treatment_wins(self):
        r = experiment.analyze_test(100, 160, 1000, 1000)
        assert r["verdict"] == "Treatment wins"
        assert r["lift"]["relative_pct"] > 0

    def test_not_conclusive_small_difference(self):
        # tiny difference → not conclusive
        r = experiment.analyze_test(100, 101, 1000, 1000)
        assert r["statistics"]["significant_at_95"] is False
        assert "Not conclusive" in r["verdict"]

    def test_rates_computed_correctly(self):
        r = experiment.analyze_test(50, 80, 1000, 1000)
        assert r["control"]["rate_pct"] == 5.0
        assert r["treatment"]["rate_pct"] == 8.0

    def test_zero_control_metric(self):
        r = experiment.analyze_test(0, 10, 1000, 1000)
        assert "error" not in r
        assert r["lift"]["relative_pct"] == 0  # no baseline to compare

    def test_metric_name_propagated(self):
        r = experiment.analyze_test(100, 120, 1000, 1000, metric_name="checkout")
        assert r["metric"] == "checkout"


# ===========================================================================
# experiment.calculate_sample_size
# ===========================================================================

class TestCalculateSampleSize:
    def test_baseline_5pct_mde_10pct_relative(self):
        # baseline=5%, relative MDE=10% means lift from 5% → 5.5% (very small absolute diff)
        # Verified against scipy.stats: n ≈ 31234 per variant
        r = experiment.calculate_sample_size(0.05, 0.10)
        assert 30000 <= r["required_per_variant"] <= 33000

    def test_total_is_double_per_variant(self):
        r = experiment.calculate_sample_size(0.05, 0.10)
        assert r["total_required"] == math.ceil(r["required_per_variant"] * 2)

    def test_higher_power_needs_more_users(self):
        r80 = experiment.calculate_sample_size(0.05, 0.10, power=0.80)
        r90 = experiment.calculate_sample_size(0.05, 0.10, power=0.90)
        assert r90["required_per_variant"] > r80["required_per_variant"]

    def test_stricter_significance_needs_more_users(self):
        r05 = experiment.calculate_sample_size(0.05, 0.10, significance=0.05)
        r01 = experiment.calculate_sample_size(0.05, 0.10, significance=0.01)
        assert r01["required_per_variant"] > r05["required_per_variant"]

    def test_larger_mde_needs_fewer_users(self):
        r10 = experiment.calculate_sample_size(0.05, 0.10)
        r20 = experiment.calculate_sample_size(0.05, 0.20)
        assert r20["required_per_variant"] < r10["required_per_variant"]

    def test_arbitrary_significance_0_01(self):
        # Should work without error — uses proper inverse normal CDF
        r = experiment.calculate_sample_size(0.10, 0.05, significance=0.01, power=0.90)
        assert r["required_per_variant"] > 0
        assert r["assumptions"]["significance_level"] == 0.01

    def test_z_values_exposed_in_assumptions(self):
        r = experiment.calculate_sample_size(0.05, 0.10)
        assert "z_alpha" in r["assumptions"]
        assert "z_beta" in r["assumptions"]
        # At α=0.05, two-tailed: z_alpha ≈ 1.96
        assert abs(r["assumptions"]["z_alpha"] - 1.96) < 0.01

    def test_rate_fields_in_percent(self):
        r = experiment.calculate_sample_size(0.05, 0.10)
        assert r["baseline_rate_pct"] == 5.0
        assert r["expected_treatment_rate_pct"] == pytest.approx(5.5, abs=0.1)


# ---------------------------------------------------------------------------
# Import pytest for approx
# ---------------------------------------------------------------------------
import pytest
