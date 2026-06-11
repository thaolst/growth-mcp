"""Knowledge layer: versioned, source-traced growth marketing domain knowledge.

Inspired by versioned skill-contract registries: every entry carries a
version and a source trace, so consumers know what they are getting and
where it came from. Exposed through MCP resources and prompts in server.py.

Source legend:
- "field" = distilled from real fintech loyalty campaigns in Southeast Asia
- "standard" = widely accepted industry methodology
"""

KNOWLEDGE_VERSION = "1.0.0"

FRAMEWORKS = {
    "version": KNOWLEDGE_VERSION,
    "frameworks": {
        "retention_benchmarks": {
            "version": "1.0.0",
            "source": "field",
            "summary": "Weekly retention reference bands for fintech loyalty programs",
            "bands": {
                "week_1": {"weak": "<40%", "healthy": "40-60%", "strong": ">60%"},
                "week_4": {"weak": "<20%", "healthy": "20-35%", "strong": ">35%"},
                "week_8": {"weak": "<12%", "healthy": "12-25%", "strong": ">25%"},
            },
            "notes": [
                "Bands assume a points/cashback loyalty context, not pure utility apps.",
                "A flattening curve matters more than any single point: find the plateau.",
                "Compare cohorts exposed to high vs low reward-price periods separately.",
            ],
        },
        "voucher_ladder_principles": {
            "version": "1.0.0",
            "source": "field",
            "summary": "How to structure tiered voucher thresholds",
            "principles": [
                "Anchor tier 1 below current AOV (about 0.8x) so the first step feels reachable.",
                "Place the top tier at about 1.5x AOV: enough stretch to lift basket size without stalling.",
                "Keep percentage discounts at or under 25%: above that, abuse and margin damage outweigh lift.",
                "Budget-to-AOV ratio above 15% is a high abuse-risk signal: add verification gates.",
                "Price elasticity differs by segment: test ladders per segment, not globally.",
            ],
        },
        "meu_planning": {
            "version": "1.0.0",
            "source": "field",
            "summary": "Monthly Engaging Users planning structure",
            "steps": [
                "Decompose the MEU target: carryover base + reactivation + new user activation.",
                "Read last cycle's data first: which segments drove the gap, which mechanics moved them.",
                "Assign one primary mechanic per segment (voucher, points exchange, game) and one comm angle.",
                "Reserve 10-15% of budget for in-flight optimization, never plan to spend 100% upfront.",
                "Define the weekly checkpoint metric per segment before launch, not after.",
            ],
        },
        "experiment_hygiene": {
            "version": "1.0.0",
            "source": "standard",
            "summary": "Minimum standards before trusting an A/B readout",
            "checklist": [
                "Sample size computed before launch, not after peeking.",
                "One primary metric declared upfront: everything else is exploratory.",
                "Run full weekly cycles: weekday/weekend behavior differs.",
                "Check sample ratio mismatch before reading any result.",
                "Significant but tiny lifts may not survive rollout: check practical significance.",
            ],
        },
    },
}

GLOSSARY = {
    "version": KNOWLEDGE_VERSION,
    "source": "field",
    "terms": {
        "MEU": "Monthly Engaging Users: users performing a qualifying engagement action within a calendar month. The core target metric for engagement teams.",
        "AOV": "Average Order Value: mean transaction value, the anchor for voucher threshold design.",
        "voucher ladder": "A tiered set of spend thresholds with increasing rewards, designed to lift basket size.",
        "points exchange": "Loyalty mechanic where accumulated points are redeemed for vouchers or perks; redemption price can be tuned by period.",
        "cohort": "A group of users defined by a shared starting event (e.g. first redemption in week X), tracked over time.",
        "retention curve plateau": "The point where a cohort's retention stops declining; the height of the plateau is the program's long-term floor.",
        "sample ratio mismatch": "When the observed split between experiment groups deviates from the designed split; invalidates the readout until explained.",
        "reactivation": "Bringing back users inactive for a defined window; cheaper than acquisition, usually the largest MEU lever after carryover.",
        "abuse risk": "Likelihood that an incentive is exploited (multi-accounting, threshold gaming); scales with the budget-to-AOV ratio.",
        "first exposure wins": "Group assignment rule: a user belongs to the first experiment variant they were exposed to, regardless of later exposures.",
    },
}
