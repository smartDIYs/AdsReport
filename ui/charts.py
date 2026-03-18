import pandas as pd
import plotly.express as px
import streamlit as st


def bar_chart_cost_conversions(df: pd.DataFrame, group_col: str, title: str) -> None:
    """費用・CV数の棒グラフを並べて表示する"""
    if df.empty:
        return

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            df,
            x=group_col,
            y="cost",
            title=f"{title} - 費用",
            labels={group_col: title, "cost": "費用 (¥)"},
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            df,
            x=group_col,
            y="conversions",
            title=f"{title} - CV数",
            labels={group_col: title, "conversions": "CV数"},
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)


def pie_chart_cost(df: pd.DataFrame, group_col: str, title: str) -> None:
    """費用配分の円グラフを表示する"""
    if df.empty:
        return

    fig = px.pie(
        df,
        names=group_col,
        values="cost",
        title=f"{title} - 費用配分",
    )
    st.plotly_chart(fig, use_container_width=True)
