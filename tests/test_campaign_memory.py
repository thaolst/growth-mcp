"""Tests for campaign_memory module."""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from growth_mcp import campaign_memory as cm


# ===========================================================================
# Test data: sample campaigns saved to a temp directory
# ===========================================================================

SAMPLE_SUCCESS = {
    "id": "test-success-001",
    "name": "Test Weekend Campaign",
    "objective": "boost weekend GMV",
    "segment": "active",
    "budget_level": "S",
    "budget": "40M VND",
    "channels": ["in-app push", "in-app banner"],
    "voucher": {"type": "cashback", "value": "10% up to 50K"},
    "result": "success",
    "metrics": {"reach": "120K", "conversion": "8.2%", "ROI": "3.2x"},
    "learnings": ["Push open rate cao nhất 9-10h sáng Thứ 7", "Cashback 10% đủ hấp dẫn active users"],
    "fail_reasons": [],
}

SAMPLE_FAIL = {
    "id": "test-fail-001",
    "name": "Test High Spender Free Gift",
    "objective": "retain high spenders with free gift",
    "segment": "high_spender",
    "budget_level": "M",
    "budget": "150M VND",
    "channels": ["in-app banner", "SMS", "Zalo OA"],
    "voucher": {"type": "free_item", "value": "Free gift on 1M min spend"},
    "result": "fail",
    "metrics": {"reach": "8K", "conversion": "1.2%", "ROI": "0.3x"},
    "learnings": ["High spender prefer exclusive access over free items", "Zalo OA is best channel (CTR 4.5%)"],
    "fail_reasons": ["Min spend 1M too high for free item", "SMS not effective for high spenders"],
}


# ===========================================================================
# Fixture helpers
# ===========================================================================

def _setup_test_memory(tmp_dir: str) -> str:
    """Write sample campaigns to a temp dir and return the path."""
    for camp in [SAMPLE_SUCCESS, SAMPLE_FAIL]:
        path = os.path.join(tmp_dir, f"{camp['id']}.json")
        with open(path, "w") as f:
            json.dump(camp, f)
    return tmp_dir


class TestExtractKeywords:
    def test_simple_keywords(self):
        result = cm._extract_keywords("boost weekend GMV")
        assert "boost" not in result  # stop word
        assert "gmv" in result
        assert "weekend" in result

    def test_empty_string(self):
        result = cm._extract_keywords("")
        assert result == set()

    def test_short_words_removed(self):
        result = cm._extract_keywords("to be or za")
        assert result == set()

    def test_lowercase_normalised(self):
        result = cm._extract_keywords("HIGH SPENDER retention")
        assert "high" in result
        assert "spender" in result
        assert "retention" in result


class TestSearchCampaigns:
    def test_perfect_match_returns_highest_score(self):
        """Same segment + budget + overlapping keywords = highest score."""
        with tempfile.TemporaryDirectory() as tmp:
            cm.MEMORY_DIR = Path(tmp)
            _setup_test_memory(tmp)

            results = cm.search_campaigns(
                objective="boost weekend GMV",
                segment="active",
                budget_level="S",
            )

            assert len(results) >= 1
            best = results[0]
            assert best["id"] == "test-success-001"
            assert best["match_score"] > 50  # perfect match

    def test_fail_campaign_has_warning_signals(self):
        """Fail campaigns should have fail_reasons in results."""
        with tempfile.TemporaryDirectory() as tmp:
            cm.MEMORY_DIR = Path(tmp)
            _setup_test_memory(tmp)

            results = cm.search_campaigns(
                objective="retain high spenders",
                segment="high_spender",
                budget_level="M",
            )

            assert len(results) >= 1
            fail = results[0]
            assert fail["result"] == "fail"
            assert len(fail.get("fail_reasons", [])) > 0

    def test_no_match_returns_empty(self):
        """No matching campaigns should return empty list."""
        with tempfile.TemporaryDirectory() as tmp:
            cm.MEMORY_DIR = Path(tmp)
            _setup_test_memory(tmp)

            results = cm.search_campaigns(
                objective="something completely different",
                segment="new_user",
                budget_level="L",
            )
            assert results == []

    @staticmethod
    def test_empty_memory_returns_empty():
        """No campaign files should return empty list."""
        with tempfile.TemporaryDirectory() as tmp:
            cm.MEMORY_DIR = Path(tmp)
            results = cm.search_campaigns("test", "test", "S")
            assert results == []


class TestSaveCampaign:
    def test_save_and_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            cm.MEMORY_DIR = Path(tmp)

            new_camp = {
                "name": "New Test Campaign",
                "objective": "test save and reload",
                "segment": "active",
                "budget_level": "M",
                "result": "success",
                "learnings": ["Testing save works"],
                "fail_reasons": [],
            }

            filename = cm.save_campaign(new_camp)
            assert filename.endswith(".json")

            # Reload and verify
            campaigns = cm.load_all_campaigns()
            assert len(campaigns) == 1
            assert campaigns[0]["name"] == "New Test Campaign"
            assert "id" in campaigns[0]
