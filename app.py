import streamlit as st
import os
from datetime import datetime

st.set_page_config(page_title="YOHAKU OS", page_icon="🏛️", layout="wide")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
except Exception:
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

supabase_client = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        st.error(f"Supabase error: {e}")

st.sidebar.title("🏛️ YOHAKU OS")
st.sidebar.caption("Civilization OS v2.1")
st.sidebar.divider()
st.sidebar.metric("Governance Phase", "Phase 2")
st.sidebar.metric("Agent count", 16)
st.sidebar.divider()
st.sidebar.caption(f"Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
if st.sidebar.button("Refresh"):
    st.rerun()

st.title("🏛️ YOHAKU Civilization OS — Dashboard")

if not supabase_client:
    st.warning("Cannot connect to Supabase. Check Secrets settings.")
    st.stop()

try:
    summary = supabase_client.table("os_summary").select("*").order("created_at", desc=True).limit(1).execute()
    proposals = supabase_client.table("ai_proposals").select("*").eq("status", "未確認").order("created_at", desc=True).limit(10).execute()
    psychology = supabase_client.table("customer_psychology").select("*").order("created_at", desc=True).limit(5).execute()
except Exception as e:
    st.error(f"Data error: {e}")
    st.stop()

latest = summary.data[0] if summary.data else {}
c1, c2, c3 = st.columns(3)
with c1:
    s = latest.get("status", "unknown")
    if "正常" in s:
        st.success(f"OS: {s}")
    elif "警告" in s:
        st.warning(f"OS: {s}")
    else:
        st.error(f"OS: {s}")
with c2:
    st.metric("Agents", latest.get("active_agents", 0))
with c3:
    st.metric("Errors", latest.get("error_count", 0))

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("💡 AI Proposals")
    if proposals.data:
        for p in proposals.data:
            with st.expander(p.get("title", "untitled")):
                st.write(p.get("content", ""))
    else:
        st.info("No pending proposals")
with right:
    st.subheader("🧠 Customer Psychology")
    if psychology.data:
        for c in psychology.data:
            with st.expander(f"{c.get('customer_name', 'N/A')} ({c.get('customer_type', '')})"):
                st.write(c.get("analysis", ""))
    else:
        st.info("No data yet")