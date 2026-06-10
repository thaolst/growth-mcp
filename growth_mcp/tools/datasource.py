"""CSV data layer: feed real campaign data into growth-mcp analyzers.

This is the first data source (local CSV). The functions here parse raw
files and bridge into the existing pure analyzers (experiment, retention),
so analysis runs on real numbers instead of manually typed inputs.
"""

import csv
import os
from collections import defaultdict

from growth_mcp.tools import experiment, retention

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB guardrail
SAMPLE_ROWS = 5


def _read_csv(file_path: str) -> tuple[list[str], list[dict]] | dict:
    """Read a CSV file. Returns (headers, rows) or an error dict."""
    if not os.path.isfile(file_path):
        return {"error": f"File not found: {file_path}"}
    if os.path.getsize(file_path) > MAX_FILE_SIZE_BYTES:
        return {"error": f"File exceeds {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB limit."}
    try:
        with open(file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            rows = list(reader)
    except (csv.Error, UnicodeDecodeError) as e:
        return {"error": f"Failed to parse CSV: {e}"}
    if not headers:
        return {"error": "CSV has no header row."}
    if not rows:
        return {"error": "CSV has a header but no data rows."}
    return headers, rows


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def inspect_csv(file_path: str) -> dict:
    """Summarize a CSV: columns, inferred types, row count, sample rows."""
    parsed = _read_csv(file_path)
    if isinstance(parsed, dict):
        return parsed
    headers, rows = parsed

    columns = {}
    for h in headers:
        values = [r.get(h, "") for r in rows]
        non_empty = [v for v in values if v not in ("", None)]
        numeric = sum(1 for v in non_empty if _is_number(v))
        if non_empty and numeric == len(non_empty):
            col_type = "numeric"
        elif non_empty and numeric > 0:
            col_type = "mixed"
        else:
            col_type = "text"
        columns[h] = {
            "type": col_type,
            "non_empty": len(non_empty),
            "empty": len(values) - len(non_empty),
            "unique": len(set(non_empty)),
        }

    return {
        "file": os.path.basename(file_path),
        "rows": len(rows),
        "columns": columns,
        "sample_rows": rows[:SAMPLE_ROWS],
    }


def analyze_experiment_from_csv(
    file_path: str,
    group_col: str,
    converted_col: str,
    control_label: str = "control",
    treatment_label: str = "treatment",
    metric_name: str = "conversion",
) -> dict:
    """Aggregate raw A/B rows and run a two-proportion z-test.

    Expects one row per user with a group column (control/treatment labels)
    and a converted column (1/0, true/false, yes/no).
    """
    parsed = _read_csv(file_path)
    if isinstance(parsed, dict):
        return parsed
    headers, rows = parsed

    for col in (group_col, converted_col):
        if col not in headers:
            return {"error": f"Column '{col}' not found. Available: {headers}"}

    truthy = {"1", "true", "yes", "y", "converted"}
    falsy = {"0", "false", "no", "n", ""}
    counts = {control_label: [0, 0], treatment_label: [0, 0]}  # [conversions, sample]

    skipped = 0
    for r in rows:
        group = (r.get(group_col) or "").strip()
        if group not in counts:
            skipped += 1
            continue
        raw = (r.get(converted_col) or "").strip().lower()
        if raw in truthy:
            counts[group][0] += 1
            counts[group][1] += 1
        elif raw in falsy:
            counts[group][1] += 1
        else:
            skipped += 1

    c_conv, c_n = counts[control_label]
    t_conv, t_n = counts[treatment_label]
    if c_n == 0 or t_n == 0:
        return {
            "error": (
                f"No rows matched group labels '{control_label}'/'{treatment_label}' "
                f"in column '{group_col}'. Check control_label and treatment_label."
            )
        }

    result = experiment.analyze_test(c_conv, t_conv, c_n, t_n, metric_name)
    result["data_source"] = {
        "file": os.path.basename(file_path),
        "rows_used": c_n + t_n,
        "rows_skipped": skipped,
        "control": {"conversions": c_conv, "sample": c_n},
        "treatment": {"conversions": t_conv, "sample": t_n},
    }
    return result


def analyze_retention_from_csv(
    file_path: str,
    period_col: str,
    value_col: str,
    campaign_level: str = "S",
) -> dict:
    """Build a retention cohort from CSV and run cohort analysis.

    Accepts either format:
    - rates: value_col holds retention rates 0.0-1.0 per period
    - counts: value_col holds active user counts per period
      (auto-normalized against the first period)
    """
    parsed = _read_csv(file_path)
    if isinstance(parsed, dict):
        return parsed
    headers, rows = parsed

    for col in (period_col, value_col):
        if col not in headers:
            return {"error": f"Column '{col}' not found. Available: {headers}"}

    series: dict[str, float] = {}
    for r in rows:
        period = (r.get(period_col) or "").strip()
        raw = (r.get(value_col) or "").strip()
        if not period or not _is_number(raw):
            continue
        series[period] = float(raw)

    if len(series) < 2:
        return {"error": "Need at least 2 periods with numeric values."}

    values = list(series.values())
    normalized = False
    if any(v > 1.0 for v in values):
        # Treat as user counts: normalize against the first (sorted) period
        first = series[sorted(series.keys())[0]]
        if first <= 0:
            return {"error": "First period count must be positive to normalize."}
        series = {k: round(v / first, 4) for k, v in series.items()}
        normalized = True

    result = retention.analyze_cohort(series, campaign_level)
    result["data_source"] = {
        "file": os.path.basename(file_path),
        "periods": len(series),
        "normalized_from_counts": normalized,
    }
    return result


def summarize_segments_from_csv(
    file_path: str,
    segment_col: str,
    value_col: str,
) -> dict:
    """Per-segment stats (count, sum, mean, min, max, share) from raw rows.

    Useful for segmented balance or spend analysis, e.g. point balances
    or voucher redemption value by user segment.
    """
    parsed = _read_csv(file_path)
    if isinstance(parsed, dict):
        return parsed
    headers, rows = parsed

    for col in (segment_col, value_col):
        if col not in headers:
            return {"error": f"Column '{col}' not found. Available: {headers}"}

    buckets: dict[str, list[float]] = defaultdict(list)
    skipped = 0
    for r in rows:
        seg = (r.get(segment_col) or "").strip()
        raw = (r.get(value_col) or "").strip()
        if not seg or not _is_number(raw):
            skipped += 1
            continue
        buckets[seg].append(float(raw))

    if not buckets:
        return {"error": "No usable rows: check segment_col and value_col."}

    grand_total = sum(sum(v) for v in buckets.values())
    segments = {}
    for seg, vals in sorted(buckets.items(), key=lambda kv: -sum(kv[1])):
        total = sum(vals)
        segments[seg] = {
            "count": len(vals),
            "sum": round(total, 2),
            "mean": round(total / len(vals), 2),
            "min": min(vals),
            "max": max(vals),
            "share_of_total": round(total / grand_total, 4) if grand_total else 0,
        }

    return {
        "file": os.path.basename(file_path),
        "segment_count": len(segments),
        "rows_used": sum(len(v) for v in buckets.values()),
        "rows_skipped": skipped,
        "segments": segments,
    }
