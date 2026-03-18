import pandas as pd
import streamlit as st

from ui.charts import bar_chart_cost_conversions
from utils.formatting import (
    format_currency,
    format_decimal,
    format_number,
    format_percent,
    safe_divide,
)


def _build_campaign_summary(df: pd.DataFrame) -> pd.DataFrame:
    """キャンペーン別集計テーブルを作成する"""
    grouped = (
        df.groupby(["platform", "campaign_name", "category"])
        .agg(
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            cost=("cost", "sum"),
            conversions=("conversions", "sum"),
        )
        .reset_index()
    )

    grouped["ctr"] = grouped.apply(
        lambda r: safe_divide(r["clicks"], r["impressions"]), axis=1
    )
    grouped["cpc"] = grouped.apply(
        lambda r: safe_divide(r["cost"], r["clicks"]), axis=1
    )
    grouped["cvr"] = grouped.apply(
        lambda r: safe_divide(r["conversions"], r["clicks"]), axis=1
    )
    grouped["cpa"] = grouped.apply(
        lambda r: safe_divide(r["cost"], r["conversions"]), axis=1
    )
    return grouped


def _add_total_row(df: pd.DataFrame) -> pd.DataFrame:
    """合計行を追加する（CTR等は加重平均で再計算）"""
    total_impressions = df["impressions"].sum()
    total_clicks = df["clicks"].sum()
    total_cost = df["cost"].sum()
    total_conversions = df["conversions"].sum()

    total = pd.DataFrame(
        [
            {
                "platform": "",
                "campaign_name": "合計",
                "category": "",
                "impressions": total_impressions,
                "clicks": total_clicks,
                "cost": total_cost,
                "conversions": total_conversions,
                "ctr": safe_divide(total_clicks, total_impressions),
                "cpc": safe_divide(total_cost, total_clicks),
                "cvr": safe_divide(total_conversions, total_clicks),
                "cpa": safe_divide(total_cost, total_conversions),
            }
        ]
    )
    return pd.concat([df, total], ignore_index=True)


def _format_display(df: pd.DataFrame) -> pd.DataFrame:
    """表示用にフォーマットする"""
    display = df.copy()
    display["impressions"] = display["impressions"].apply(format_number)
    display["clicks"] = display["clicks"].apply(format_number)
    display["cost"] = display["cost"].apply(format_currency)
    display["conversions"] = display["conversions"].apply(format_decimal)
    display["ctr"] = display["ctr"].apply(lambda v: format_percent(v * 100 if v else None))
    display["cpc"] = display["cpc"].apply(format_currency)
    display["cvr"] = display["cvr"].apply(lambda v: format_percent(v * 100 if v else None))
    display["cpa"] = display["cpa"].apply(format_currency)

    display = display.rename(
        columns={
            "platform": "プラットフォーム",
            "campaign_name": "キャンペーン",
            "category": "カテゴリ",
            "impressions": "表示回数",
            "clicks": "クリック数",
            "cost": "費用",
            "conversions": "CV数",
            "ctr": "CTR",
            "cpc": "CPC",
            "cvr": "CV率",
            "cpa": "CPA",
        }
    )
    col_order = ["プラットフォーム", "キャンペーン", "カテゴリ", "表示回数", "クリック数", "CTR", "CPC", "費用", "CV数", "CV率", "CPA"]
    display = display[[c for c in col_order if c in display.columns]]
    return display


def render_campaign_view(df: pd.DataFrame) -> None:
    """キャンペーン別ビューを表示する"""
    if df.empty:
        st.info("データがありません。")
        return

    summary = _build_campaign_summary(df)
    summary_with_total = _add_total_row(summary)
    display = _format_display(summary_with_total)

    st.dataframe(display, use_container_width=True, hide_index=True)

    # チャート
    bar_chart_cost_conversions(summary, "campaign_name", "キャンペーン")

    # CSVエクスポート
    csv = summary_with_total.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "CSVダウンロード（キャンペーン別）",
        csv,
        "campaign_report.csv",
        "text/csv",
    )
