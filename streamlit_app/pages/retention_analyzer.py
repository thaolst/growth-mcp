"""Retention Analyzer — upload cohort CSV, get analysis + recommendations."""

import os
import sys
import tempfile

import pandas as pd
import streamlit as st

# Add parent dir to path so we can import growth_mcp modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# ── Page config ────────────────────────────────────────────────

st.set_page_config(
    page_title="Retention Analyzer — Growth MCP",
    page_icon="📊",
    layout="wide",
)

# ── Sidebar (same as main) ─────────────────────────────────────

with st.sidebar:
    st.markdown("## 📈 **Growth MCP**")
    st.caption("AI-powered tools for growth marketers")
    st.divider()

    st.page_link("main.py", label="🏠 Home", use_container_width=True)
    st.page_link("pages/retention_analyzer.py", label="📊 Retention Analyzer", use_container_width=True)
    st.page_link("pages/campaign_brief.py", label="📝 Campaign Brief Generator", use_container_width=True, disabled=True)
    st.page_link("pages/voucher_designer.py", label="🎫 Voucher Designer", use_container_width=True, disabled=True)
    st.page_link("pages/experiment_analyzer.py", label="🧪 A/B Test Analyzer", use_container_width=True, disabled=True)

    st.divider()
    st.caption("Built by [Tara Le](https://github.com/thaolst)")


st.title("📊 Retention Analyzer")

st.markdown("""
Analyze retention cohort data — find where users drop off and get
intervention recommendations tailored to your campaign budget.
""")

# ── Input section ──────────────────────────────────────────────

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader(
        "Upload cohort CSV",
        type=["csv"],
        help="CSV with one row per period. Columns: period label + retention rate or user count.",
    )

with col2:
    campaign_level = st.selectbox(
        "Campaign budget level",
        options=["S (small — in-app only)", "M (medium — some paid channels)"],
        index=0,
    )
    level_code = "S" if "S" in campaign_level else "M"

# If no data, show example format
if not uploaded_file:
    with st.container(border=True):
        st.markdown("**📄 Expected CSV format**")
        st.dataframe(
            pd.DataFrame({
                "period": ["week_0", "week_1", "week_2", "week_3", "week_4"],
                "retention_rate": [1.0, 0.62, 0.41, 0.28, 0.21],
            })
        )
        st.caption("First column = period labels. Second column = retention rates (0-1) or active user counts.")
    st.stop()

# ── Parse CSV ──────────────────────────────────────────────────

try:
    df = pd.read_csv(uploaded_file)
    st.success(f"✅ Loaded {len(df)} rows, {len(df.columns)} columns")
except Exception as e:
    st.error(f"Could not read CSV: {e}")
    st.stop()

with st.expander("📋 Raw data preview", expanded=False):
    st.dataframe(df, use_container_width=True)

# Let user pick which columns
cols = df.columns.tolist()

if len(cols) < 2:
    st.error("CSV needs at least 2 columns: period labels + values")
    st.stop()

period_col = st.selectbox("Period column (e.g. week, day, month)", cols, index=0)
value_col = st.selectbox("Value column (retention rate or active user count)", cols, index=min(1, len(cols) - 1))

# ── Analyze ────────────────────────────────────────────────────

if st.button("🚀 Analyze Retention", type="primary", use_container_width=True):

    with st.spinner("Analyzing cohort data..."):

        # Save to temp file for the tool to read
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name

        try:
            # Use the datasource module directly — returns dict, not JSON string
            from growth_mcp.tools.datasource import analyze_retention_from_csv

            result = analyze_retention_from_csv(
                file_path=temp_path,
                period_col=period_col,
                value_col=value_col,
                campaign_level=level_code,
            )

            # Clean up
            os.unlink(temp_path)

            # ── Display results ────────────────────────────────────
            if "error" in result:
                st.error(f"Analysis error: {result['error']}")
                st.stop()

            st.balloons()
            st.header("📊 Analysis Results")

            summary = result.get("cohort_summary", {})
            analysis = result.get("analysis", {})
            interventions = result.get("interventions", [])

            # Key metrics row
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)

            with col_m1:
                st.metric("Periods Analyzed", summary.get("periods", len(df)))

            with col_m2:
                biggest_drop = summary.get("biggest_drop", {})
                drop_pct = biggest_drop.get("drop_pct", "—")
                drop_period = biggest_drop.get("period", "")
                st.metric("Biggest Drop", f"{drop_pct}%" if drop_pct != "—" else "—",
                          help=f"Between: {drop_period}")

            with col_m3:
                final_ret = summary.get("latest_retention_pct")
                if final_ret is not None:
                    st.metric("Final Retention", f"{final_ret}%")
                else:
                    st.metric("Final Retention", "—")

            with col_m4:
                phase = analysis.get("critical_phase", level_code)
                st.metric("Critical Phase", phase)

            st.divider()

            # Retention data chart
            st.subheader("📈 Retention Curve")
            retention_data = summary.get("data", {})
            if retention_data:
                import pandas as _pd
                chart_df = _pd.DataFrame({
                    "period": list(retention_data.keys()),
                    "retention": [v * 100 for v in retention_data.values()],
                })
                st.bar_chart(chart_df, x="period", y="retention", height=300)

            st.divider()

            # Diagnosis section
            st.subheader("🔍 Diagnosis")

            biggest_drop_pct = analysis.get("drop_percentage", 0)
            critical_phase = analysis.get("critical_phase", "early activation")
            retention_type = analysis.get("retention_type", "")

            st.markdown(f"""
            - **Biggest drop**: {biggest_drop_pct}% between {analysis.get('biggest_drop_period', '?')}
            - **Critical phase**: {critical_phase}
            - **Retention type**: {retention_type if retention_type else 'Unknown — check the data'}
            """)

            if biggest_drop_pct > 35:
                st.warning(
                    f"⚠️ Drop >35% in a single period suggests an **activation** problem, "
                    f"not a retention problem. Focus on onboarding, first-time experience, "
                    f"and early habit formation before optimizing later periods."
                )

            # Recommendations
            st.divider()
            st.subheader("💡 Recommendations")

            if interventions:
                for i, rec in enumerate(interventions, 1):
                    with st.container(border=True):
                        cols = st.columns([3, 1])
                        cols[0].markdown(f"**{i}. {rec.get('phase', rec.get('action', 'Recommendation'))}**")
                        cols[1].markdown(f"*{rec.get('action', 'Intervene')}*")
                        if "detail" in rec:
                            st.markdown(f"   {rec['detail']}")
                        if "expected_lift" in rec:
                            st.markdown(f"   📈 Expected lift: **{rec['expected_lift']}**")
                        if "next_step" in rec:
                            st.markdown(f"   ➡️ Next: {rec['next_step']}")
            else:
                st.info("No specific recommendations. Review the data manually.")

            # Full JSON
            with st.expander("📄 Full analysis (JSON)", expanded=False):
                st.json(result)

        except ImportError as e:
            st.error(f"Could not import growth_mcp module: {e}")
            st.info("Make sure you've installed growth-mcp: `pip install -e .` in the repo root")
            os.unlink(temp_path)

        except Exception as e:
            st.error(f"Analysis failed: {e}")
            # Clean up on error
            try:
                os.unlink(temp_path)
            except Exception:
                pass
else:
    st.info("👆 Click **Analyze Retention** to run the analysis")
