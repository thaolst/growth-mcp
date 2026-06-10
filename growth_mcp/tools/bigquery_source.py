"""BigQuery data source: run SQL and feed results into growth-mcp analyzers.

Requires the optional dependency:

    pip install "growth-mcp[bigquery]"

Authentication follows the standard Google Cloud flow (Application Default
Credentials): either `gcloud auth application-default login` or the
GOOGLE_APPLICATION_CREDENTIALS environment variable pointing to a service
account key file.
"""

from growth_mcp.tools import datasource

MAX_ROWS = 200_000  # guardrail: aggregate in SQL if your data is bigger

_INSTALL_HINT = (
    "BigQuery support requires the optional dependency. "
    'Install with: pip install "growth-mcp[bigquery]"'
)

_FORBIDDEN_KEYWORDS = (
    "insert ", "update ", "delete ", "drop ", "create ", "alter ",
    "truncate ", "merge ", "grant ", "revoke ",
)


def _validate_sql(sql: str) -> dict | None:
    """Read-only guardrail: only SELECT/WITH statements are allowed."""
    stripped = sql.strip().lower()
    if not (stripped.startswith("select") or stripped.startswith("with")):
        return {"error": "Only SELECT (or WITH ... SELECT) queries are allowed."}
    for kw in _FORBIDDEN_KEYWORDS:
        if kw in stripped:
            return {"error": f"Query contains a write keyword ('{kw.strip()}'). Read-only queries only."}
    return None


def _run_query(sql: str, project: str | None = None) -> list[dict] | dict:
    """Execute a read-only query. Returns rows as list[dict] or an error dict."""
    invalid = _validate_sql(sql)
    if invalid:
        return invalid
    try:
        from google.cloud import bigquery  # noqa: PLC0415 (lazy optional import)
    except ImportError:
        return {"error": _INSTALL_HINT}

    try:
        client = bigquery.Client(project=project)
        job = client.query(sql)
        rows = [dict(row) for row in job.result(max_results=MAX_ROWS)]
    except Exception as e:  # auth, permission, SQL errors from the API
        return {"error": f"BigQuery query failed: {e}"}

    if not rows:
        return {"error": "Query returned no rows."}
    return rows


def _check_columns(rows: list[dict], cols: tuple[str, ...]) -> dict | None:
    available = list(rows[0].keys())
    for col in cols:
        if col not in available:
            return {"error": f"Column '{col}' not in query result. Available: {available}"}
    return None


def analyze_experiment_from_bigquery(
    sql: str,
    group_col: str,
    converted_col: str,
    project: str | None = None,
    control_label: str = "control",
    treatment_label: str = "treatment",
    metric_name: str = "conversion",
) -> dict:
    """Run an A/B analysis on the result of a BigQuery SELECT (1 row per user)."""
    rows = _run_query(sql, project)
    if isinstance(rows, dict):
        return rows
    invalid = _check_columns(rows, (group_col, converted_col))
    if invalid:
        return invalid

    result = datasource.experiment_from_rows(
        rows, group_col, converted_col, control_label, treatment_label, metric_name,
    )
    if "error" not in result:
        result["data_source"]["source"] = "bigquery"
        result["data_source"]["rows_fetched"] = len(rows)
    return result


def analyze_retention_from_bigquery(
    sql: str,
    period_col: str,
    value_col: str,
    project: str | None = None,
    campaign_level: str = "S",
) -> dict:
    """Run cohort retention analysis on a BigQuery result (1 row per period)."""
    rows = _run_query(sql, project)
    if isinstance(rows, dict):
        return rows
    invalid = _check_columns(rows, (period_col, value_col))
    if invalid:
        return invalid

    series: dict[str, float] = {}
    for r in rows:
        period = str(r.get(period_col) or "").strip()
        raw = r.get(value_col)
        if not period or raw is None:
            continue
        try:
            series[period] = float(raw)
        except (TypeError, ValueError):
            continue

    result = datasource.retention_from_pairs(series, campaign_level)
    if "error" not in result:
        result["data_source"]["source"] = "bigquery"
    return result


def summarize_segments_from_bigquery(
    sql: str,
    segment_col: str,
    value_col: str,
    project: str | None = None,
) -> dict:
    """Per-segment statistics on a BigQuery result (1 row per user/transaction)."""
    rows = _run_query(sql, project)
    if isinstance(rows, dict):
        return rows
    invalid = _check_columns(rows, (segment_col, value_col))
    if invalid:
        return invalid

    result = datasource.segments_from_rows(rows, segment_col, value_col)
    if "error" not in result:
        result["source"] = "bigquery"
        result["rows_fetched"] = len(rows)
    return result
