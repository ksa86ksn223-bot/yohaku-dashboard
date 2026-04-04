"""
py/dashboard/app.py
====================
YOHAKU Civilization OS — Streamlit ダッシュボード v1

起動:
  cd py && streamlit run dashboard/app.py
  # → http://localhost:8501/

環境変数:
  SUPABASE_URL       Supabase Project URL（必須）
  SUPABASE_ANON_KEY  Supabase Anon Key（必須）
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# ページ設定
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="YOHAKU OS Dashboard",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Supabase 接続
# ---------------------------------------------------------------------------

@st.cache_resource
def get_supabase_client():
    """Supabase クライアントを返す（接続エラー時は None）。

    優先順位: st.secrets → 環境変数
    Streamlit Community Cloud では st.secrets に設定し、
    ローカル / GitHub Actions では環境変数を使用する。
    """
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except (KeyError, FileNotFoundError):
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_ANON_KEY", "")
    if not url or not key:
        return None
    try:
        from supabase import create_client  # noqa: PLC0415
        return create_client(url, key)
    except Exception as e:
        st.error(f"Supabase 接続エラー: {e}")
        return None


def fetch_latest_os_summary(client) -> dict | None:
    """os_summary テーブルから最新レコードを取得する。"""
    try:
        result = (
            client.table("os_summary")
            .select("*")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = result.data
        return rows[0] if rows else None
    except Exception as e:
        st.warning(f"os_summary 取得エラー: {e}")
        return None


def fetch_os_summary_history(client, days: int = 30) -> pd.DataFrame:
    """os_summary の直近 N 日分を DataFrame で返す。"""
    try:
        result = (
            client.table("os_summary")
            .select("created_at, status, error_count, active_agents, pending_proposals")
            .order("created_at", desc=False)
            .limit(days)
            .execute()
        )
        rows = result.data
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["created_at"] = pd.to_datetime(df["created_at"])
        df = df.set_index("created_at")
        return df
    except Exception as e:
        st.warning(f"os_summary 履歴取得エラー: {e}")
        return pd.DataFrame()


def fetch_pending_proposals(client) -> pd.DataFrame:
    """ai_proposals から status=未確認 を取得する。"""
    try:
        result = (
            client.table("ai_proposals")
            .select("created_at, title, source, pono_score, status")
            .eq("status", "未確認")
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        rows = result.data
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%m/%d %H:%M")
        df = df.rename(columns={
            "created_at": "日時",
            "title": "タイトル",
            "source": "ソース",
            "pono_score": "Ponoスコア",
            "status": "ステータス",
        })
        return df
    except Exception as e:
        st.warning(f"ai_proposals 取得エラー: {e}")
        return pd.DataFrame()


def fetch_psychology_stats(client) -> dict[str, int]:
    """customer_psychology_stats VIEWから顧客タイプ別累計件数を取得する。

    個人情報（顧客名・分析テキスト）は一切取得しない。
    VIEWは月別集計なので、全月を合算して累計を返す。
    VIEWが存在しない場合は空辞書を返す（エラーにしない）。

    Returns:
        {"安心重視": 3, "迷い中": 1, ...}
    """
    try:
        result = (
            client.table("customer_psychology_stats")
            .select("customer_type, count")
            .execute()
        )
        rows = result.data
        if not rows:
            return {}
        counts: dict[str, int] = {}
        for row in rows:
            t = row.get("customer_type") or "不明"
            counts[t] = counts.get(t, 0) + int(row.get("count") or 0)
        return counts
    except Exception as e:
        st.warning(f"customer_psychology 統計取得エラー: {e}")
        return {}


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

def render_status_badge(status: str | None) -> str:
    """ステータス文字列から表示用バッジを返す。

    os_summary_agent.py の determine_status() は "🟢 正常" のように
    絵文字付きで値を保存するため、既に絵文字が含まれる場合は追加しない。
    """
    if status is None:
        return "⚪ データなし"
    # 既に絵文字が先頭についている場合はそのまま返す
    if status.startswith(("🔴", "🟡", "🟢", "⚪")):
        return status
    # 絵文字なし（旧データ互換）の場合はキーワードで判定して付与
    if "🔴" in status or "異常" in status:
        return f"🔴 {status}"
    if "🟡" in status or "警告" in status:
        return f"🟡 {status}"
    return f"🟢 {status}"


def main() -> None:
    client = get_supabase_client()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ── サイドバー ────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("🏛️ YOHAKU OS")
        st.caption("Civilization OS v2.1")
        st.divider()

        if client:
            latest = fetch_latest_os_summary(client)
        else:
            latest = None

        phase = latest.get("phase", "Phase 2") if latest else "Phase 2"
        agents = latest.get("active_agents", 16) if latest else 16

        st.metric("Governance Phase", phase)
        st.metric("稼働Agent数", agents)
        st.divider()
        st.caption(f"最終更新: {now_str}")

        if st.button("🔄 更新"):
            st.cache_resource.clear()
            st.rerun()

    # ── メインコンテンツ ──────────────────────────────────────────────────
    st.title("🏛️ YOHAKU Civilization OS — Dashboard")

    if not client:
        st.error(
            "⚠️ Supabase に接続できません。\n\n"
            "環境変数 `SUPABASE_URL` と `SUPABASE_ANON_KEY` を設定してください。"
        )
        st.code(
            "export SUPABASE_URL=https://xxxx.supabase.co\n"
            "export SUPABASE_ANON_KEY=your_anon_key\n"
            "streamlit run dashboard/app.py"
        )
        return

    latest = fetch_latest_os_summary(client)

    # ── 上段: OS状態 4カラム ───────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_display = latest.get("status", "データなし") if latest else "データなし"
        st.metric(
            label="OS状態",
            value=render_status_badge(status_display),
        )

    with col2:
        active = latest.get("active_agents", 0) if latest else 0
        st.metric(label="稼働Agent数", value=f"{active} 本")

    with col3:
        errors = latest.get("error_count", 0) if latest else 0
        delta_color = "inverse" if errors > 0 else "off"
        st.metric(label="今日のエラー数", value=errors, delta_color=delta_color)

    with col4:
        if latest:
            rate = latest.get("approval_rate")
            approved = latest.get("approved_count", 0)
            rejected = latest.get("rejected_count", 0)
            if rate is not None:
                rate_pct = f"{rate * 100:.1f}%"
                rate_sub = f"承認{approved}/却下{rejected}"
            else:
                rate_pct = "N/A"
                rate_sub = f"承認{approved}/却下{rejected}"
        else:
            rate_pct = "N/A"
            rate_sub = "承認0/却下0"
        st.metric(label="承認率", value=rate_pct, help=rate_sub)

    st.divider()

    # ── 中段: 提案リスト + 顧客分析 ──────────────────────────────────
    mid_left, mid_right = st.columns([3, 2])

    with mid_left:
        st.subheader("💡 未確認のAI提案")
        proposals_df = fetch_pending_proposals(client)
        if proposals_df.empty:
            st.info("未確認の提案はありません。")
        else:
            st.dataframe(
                proposals_df,
                use_container_width=True,
                hide_index=True,
            )

    with mid_right:
        st.subheader("🧠 顧客タイプ別件数")
        psych_stats = fetch_psychology_stats(client)
        if not psych_stats:
            st.info("顧客心理分析データがありません。")
        else:
            total = sum(psych_stats.values())
            st.caption(f"累計 {total} 件")
            for ctype, count in sorted(psych_stats.items(), key=lambda x: -x[1]):
                st.metric(label=ctype, value=f"{count} 件")

    st.divider()

    # ── 下段: OS状態時系列グラフ ─────────────────────────────────────
    st.subheader("📈 OS状態の推移（直近30日）")
    history_df = fetch_os_summary_history(client, days=30)

    if history_df.empty:
        st.info("履歴データがまだありません。")
    else:
        numeric_cols = [c for c in ["error_count", "active_agents", "pending_proposals"] if c in history_df.columns]
        if numeric_cols:
            st.line_chart(history_df[numeric_cols])
        else:
            st.info("表示できる数値データがありません。")


if __name__ == "__main__":
    main()
