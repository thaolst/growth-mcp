"""Campaign Brief Generator — nhập mục tiêu + segment, ra brief hoàn chỉnh."""

import os
import sys

import streamlit as st

# Add parent dir to path so we can import growth_mcp modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# ── Page config ────────────────────────────────────────────────

st.set_page_config(
    page_title="Campaign Brief Generator — Growth MCP",
    page_icon="📝",
    layout="wide",
)

# ── Sidebar ────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📈 **Growth MCP**")
    st.caption("AI-powered tools for growth marketers")
    st.divider()
    st.page_link("main.py", label="🏠 Home", use_container_width=True)
    st.page_link("pages/retention_analyzer.py", label="📊 Retention Analyzer", use_container_width=True)
    st.page_link("pages/campaign_brief.py", label="📝 Campaign Brief Generator", use_container_width=True)
    st.page_link("pages/voucher_designer.py", label="🎫 Voucher Designer", use_container_width=True, disabled=True)
    st.page_link("pages/experiment_analyzer.py", label="🧪 A/B Test Analyzer", use_container_width=True, disabled=True)
    st.divider()
    st.caption("Built by [Tara Le](https://github.com/thaolst)")

# ── Main content ───────────────────────────────────────────────

st.title("📝 Campaign Brief Generator")
st.markdown("""
Nhập mục tiêu campaign + budget → nhận brief hoàn chỉnh với kênh, timeline,
và gợi ý voucher phù hợp với segment.
""")

st.divider()

# ── Input form ─────────────────────────────────────────────────

with st.container(border=True):
    st.subheader("🎯 Campaign Info")

    col1, col2 = st.columns(2)

    with col1:
        objective = st.text_input(
            "Campaign objective",
            placeholder="e.g. reactivate dormant users, boost weekend GMV",
            help="Mục tiêu chính của campaign",
        )

        segment = st.selectbox(
            "Target segment",
            options=["new_user", "active", "lapsed", "high_spender"],
            format_func=lambda x: {
                "new_user": "🆕 New user — first purchase",
                "active": "✅ Active — regular user",
                "lapsed": "💤 Lapsed — dormant/churned",
                "high_spender": "💎 High spender — VIP",
            }.get(x, x),
        )

    with col2:
        budget_level = st.selectbox(
            "Budget level",
            options=["S", "M", "L"],
            format_func=lambda x: {
                "S": "S — Small (<50M VND, in-app only)",
                "M": "M — Medium (50-200M, some paid)",
                "L": "L — Large (200M+, multi-channel)",
            }.get(x, x),
        )

        custom_channels = st.text_input(
            "Custom channels (optional)",
            placeholder="e.g. Zalo, SMS, push",
            help="Enter channels separated by commas, or leave blank for defaults",
        )

    col3, col4 = st.columns(2)
    with col3:
        st.caption("**Level S:** in-app banners, push notifications")
    with col4:
        st.caption("**Level M:** + paid social, paid search")
    st.caption("**Level L:** + TVC, KOL, OOH, full funnel")

    generate = st.button("🚀 Generate Campaign Brief", type="primary", use_container_width=True)

# ── Generate ───────────────────────────────────────────────────

if generate:
    if not objective:
        st.error("Please enter a campaign objective")
        st.stop()

    with st.spinner("Designing campaign..."):
        try:
            from growth_mcp.tools.campaign import design_campaign, suggest_voucher

            # Parse custom channels
            channels_list = None
            if custom_channels:
                channels_list = [c.strip() for c in custom_channels.split(",") if c.strip()]

            # Generate brief
            brief = design_campaign(
                level=budget_level,
                objective=objective,
                target_segment=segment,
                channels=channels_list,
            )

            # Generate voucher suggestion
            # suggest_voucher only supports S and M budget levels
            voucher_budget = "M" if budget_level == "L" else budget_level
            voucher = suggest_voucher(
                segment=segment,
                objective=objective[:50],
                budget_level=voucher_budget,
            )

            st.balloons()
            st.header("📋 Campaign Brief")

            if "error" in brief:
                st.error(f"Error: {brief['error']}")
                st.stop()

            # ── Level info ────────────────────────────────────
            with st.container(border=True):
                level_info = brief.get("level_info", {})
                cols = st.columns(4)
                cols[0].metric("Budget Level", level_info.get("name", budget_level))
                cols[1].metric("Budget Range", level_info.get("budget_range", "—"))
                cols[2].metric("Timeline", level_info.get("timeline", "—"))
                cols[3].metric("Segment", segment)

            # ── Objective & Target ────────────────────────────
            with st.container(border=True):
                st.markdown(f"**Objective:** {brief.get('objective', objective)}")
                st.markdown(f"**Target:** {brief.get('target', segment)}")

            # ── Channels ───────────────────────────────────────
            channels = brief.get("channels", [])
            with st.container(border=True):
                st.markdown("**📡 Channels**")
                for ch in channels:
                    st.markdown(f"- {ch}")

            # ── Key Considerations ─────────────────────────────
            considerations = brief.get("key_considerations", [])
            with st.container(border=True):
                st.markdown("**💡 Key Considerations**")
                for c in considerations:
                    st.markdown(f"- {c}")

            # ── Campaign Memory References ────────────────────
            from growth_mcp.campaign_memory import search_campaigns, save_campaign

            memory_results = search_campaigns(
                objective=objective,
                segment=segment,
                budget_level=budget_level,
            )

            if memory_results:
                st.divider()
                st.subheader("📚 Campaign References")

                for mem in memory_results:
                    if mem["result"] == "fail":
                        with st.container(border=True):
                            st.markdown(f"**⚠️ Campaign fail — {mem.get('name', '')}**")
                            st.caption(f"Segment: {mem['segment']} · Budget: {mem['budget_level']} · {mem.get('duration', '')}")
                            for reason in mem.get("fail_reasons", []):
                                st.markdown(f"- ❌ {reason}")
                            st.markdown("**💡 Rút ra:**")
                            for l in mem.get("learnings", []):
                                st.markdown(f"- ✅ {l}")
                    else:
                        with st.container(border=True):
                            st.markdown(f"**✅ Campaign thành công — {mem.get('name', '')}**")
                            st.caption(f"Segment: {mem['segment']} · Budget: {mem['budget_level']} · {mem.get('duration', '')}")
                            metrics = mem.get("metrics", {})
                            if metrics:
                                cols = st.columns(len(metrics))
                                for i, (k, v) in enumerate(list(metrics.items())[:5]):
                                    cols[i].metric(k.replace("_", " ").title(), str(v))
                            st.markdown("**💡 Learnings từ campaign này:**")
                            for l in mem.get("learnings", []):
                                st.markdown(f"- 💡 {l}")

            # ── Voucher Suggestion ────────────────────────────
            st.divider()
            st.subheader("🎫 Suggested Voucher")

            if "error" not in voucher:
                # Voucher result has nested structure: {segment, objective, suggested_voucher: {type, value, ...}}
                v = voucher.get("suggested_voucher", voucher)
                with st.container(border=True):
                    cols = st.columns(2)
                    with cols[0]:
                        st.markdown(f"**Type:** {v.get('type', '—')}")
                        st.markdown(f"**Value:** {v.get('value', '—')}")
                    with cols[1]:
                        st.markdown(f"**Min spend:** {v.get('min_spend', '—')}")
                        st.markdown(f"**Expiry:** {v.get('expiry', '—')}")
                voucher_note = voucher.get("note")
                if voucher_note:
                    st.caption(f"📝 {voucher_note}")
            else:
                st.info(f"No voucher suggestion available: {voucher.get('error', '')}")

            # ── Full JSON ─────────────────────────────────────
            with st.expander("📄 Full campaign brief (JSON)", expanded=False):
                import json
                full = {**brief, "suggested_voucher": voucher}
                st.json(full)

            # ── Save to Memory ────────────────────────────────
            st.divider()
            with st.expander("💾 Save this campaign to memory", expanded=False):
                st.markdown("Sau khi campaign chạy xong, nhập kết quả để lần sau app tự động tham khảo.")
                with st.form("save_campaign_form"):
                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        camp_name = st.text_input("Campaign name", value=brief.get("objective", ""))
                        camp_result = st.selectbox("Result", ["success", "fail"])
                        camp_budget = st.text_input("Actual budget spent", placeholder="e.g. 35M VND")
                    with col_s2:
                        camp_reach = st.text_input("Reach", placeholder="e.g. 120K users")
                        camp_conv = st.text_input("Conversion rate", placeholder="e.g. 8.2%")
                        camp_roi = st.text_input("ROI", placeholder="e.g. 3.2x")
                    camp_learnings = st.text_area("Learnings (1 learning per line)", placeholder="What worked? What didn't?")
                    camp_fails = st.text_area("Failures to avoid (1 per line)", placeholder="What went wrong?")

                    saved = st.form_submit_button("💾 Save to Campaign Memory", type="primary", use_container_width=True)

                if saved:
                    new_camp = {
                        "id": f"camp-{camp_name[:20].lower().replace(' ', '-')}",
                        "name": camp_name,
                        "objective": objective,
                        "segment": segment,
                        "budget_level": budget_level,
                        "budget": camp_budget,
                        "channels": channels_list or brief.get("channels", []),
                        "voucher": v if "error" not in voucher else {},
                        "result": camp_result,
                        "metrics": {
                            "reach": camp_reach,
                            "conversion_rate": camp_conv,
                            "ROI": camp_roi,
                        },
                        "learnings": [l.strip() for l in camp_learnings.split("\n") if l.strip()],
                        "fail_reasons": [l.strip() for l in camp_fails.split("\n") if l.strip()],
                        "date": "2026-07-04",
                    }
                    filename = save_campaign(new_camp)
                    st.success(f"✅ Saved! File: `{filename}` — App sẽ tham khảo campaign này trong lần generate sau.")

            # ── Reference ─────────────────────────────────────
            prompt_ref = brief.get("prompt_reference")
            if prompt_ref:
                st.divider()
                st.caption(f"📖 Prompt reference: [{prompt_ref}]({prompt_ref})")

        except ImportError as e:
            st.error(f"Could not import growth_mcp module: {e}")
            st.info("Install growth-mcp: `pip install -e .` in the repo root")
        except Exception as e:
            st.error(f"Error generating brief: {e}")

else:
    st.info("👆 Fill in campaign info and click **Generate Campaign Brief**")
