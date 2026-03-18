import pandas as pd
import streamlit as st

from utils.formatting import (
    format_currency,
    format_decimal,
    format_number,
    format_percent,
    safe_divide,
)


def render_kpi_cards(df: pd.DataFrame) -> None:
    """KPIサマリーカードを表示する"""
    if df.empty:
        st.info("データがありません。")
        return

    total_impressions = df["impressions"].sum()
    total_clicks = df["clicks"].sum()
    total_cost = df["cost"].sum()
    total_conversions = df["conversions"].sum()

    ctr = safe_divide(total_clicks, total_impressions)
    cpc = safe_divide(total_cost, total_clicks)
    cvr = safe_divide(total_conversions, total_clicks)
    cpa = safe_divide(total_cost, total_conversions)

    row1 = st.columns(4)
    with row1[0]:
        st.metric("表示回数", format_number(total_impressions), border=True)
    with row1[1]:
        st.metric("クリック数", format_number(total_clicks), border=True)
    with row1[2]:
        st.metric("CTR", format_percent(ctr * 100 if ctr else None), border=True)
    with row1[3]:
        st.metric("CPC", format_currency(cpc), border=True)

    row2 = st.columns(4)
    with row2[0]:
        st.metric("費用", format_currency(total_cost), border=True)
    with row2[1]:
        st.metric("CV数", format_decimal(total_conversions), border=True)
    with row2[2]:
        st.metric("CV率", format_percent(cvr * 100 if cvr else None), border=True)
    with row2[3]:
        st.metric("CPA", format_currency(cpa), border=True)
