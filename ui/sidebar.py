import calendar
from datetime import date, timedelta

import streamlit as st

from config.settings import CATEGORIES, DATE_PRESETS, PLATFORMS


def _days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def render_sidebar() -> dict:
    """サイドバーUIを描画し、フィルター条件を返す"""
    st.sidebar.header("フィルター")

    # 期間選択
    st.sidebar.subheader("期間")
    preset = st.sidebar.selectbox("プリセット", list(DATE_PRESETS.keys()))

    today = date.today()
    if DATE_PRESETS[preset] == "this_month":
        start = today.replace(day=1)
        end = today
    elif DATE_PRESETS[preset] == "last_month":
        first_of_this_month = today.replace(day=1)
        end = first_of_this_month - timedelta(days=1)
        start = end.replace(day=1)
    elif DATE_PRESETS[preset] == "two_months_ago":
        first_of_this_month = today.replace(day=1)
        last_month_end = first_of_this_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        end = last_month_start - timedelta(days=1)
        start = end.replace(day=1)
    elif DATE_PRESETS[preset] == "last_7_days":
        start = today - timedelta(days=6)
        end = today
    elif DATE_PRESETS[preset] == "last_30_days":
        start = today - timedelta(days=29)
        end = today
    else:
        default_start = st.session_state.get("custom_start", today.replace(day=1))
        default_end = st.session_state.get("custom_end", today)

        years = list(range(2020, today.year + 1))
        months = list(range(1, 13))

        days_31 = list(range(1, 32))

        with st.sidebar.form("custom_date_form"):
            st.markdown("**開始日**")
            s_year = st.selectbox("年", years, index=years.index(default_start.year), key="sy")
            s_month = st.selectbox("月", months, index=default_start.month - 1, key="sm")
            s_day = st.selectbox("日", days_31, index=default_start.day - 1, key="sd")

            st.markdown("---")
            st.markdown("**終了日**")
            e_year = st.selectbox("年", years, index=years.index(default_end.year), key="ey")
            e_month = st.selectbox("月", months, index=default_end.month - 1, key="em")
            e_day = st.selectbox("日", days_31, index=default_end.day - 1, key="ed")

            submitted = st.form_submit_button("適用", type="primary", use_container_width=True)

        if submitted:
            # 存在しない日はその月の末日に補正
            s_day = min(s_day, _days_in_month(s_year, s_month))
            e_day = min(e_day, _days_in_month(e_year, e_month))
            start = date(s_year, s_month, s_day)
            end = date(e_year, e_month, e_day)
            st.session_state["custom_start"] = start
            st.session_state["custom_end"] = end
        else:
            start = default_start
            end = default_end

        st.sidebar.caption(
            f"{start.year}/{start.month}/{start.day} 〜 {end.year}/{end.month}/{end.day}"
        )

    # プラットフォーム選択
    st.sidebar.subheader("プラットフォーム")
    selected_platforms = st.sidebar.multiselect(
        "表示するプラットフォーム",
        PLATFORMS,
        default=PLATFORMS,
    )

    # カテゴリ選択
    st.sidebar.subheader("カテゴリ")
    selected_categories = st.sidebar.multiselect(
        "表示するカテゴリ",
        CATEGORIES + ["未分類"],
        default=CATEGORIES + ["未分類"],
    )

    return {
        "start_date": start,
        "end_date": end,
        "platforms": selected_platforms,
        "categories": selected_categories,
    }
