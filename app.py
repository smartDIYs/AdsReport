import streamlit as st

from data.aggregator import fetch_all_platforms
from ui.campaign_view import render_campaign_view
from ui.category_view import render_category_view
from ui.kpi_cards import render_kpi_cards
from ui.sidebar import render_sidebar

st.set_page_config(
    page_title="広告レポートダッシュボード",
    page_icon="📊",
    layout="wide",
)


def check_password():
    """パスワード認証を行う。認証済みならTrueを返す。"""
    if st.session_state.get("authenticated"):
        return True

    st.markdown(
        """
        <div style="display:flex; justify-content:center; align-items:center; height:400px;">
            <div style="text-align:center; width:350px;">
                <h2>広告レポートダッシュボード</h2>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        password = st.text_input("パスワードを入力してください", type="password")
        if st.button("ログイン", type="primary", use_container_width=True):
            correct = st.secrets.get("APP_PASSWORD", "")
            if password == correct:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("パスワードが正しくありません。")
    return False


if not check_password():
    st.stop()

st.title("広告レポートダッシュボード")

# サイドバー
filters = render_sidebar()

# データ取得
if not filters["platforms"]:
    st.warning("プラットフォームを1つ以上選択してください。")
    st.stop()

loading_placeholder = st.empty()
with loading_placeholder.container():
    st.markdown(
        """
        <div style="display:flex; justify-content:center; align-items:center; height:300px;">
            <div style="text-align:center;">
                <div style="font-size:24px; font-weight:bold; color:#4A90D9;">
                    広告データを取得中です...<br>しばらくお待ちください
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    df = fetch_all_platforms(
        filters["start_date"],
        filters["end_date"],
        filters["platforms"],
    )
loading_placeholder.empty()

# カテゴリフィルター適用
if "category" in df.columns and not df.empty:
    df = df[df["category"].isin(filters["categories"])]

# KPIカード
render_kpi_cards(df)

st.divider()

# タブ表示
tab_campaign, tab_category = st.tabs(["キャンペーン別", "カテゴリ別"])

with tab_campaign:
    render_campaign_view(df)

with tab_category:
    render_category_view(df)

