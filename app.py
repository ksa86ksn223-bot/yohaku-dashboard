import streamlit as st
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="YOHAKU OS", page_icon="🏛️", layout="wide")

# --- Supabase接続 ---
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
        st.error(f"Supabase接続エラー: {e}")

# --- サイドバー ---
st.sidebar.title("🏛️ YOHAKU OS")
st.sidebar.caption("Civilization OS v2.1")
st.sidebar.divider()
st.sidebar.metric("Governance Phase", "Phase 2")
st.sidebar.metric("稼働Agent数", 16)
st.sidebar.divider()
st.sidebar.caption(f"最終更新: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
if st.sidebar.button("🔄 更新"):
    st.rerun()

# --- メイン ---
st.title("🏛️ YOHAKU Civilization OS — Dashboard")

if not supabase_client:
    st.warning("⚠️ Supabaseに接続できません。Secretsを確認してください。")
    st.stop()

# --- データ取得 ---
try:
    summary = supabase_client.table("os_summary").select("*").order("created_at", desc=True).limit(1).execute()
    proposals = supabase_client.table("ai_proposals").select("*").eq("status", "未確認").order("created_at", desc=True).limit(10).execute()
    psychology = supabase_client.table("customer_psychology").select("*").order("created_at", desc=True).limit(5).execute()
    history = supabase_client.table("os_summary").select("*").order("created_at", desc=True).limit(30).execute()
except Exception as e:
    st.error(f"データ取得エラー: {e}")
    st.stop()

# --- 上段: OS状態 ---
latest = summary.data[0] if summary.data else {}
col1, col2, col3 = st.columns(3)
with col1:
    status = latest.get("status", "不明")
    if "正常" in status:
        st.success(f"OS状態: {status}")
    elif "警告" in status:
        st.warning(f"OS状態: {status}")
    else:
        st.error(f"OS状態: {status}")
with col2:
    st.metric("稼働Agent数", latest.get("active_agents", 0))
with col3:
    st.metric("今日のエラー数", latest.get("error_count", 0))

st.divider()

# --- 中段 ---
left, right = st.columns(2)

with left:
    st.subheader("💡 未確認のAI提案")
    if proposals.data:
        for p in proposals.data:
            with st.expander(f"📌 {p.get('title', '無題')}"):
                st.write(p.get("content", ""))
                st.caption(f"提案元: {p.get('source', '')} | Ponoスコア: {p.get('pono_score', '-')}")
    else:
        st.info("未確認の提案はありません")

with right:
    st.subheader("🧠 最新の顧客心理分析")
    if psychology.data:
        for c in psychology.data:
            with st.expander(f"👤 {c.get('customer_name', '名前なし')} ({c.get('customer_type', '')})"):
                st.write(c.get("analysis", ""))
                st.caption(f"返信案: {c.get('reply_options', '')}")
    else:
        st.info("顧客心理分析データはまだありません")

st.divider()

# --- 下段: 時系列 ---
st.subheader("📈 OS状態の推移（直近30日）")
if history.data:
    import pandas as pd
    df = pd.DataFrame(history.data)
    if "created_at" in df.columns and "error_count" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"])
        df = df.sort_values("created_at")
        st.line_chart(df.set_index("created_at")[["error_count", "active_agents"]])
    else:
        st.info("グラフ表示に必要なデータがありません")
else:
    st.info("まだ十分なデータがありません")
```

**ステップ4：保存してコミット＆プッシュ**
```
git add .
```
```
git commit -m "fix: rebuild app.py with proper st.secrets handling"
```
```
git push