"""Mixpanel data source: pull events via the raw Export API and feed them
into growth-mcp analyzers.

No extra dependency needed (stdlib urllib). Authentication via environment:

    MIXPANEL_API_SECRET   project API secret (required)
    MIXPANEL_API_HOST     optional, defaults to data.mixpanel.com
                          (use data-eu.mixpanel.com for EU residency)

Guardrails: date range capped at 90 days, events capped at 200K rows.
"""

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

from growth_mcp.tools import datasource

MAX_DATE_RANGE_DAYS = 90
MAX_EVENTS = 200_000
DEFAULT_HOST = "data.mixpanel.com"

_AUTH_HINT = (
    "MIXPANEL_API_SECRET is not set. Find your project API secret in "
    "Mixpanel under Project Settings, then export it as an environment "
    "variable before starting the server."
)


def _validate_dates(from_date: str, to_date: str) -> dict | None:
    try:
        start = date.fromisoformat(from_date)
        end = date.fromisoformat(to_date)
    except ValueError:
        return {"error": "Dates must be ISO format YYYY-MM-DD."}
    if end < start:
        return {"error": "to_date must not be before from_date."}
    if (end - start).days > MAX_DATE_RANGE_DAYS:
        return {"error": f"Date range capped at {MAX_DATE_RANGE_DAYS} days. Narrow the range."}
    return None


def _export_events(event: str, from_date: str, to_date: str) -> list[dict] | dict:
    """Fetch raw events from the Mixpanel Export API as a list of dicts.

    Each dict is {"event": name, "properties": {...}}.
    """
    secret = os.environ.get("MIXPANEL_API_SECRET", "").strip()
    if not secret:
        return {"error": _AUTH_HINT}

    host = os.environ.get("MIXPANEL_API_HOST", DEFAULT_HOST).strip() or DEFAULT_HOST
    params = urllib.parse.urlencode({
        "from_date": from_date,
        "to_date": to_date,
        "event": json.dumps([event]),
    })
    url = f"https://{host}/api/2.0/export?{params}"
    auth = base64.b64encode(f"{secret}:".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})

    events: list[dict] = []
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for line in resp:
                if len(events) >= MAX_EVENTS:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return {"error": "Mixpanel rejected the API secret (401/403). Check MIXPANEL_API_SECRET."}
        return {"error": f"Mixpanel export failed: HTTP {e.code}"}
    except urllib.error.URLError as e:
        return {"error": f"Could not reach Mixpanel ({host}): {e.reason}"}

    if not events:
        return {"error": f"No '{event}' events found between {from_date} and {to_date}."}
    return events


def _distinct_id(props: dict) -> str:
    return str(props.get("distinct_id") or props.get("$distinct_id") or "").strip()


def analyze_experiment_from_mixpanel(
    exposure_event: str,
    conversion_event: str,
    group_property: str,
    from_date: str,
    to_date: str,
    control_label: str = "control",
    treatment_label: str = "treatment",
    metric_name: str = "conversion",
) -> dict:
    """A/B analysis from Mixpanel events.

    Builds the user table from two event exports: exposure events assign
    each distinct_id to a group (via group_property), conversion events
    mark which users converted. Then runs a two-proportion z-test.
    """
    invalid = _validate_dates(from_date, to_date)
    if invalid:
        return invalid

    exposures = _export_events(exposure_event, from_date, to_date)
    if isinstance(exposures, dict):
        return exposures
    conversions = _export_events(conversion_event, from_date, to_date)
    if isinstance(conversions, dict):
        # Khong co conversion event nao van la ket qua hop le (0 conversion)
        if "No '" in conversions.get("error", ""):
            conversions = []
        else:
            return conversions

    user_group: dict[str, str] = {}
    missing_group = 0
    for ev in exposures:
        props = ev.get("properties", {})
        uid = _distinct_id(props)
        group = str(props.get(group_property) or "").strip()
        if not uid or not group:
            missing_group += 1
            continue
        # First exposure wins: giu group dau tien thay duoc cua user
        user_group.setdefault(uid, group)

    if not user_group:
        return {
            "error": (
                f"No exposure events carried property '{group_property}'. "
                "Check the property name in Mixpanel (Lexicon)."
            )
        }

    converted_ids = set()
    for ev in conversions:
        uid = _distinct_id(ev.get("properties", {}))
        if uid:
            converted_ids.add(uid)

    rows = [
        {"group": grp, "converted": "1" if uid in converted_ids else "0"}
        for uid, grp in user_group.items()
    ]

    result = datasource.experiment_from_rows(
        rows, "group", "converted", control_label, treatment_label, metric_name,
    )
    if "error" not in result:
        result["data_source"]["source"] = "mixpanel"
        result["data_source"]["exposure_event"] = exposure_event
        result["data_source"]["conversion_event"] = conversion_event
        result["data_source"]["unique_users"] = len(user_group)
        result["data_source"]["exposures_missing_group"] = missing_group
    return result


def summarize_segments_from_mixpanel(
    event: str,
    segment_property: str,
    value_property: str,
    from_date: str,
    to_date: str,
) -> dict:
    """Per-segment stats over Mixpanel events (1 row per event).

    Useful for revenue or redemption value by segment, e.g. voucher
    redemption events with an amount property.
    """
    invalid = _validate_dates(from_date, to_date)
    if invalid:
        return invalid

    events = _export_events(event, from_date, to_date)
    if isinstance(events, dict):
        return events

    rows = [
        {
            "segment": str(ev.get("properties", {}).get(segment_property) or "").strip(),
            "value": ev.get("properties", {}).get(value_property),
        }
        for ev in events
    ]

    result = datasource.segments_from_rows(rows, "segment", "value")
    if "error" not in result:
        result["source"] = "mixpanel"
        result["event"] = event
        result["events_fetched"] = len(events)
    return result
