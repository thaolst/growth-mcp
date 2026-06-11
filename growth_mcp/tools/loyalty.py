"""Loyalty program economics: points expiry, redemption elasticity, balance health.

The vertical layer for points/cashback loyalty programs. All concepts are
standard loyalty economics (breakage, arc elasticity, coverage ratio),
implemented from a fintech super-app practitioner perspective.
"""

from growth_mcp.tools import datasource


def forecast_points_expiry(
    expiring_points_by_period: dict[str, float],
    historical_redemption_rate: float,
    breakage_target_pct: float = 20.0,
) -> dict:
    """Forecast points expiry: liability, expected breakage, intervention need.

    Args:
        expiring_points_by_period: Period label -> points scheduled to expire
            (e.g. {"2026-07": 1200000, "2026-08": 900000}).
        historical_redemption_rate: Share of at-risk points typically redeemed
            before expiry once users are notified (0-1).
        breakage_target_pct: Program's target breakage percentage. Breakage
            far above target means users see no value; far below means
            cost pressure.
    """
    if not expiring_points_by_period:
        return {"error": "expiring_points_by_period is empty."}
    if not 0 <= historical_redemption_rate <= 1:
        return {"error": "historical_redemption_rate must be between 0 and 1."}
    if any(v < 0 for v in expiring_points_by_period.values()):
        return {"error": "Point amounts must be non-negative."}

    total_expiring = sum(expiring_points_by_period.values())
    expected_redeemed = total_expiring * historical_redemption_rate
    expected_breakage = total_expiring - expected_redeemed
    breakage_pct = (expected_breakage / total_expiring * 100) if total_expiring else 0.0

    periods = []
    for period in sorted(expiring_points_by_period):
        amount = expiring_points_by_period[period]
        periods.append({
            "period": period,
            "expiring_points": amount,
            "expected_breakage": round(amount * (1 - historical_redemption_rate), 2),
            "share_of_total": round(amount / total_expiring, 4) if total_expiring else 0,
        })

    gap = breakage_pct - breakage_target_pct
    if gap > 15:
        assessment = "BREAKAGE_TOO_HIGH"
        recommendation = (
            "Expected breakage is far above target: users are not finding value "
            "before expiry. Run expiry-reminder campaigns on the heaviest periods "
            "and consider lowering redemption prices for at-risk balances."
        )
    elif gap < -10:
        assessment = "BREAKAGE_TOO_LOW"
        recommendation = (
            "Expected breakage is well below target: redemption cost pressure. "
            "Review reward pricing and check for redemption abuse patterns "
            "before tightening."
        )
    else:
        assessment = "ON_TARGET"
        recommendation = (
            "Expected breakage is near target. Maintain reminder cadence and "
            "monitor the heaviest expiry periods."
        )

    heaviest = max(periods, key=lambda p: p["expiring_points"])
    return {
        "total_expiring_points": total_expiring,
        "expected_redeemed": round(expected_redeemed, 2),
        "expected_breakage": round(expected_breakage, 2),
        "expected_breakage_pct": round(breakage_pct, 2),
        "breakage_target_pct": breakage_target_pct,
        "assessment": assessment,
        "heaviest_period": heaviest["period"],
        "by_period": periods,
        "recommendation": recommendation,
    }


def _arc_elasticity(p1: float, q1: float, p2: float, q2: float) -> float | None:
    """Arc (midpoint) price elasticity between two observations."""
    avg_p = (p1 + p2) / 2
    avg_q = (q1 + q2) / 2
    if avg_p == 0 or avg_q == 0 or p2 == p1:
        return None
    return ((q2 - q1) / avg_q) / ((p2 - p1) / avg_p)


def analyze_redemption_elasticity(
    observations: list[dict],
    segment: str | None = None,
) -> dict:
    """Price elasticity of redemption from observed price periods.

    Each observation: {"period": str, "points_price": float, "redemptions": float}.
    Periods are sorted by label; elasticity is computed between adjacent
    periods using the arc (midpoint) method.

    Args:
        observations: At least 2 observed periods with price and redemptions.
        segment: Optional segment label for reporting.
    """
    if len(observations) < 2:
        return {"error": "Need at least 2 observations to compute elasticity."}
    for ob in observations:
        for key in ("period", "points_price", "redemptions"):
            if key not in ob:
                return {"error": f"Each observation needs '{key}'. Got: {sorted(ob.keys())}"}
        if float(ob["points_price"]) <= 0:
            return {"error": "points_price must be positive."}
        if float(ob["redemptions"]) < 0:
            return {"error": "redemptions must be non-negative."}

    obs = sorted(observations, key=lambda o: str(o["period"]))
    pairs = []
    elasticities = []
    for a, b in zip(obs, obs[1:]):
        e = _arc_elasticity(
            float(a["points_price"]), float(a["redemptions"]),
            float(b["points_price"]), float(b["redemptions"]),
        )
        pairs.append({
            "from_period": a["period"],
            "to_period": b["period"],
            "price_change_pct": round(
                (float(b["points_price"]) - float(a["points_price"]))
                / float(a["points_price"]) * 100, 2),
            "redemption_change_pct": round(
                (float(b["redemptions"]) - float(a["redemptions"]))
                / float(a["redemptions"]) * 100, 2) if float(a["redemptions"]) else None,
            "arc_elasticity": round(e, 3) if e is not None else None,
        })
        if e is not None:
            elasticities.append(e)

    if not elasticities:
        return {"error": "No valid adjacent pairs (price never changed or quantities are zero)."}

    avg_e = sum(elasticities) / len(elasticities)
    abs_e = abs(avg_e)
    if abs_e > 1.5:
        classification = "HIGHLY_ELASTIC"
        pricing_note = (
            "Redemptions react strongly to price. Lowering the points price on "
            "key vouchers should lift volume more than proportionally; use low-price "
            "windows for activation pushes."
        )
    elif abs_e > 1.0:
        classification = "ELASTIC"
        pricing_note = (
            "Redemptions react more than proportionally to price. Price moves are "
            "an effective lever; test in small steps."
        )
    elif abs_e > 0.5:
        classification = "MODERATELY_INELASTIC"
        pricing_note = (
            "Redemptions react less than proportionally. Price cuts cost more than "
            "the volume they buy; lead with selection and visibility instead."
        )
    else:
        classification = "INELASTIC"
        pricing_note = (
            "Redemptions barely react to price. Do not spend margin on price cuts; "
            "the constraint is likely awareness, selection, or balance sufficiency."
        )

    result = {
        "average_arc_elasticity": round(avg_e, 3),
        "classification": classification,
        "pairs": pairs,
        "periods_analyzed": len(obs),
        "pricing_note": pricing_note,
    }
    if segment:
        result["segment"] = segment
    return result


def analyze_redemption_elasticity_from_csv(
    file_path: str,
    period_col: str,
    price_col: str,
    redemptions_col: str,
    segment_col: str | None = None,
) -> dict:
    """Elasticity analysis straight from a CSV of observed price periods.

    With segment_col, elasticity is computed per segment so price sensitivity
    differences across segments are visible in one pass.
    """
    parsed = datasource._read_csv(file_path)
    if isinstance(parsed, dict):
        return parsed
    headers, rows = parsed

    needed = [period_col, price_col, redemptions_col] + ([segment_col] if segment_col else [])
    for col in needed:
        if col not in headers:
            return {"error": f"Column '{col}' not found. Available: {headers}"}

    def to_obs(row):
        try:
            return {
                "period": (row.get(period_col) or "").strip(),
                "points_price": float(row.get(price_col)),
                "redemptions": float(row.get(redemptions_col)),
            }
        except (TypeError, ValueError):
            return None

    if not segment_col:
        observations = [o for o in (to_obs(r) for r in rows) if o and o["period"]]
        result = analyze_redemption_elasticity(observations)
        if "error" not in result:
            result["source"] = "csv"
        return result

    by_segment: dict[str, list[dict]] = {}
    for r in rows:
        seg = (r.get(segment_col) or "").strip()
        ob = to_obs(r)
        if not seg or not ob or not ob["period"]:
            continue
        by_segment.setdefault(seg, []).append(ob)

    segments = {}
    skipped = []
    for seg, obs in sorted(by_segment.items()):
        result = analyze_redemption_elasticity(obs, segment=seg)
        if "error" in result:
            skipped.append({"segment": seg, "reason": result["error"]})
        else:
            segments[seg] = {
                "average_arc_elasticity": result["average_arc_elasticity"],
                "classification": result["classification"],
                "periods_analyzed": result["periods_analyzed"],
                "pricing_note": result["pricing_note"],
            }

    if not segments:
        return {"error": "No segment had enough valid observations.", "details": skipped}

    most = max(segments.items(), key=lambda kv: abs(kv[1]["average_arc_elasticity"]))
    least = min(segments.items(), key=lambda kv: abs(kv[1]["average_arc_elasticity"]))
    return {
        "source": "csv",
        "segments": segments,
        "skipped_segments": skipped,
        "most_price_sensitive": most[0],
        "least_price_sensitive": least[0],
        "note": (
            "Target price promotions at the most price-sensitive segments; "
            "for the least sensitive, price cuts mostly give margin away."
        ),
    }


def analyze_balance_health(segments: list[dict]) -> dict:
    """Points balance health per segment: coverage ratio and dormancy risk.

    Each segment dict: {"segment": str, "users": int, "total_balance": float,
    "typical_redemption_price": float} and optionally
    "active_redeemer_share" (0-1, share of users who redeemed recently).

    Coverage ratio = average balance / typical redemption price: how many
    redemptions the average user's balance can fund. Below 1 means most
    users cannot afford a single reward, which suppresses engagement.
    """
    if not segments:
        return {"error": "segments is empty."}

    out = []
    for s in segments:
        for key in ("segment", "users", "total_balance", "typical_redemption_price"):
            if key not in s:
                return {"error": f"Each segment needs '{key}'. Got: {sorted(s.keys())}"}
        users = int(s["users"])
        price = float(s["typical_redemption_price"])
        if users <= 0 or price <= 0:
            return {"error": "users and typical_redemption_price must be positive."}

        avg_balance = float(s["total_balance"]) / users
        coverage = avg_balance / price
        redeemer_share = s.get("active_redeemer_share")

        if coverage < 1:
            status = "BELOW_REDEMPTION_FLOOR"
            action = (
                "Average balance cannot fund a single typical reward. Add low-price "
                "reward options or top-up earn mechanics before pushing redemption comms."
            )
        elif coverage > 5 and (redeemer_share is None or redeemer_share < 0.3):
            status = "DORMANT_BALANCE_RISK"
            action = (
                "Balances are piling up without redemption: liability grows while "
                "perceived value does not. Push redemption with curated rewards "
                "before considering expiry policy."
            )
        else:
            status = "HEALTHY"
            action = "Balance level supports regular redemption. Maintain earn/burn balance."

        entry = {
            "segment": s["segment"],
            "users": users,
            "avg_balance": round(avg_balance, 2),
            "coverage_ratio": round(coverage, 2),
            "status": status,
            "action": action,
        }
        if redeemer_share is not None:
            entry["active_redeemer_share"] = redeemer_share
        out.append(entry)

    flagged = [e["segment"] for e in out if e["status"] != "HEALTHY"]
    return {
        "segments": out,
        "segments_flagged": flagged,
        "summary": (
            f"{len(flagged)} of {len(out)} segments need intervention."
            if flagged else "All segments healthy."
        ),
    }
