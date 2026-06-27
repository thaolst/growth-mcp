"""Growth MCP Web UI — AI tools for growth marketers."""

import streamlit as st

# ── Page config ────────────────────────────────────────────────

st.set_page_config(
    page_title="Growth MCP — AI Tools for Marketers",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ────────────────────────────────────────────────────

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
    st.caption("[GitHub](https://github.com/thaolst/growth-mcp) · [PyPI](https://pypi.org/project/growth-mcp/)")

# ── Home page ──────────────────────────────────────────────────

col1, col2 = st.columns([2, 1])

with col1:
    st.title("📈 Growth MCP")
    st.markdown("""
    ### AI-powered growth marketing tools
    
    Upload your campaign data and get instant analysis — no CLI, no code needed.
    
    **How it works:**
    1. Choose a tool from the sidebar
    2. Upload your CSV or enter campaign parameters
    3. Get analysis with actionable recommendations
    """)

with col2:
    st.markdown("### Quick Stats")
    st.metric("Tools Available", "25", "in MCP server")
    st.metric("Web UI Tools", "1", "growing daily")

st.divider()

st.markdown("### 🚀 Available Tools")

tools = [
    ("📊 Retention Analyzer", "Upload cohort CSV → analyze retention drops → get intervention recommendations", "✅ Active"),
    ("📝 Campaign Brief Generator", "Coming soon — input goal+budget → complete campaign brief", "⏳ Building"),
    ("🎫 Voucher Designer", "Coming soon — design voucher mechanics for any segment", "⏳ Planned"),
    ("🧪 A/B Test Analyzer", "Coming soon — upload experiment CSV → significance test", "⏳ Planned"),
]

for name, desc, status in tools:
    with st.container(border=True):
        col_left, col_right = st.columns([3, 1])
        col_left.markdown(f"**{name}**  \n{desc}")
        col_right.markdown(f"*{status}*")

st.divider()
st.caption("Growth MCP v1.2.0 — Built on [Streamlit](https://streamlit.io) · Data stays local, nothing is sent externally.")
