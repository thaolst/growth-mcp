"""Tests for growth_mcp tools."""

import json
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from growth_mcp.tools import campaign, retention, experiment, voucher, datasource, bigquery_source, mixpanel_source


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


# ===========================================================================
# voucher.optimize_voucher
# ===========================================================================

class TestOptimizeVoucher:
    def test_fixed_ladder(self):
        r = voucher.optimize_voucher(150000, 20, 15000, "fixed")
        assert "error" not in r
        assert len(r["voucher_ladder"]) == 3
        assert r["voucher_ladder"][0]["discount_vnd"] == 7500
        assert r["abuse_risk"] == "MEDIUM"

    def test_percentage_capped(self):
        r = voucher.optimize_voucher(150000, 100, 10000, "percentage")
        assert "error" not in r
        for tier in r["voucher_ladder"]:
            pct = float(tier["discount"].rstrip("%"))
            assert pct <= voucher.MAX_PCT_DISCOUNT

    def test_low_risk(self):
        r = voucher.optimize_voucher(1000000, 10, 50000, "fixed")
        assert r["abuse_risk"] == "LOW"

    def test_high_risk(self):
        r = voucher.optimize_voucher(100000, 10, 20000, "fixed")
        assert r["abuse_risk"] == "HIGH"

    def test_invalid_type(self):
        r = voucher.optimize_voucher(150000, 20, 15000, "bogus")
        assert "error" in r

    def test_invalid_aov(self):
        r = voucher.optimize_voucher(0, 20, 15000)
        assert "error" in r


# ===========================================================================
# datasource (CSV data layer)
# ===========================================================================

import tempfile


def _write_csv(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    f.write(content)
    f.close()
    return f.name


class TestInspectCsv:
    def test_basic(self):
        p = _write_csv("segment,balance\nnew,100\nactive,250\nactive,300\n")
        r = datasource.inspect_csv(p)
        assert r["rows"] == 3
        assert r["columns"]["balance"]["type"] == "numeric"
        assert r["columns"]["segment"]["unique"] == 2

    def test_missing_file(self):
        r = datasource.inspect_csv("/nonexistent.csv")
        assert "error" in r

    def test_empty_data(self):
        p = _write_csv("a,b\n")
        r = datasource.inspect_csv(p)
        assert "error" in r


class TestExperimentFromCsv:
    def test_significant(self):
        rows = ["group,converted"]
        rows += ["control,1"] * 100 + ["control,0"] * 900
        rows += ["treatment,1"] * 150 + ["treatment,0"] * 850
        p = _write_csv("\n".join(rows) + "\n")
        r = datasource.analyze_experiment_from_csv(p, "group", "converted")
        assert "error" not in r
        assert r["data_source"]["control"]["sample"] == 1000
        assert r["data_source"]["treatment"]["conversions"] == 150

    def test_bad_labels(self):
        p = _write_csv("group,converted\nA,1\nB,0\n")
        r = datasource.analyze_experiment_from_csv(p, "group", "converted")
        assert "error" in r

    def test_missing_column(self):
        p = _write_csv("g,c\ncontrol,1\n")
        r = datasource.analyze_experiment_from_csv(p, "group", "converted")
        assert "error" in r


class TestRetentionFromCsv:
    def test_rates(self):
        p = _write_csv("period,rate\nweek_0,1.0\nweek_1,0.6\nweek_2,0.45\n")
        r = datasource.analyze_retention_from_csv(p, "period", "rate")
        assert "error" not in r
        assert r["data_source"]["normalized_from_counts"] is False

    def test_counts_normalized(self):
        p = _write_csv("period,users\nweek_0,1000\nweek_1,600\nweek_2,450\n")
        r = datasource.analyze_retention_from_csv(p, "period", "users")
        assert "error" not in r
        assert r["data_source"]["normalized_from_counts"] is True

    def test_too_few_periods(self):
        p = _write_csv("period,rate\nweek_0,1.0\n")
        r = datasource.analyze_retention_from_csv(p, "period", "rate")
        assert "error" in r


class TestSegmentsFromCsv:
    def test_basic(self):
        p = _write_csv(
            "segment,xu\nnew,100\nnew,200\nactive,500\nactive,700\nlapsed,50\n"
        )
        r = datasource.summarize_segments_from_csv(p, "segment", "xu")
        assert r["segment_count"] == 3
        assert r["segments"]["active"]["sum"] == 1200
        assert abs(sum(s["share_of_total"] for s in r["segments"].values()) - 1.0) < 0.01

    def test_no_usable_rows(self):
        p = _write_csv("segment,xu\n,abc\n")
        r = datasource.summarize_segments_from_csv(p, "segment", "xu")
        assert "error" in r


# ===========================================================================
# bigquery_source
# ===========================================================================

class TestBigQuerySqlGuardrail:
    def test_select_allowed(self):
        assert bigquery_source._validate_sql("SELECT * FROM t") is None
        assert bigquery_source._validate_sql("  WITH x AS (SELECT 1) SELECT * FROM x") is None

    def test_write_rejected(self):
        for sql in ["DELETE FROM t", "DROP TABLE t", "SELECT 1; DROP TABLE t",
                    "INSERT INTO t VALUES (1)", "update t set a=1"]:
            assert bigquery_source._validate_sql(sql) is not None


class TestBigQueryExperiment:
    def test_with_mocked_rows(self, monkeypatch):
        rows = (
            [{"grp": "control", "conv": 1}] * 100 + [{"grp": "control", "conv": 0}] * 900
            + [{"grp": "treatment", "conv": 1}] * 150 + [{"grp": "treatment", "conv": 0}] * 850
        )
        monkeypatch.setattr(bigquery_source, "_run_query", lambda sql, project=None: rows)
        r = bigquery_source.analyze_experiment_from_bigquery("SELECT 1", "grp", "conv")
        assert "error" not in r
        assert r["data_source"]["source"] == "bigquery"
        assert r["data_source"]["treatment"]["conversions"] == 150

    def test_missing_column(self, monkeypatch):
        monkeypatch.setattr(
            bigquery_source, "_run_query",
            lambda sql, project=None: [{"a": 1}],
        )
        r = bigquery_source.analyze_experiment_from_bigquery("SELECT 1", "grp", "conv")
        assert "error" in r

    def test_query_error_propagates(self, monkeypatch):
        monkeypatch.setattr(
            bigquery_source, "_run_query",
            lambda sql, project=None: {"error": "boom"},
        )
        r = bigquery_source.analyze_experiment_from_bigquery("SELECT 1", "grp", "conv")
        assert r == {"error": "boom"}


class TestBigQueryRetention:
    def test_counts_normalized(self, monkeypatch):
        rows = [
            {"period": "week_0", "users": 1000},
            {"period": "week_1", "users": 600},
            {"period": "week_2", "users": 450},
        ]
        monkeypatch.setattr(bigquery_source, "_run_query", lambda sql, project=None: rows)
        r = bigquery_source.analyze_retention_from_bigquery("SELECT 1", "period", "users")
        assert "error" not in r
        assert r["data_source"]["normalized_from_counts"] is True
        assert r["data_source"]["source"] == "bigquery"


class TestBigQuerySegments:
    def test_basic(self, monkeypatch):
        rows = [
            {"segment": "new", "xu": 100}, {"segment": "new", "xu": 200},
            {"segment": "active", "xu": 500}, {"segment": "active", "xu": 700},
        ]
        monkeypatch.setattr(bigquery_source, "_run_query", lambda sql, project=None: rows)
        r = bigquery_source.summarize_segments_from_bigquery("SELECT 1", "segment", "xu")
        assert r["segment_count"] == 2
        assert r["segments"]["active"]["sum"] == 1200
        assert r["source"] == "bigquery"


class TestBigQueryImportHint:
    def test_missing_dependency_hint(self):
        # google-cloud-bigquery không được cài trong môi trường test
        r = bigquery_source._run_query("SELECT 1")
        assert "error" in r
        assert "growth-mcp[bigquery]" in r["error"]


# ===========================================================================
# mixpanel_source
# ===========================================================================

def _mk_event(name, uid, **props):
    p = {"distinct_id": uid}
    p.update(props)
    return {"event": name, "properties": p}


class TestMixpanelDates:
    def test_valid(self):
        assert mixpanel_source._validate_dates("2026-05-01", "2026-05-31") is None

    def test_bad_format(self):
        assert "error" in mixpanel_source._validate_dates("01/05/2026", "2026-05-31")

    def test_reversed(self):
        assert "error" in mixpanel_source._validate_dates("2026-05-31", "2026-05-01")

    def test_too_long(self):
        assert "error" in mixpanel_source._validate_dates("2025-01-01", "2026-01-01")


class TestMixpanelAuth:
    def test_missing_secret_hint(self, monkeypatch):
        monkeypatch.delenv("MIXPANEL_API_SECRET", raising=False)
        r = mixpanel_source._export_events("exp", "2026-05-01", "2026-05-02")
        assert "error" in r
        assert "MIXPANEL_API_SECRET" in r["error"]


class TestMixpanelExperiment:
    def _patch_export(self, monkeypatch, exposures, conversions):
        def fake(event, from_date, to_date):
            if event == "exp_exposed":
                return exposures
            if event == "purchased":
                return conversions if conversions else {
                    "error": f"No '{event}' events found between {from_date} and {to_date}."
                }
            return {"error": "unexpected event"}
        monkeypatch.setattr(mixpanel_source, "_export_events", fake)

    def test_basic(self, monkeypatch):
        exposures = (
            [_mk_event("exp_exposed", f"c{i}", variant="control") for i in range(1000)]
            + [_mk_event("exp_exposed", f"t{i}", variant="treatment") for i in range(1000)]
        )
        conversions = (
            [_mk_event("purchased", f"c{i}") for i in range(100)]
            + [_mk_event("purchased", f"t{i}") for i in range(150)]
        )
        self._patch_export(monkeypatch, exposures, conversions)
        r = mixpanel_source.analyze_experiment_from_mixpanel(
            "exp_exposed", "purchased", "variant", "2026-05-01", "2026-05-31",
        )
        assert "error" not in r
        assert r["data_source"]["source"] == "mixpanel"
        assert r["data_source"]["control"]["conversions"] == 100
        assert r["data_source"]["treatment"]["conversions"] == 150
        assert r["data_source"]["unique_users"] == 2000

    def test_no_conversions_is_valid(self, monkeypatch):
        exposures = (
            [_mk_event("exp_exposed", f"c{i}", variant="control") for i in range(50)]
            + [_mk_event("exp_exposed", f"t{i}", variant="treatment") for i in range(50)]
        )
        self._patch_export(monkeypatch, exposures, [])
        r = mixpanel_source.analyze_experiment_from_mixpanel(
            "exp_exposed", "purchased", "variant", "2026-05-01", "2026-05-31",
        )
        assert "error" not in r
        assert r["data_source"]["control"]["conversions"] == 0

    def test_first_exposure_wins(self, monkeypatch):
        exposures = [
            _mk_event("exp_exposed", "u1", variant="control"),
            _mk_event("exp_exposed", "u1", variant="treatment"),
            _mk_event("exp_exposed", "u2", variant="treatment"),
        ]
        self._patch_export(monkeypatch, exposures, [])
        r = mixpanel_source.analyze_experiment_from_mixpanel(
            "exp_exposed", "purchased", "variant", "2026-05-01", "2026-05-31",
        )
        assert r["data_source"]["control"]["sample"] == 1
        assert r["data_source"]["treatment"]["sample"] == 1

    def test_missing_group_property(self, monkeypatch):
        exposures = [_mk_event("exp_exposed", "u1")]
        self._patch_export(monkeypatch, exposures, [])
        r = mixpanel_source.analyze_experiment_from_mixpanel(
            "exp_exposed", "purchased", "variant", "2026-05-01", "2026-05-31",
        )
        assert "error" in r


class TestMixpanelSegments:
    def test_basic(self, monkeypatch):
        events = (
            [_mk_event("voucher_redeemed", f"a{i}", segment="active", amount=500) for i in range(4)]
            + [_mk_event("voucher_redeemed", f"n{i}", segment="new", amount=100) for i in range(2)]
        )
        monkeypatch.setattr(
            mixpanel_source, "_export_events",
            lambda event, from_date, to_date: events,
        )
        r = mixpanel_source.summarize_segments_from_mixpanel(
            "voucher_redeemed", "segment", "amount", "2026-05-01", "2026-05-31",
        )
        assert r["segment_count"] == 2
        assert r["segments"]["active"]["sum"] == 2000
        assert r["source"] == "mixpanel"
