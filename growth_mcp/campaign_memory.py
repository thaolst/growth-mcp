"""Campaign Memory — search past campaigns for reference + learnings."""

import json
import os
import re
from pathlib import Path

MEMORY_DIR = Path(__file__).resolve().parent.parent / "campaign_memory"


def load_all_campaigns() -> list[dict]:
    """Load all campaign files from campaign_memory/ directory."""
    campaigns = []
    if not MEMORY_DIR.exists():
        return campaigns

    for f in sorted(MEMORY_DIR.glob("*.json")):
        try:
            with open(f) as fh:
                data = json.load(fh)
                data["_file"] = f.name
                campaigns.append(data)
        except (json.JSONDecodeError, IOError):
            continue
    return campaigns


def _extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from a text string."""
    text = text.lower().strip()
    # Remove common stop words
    stop_words = {"the", "a", "an", "for", "with", "to", "and", "in", "of",
                  "on", "at", "by", "is", "was", "are", "be", "has", "have",
                  "do", "does", "did", "this", "that", "these", "those",
                  "it", "its", "we", "they", "them", "their", "our",
                  "new", "boost", "tăng", "cho", "với", "của", "và",
                  "các", "được", "có", "trong", "trên", "khi"}
    words = re.findall(r"[a-zA-Z_]+", text)
    return {w for w in words if w not in stop_words and len(w) > 2}


def search_campaigns(
    objective: str,
    segment: str,
    budget_level: str,
    max_results: int = 3,
) -> list[dict]:
    """Search campaign memory for campaigns similar to the given parameters.

    Returns campaigns sorted by relevance (match score descending).
    Each result includes a 'match_score' float and 'matched_keywords' list.
    """
    campaigns = load_all_campaigns()
    if not campaigns:
        return []

    objective_keywords = _extract_keywords(objective)
    scored: list[tuple[float, dict]] = []

    for camp in campaigns:
        score = 0.0
        matched = []

        # 1. Segment match (highest weight)
        if camp.get("segment") == segment:
            score += 30
            matched.append(f"segment match: {segment}")

        # 2. Budget level match
        if camp.get("budget_level") == budget_level:
            score += 20
            matched.append(f"budget match: {budget_level}")

        # 3. Objective keyword overlap
        camp_keywords = _extract_keywords(camp.get("objective", ""))
        overlap = objective_keywords & camp_keywords
        if overlap:
            score += len(overlap) * 10
            matched.append(f"keywords: {', '.join(sorted(overlap))}")

        # 4. Learning keywords
        for learning in camp.get("learnings", []):
            learn_keywords = _extract_keywords(learning)
            if objective_keywords & learn_keywords:
                score += 5
                matched.append(f"learning overlap")

        camp_copy = dict(camp)
        camp_copy["match_score"] = round(score, 1)
        camp_copy["matched_keywords"] = matched
        scored.append((score, camp_copy))

    scored.sort(key=lambda x: -x[0])
    return [c for s, c in scored if s > 0][:max_results]


def save_campaign(campaign: dict) -> str:
    """Save a new campaign to memory. Returns filename."""
    camp_id = campaign.get("id") or f"camp-{len(load_all_campaigns()) + 1:03d}"
    campaign["id"] = camp_id
    filename = f"{camp_id}.json"
    filepath = MEMORY_DIR / filename

    with open(filepath, "w") as f:
        json.dump(campaign, f, indent=2, ensure_ascii=False)

    return filename
