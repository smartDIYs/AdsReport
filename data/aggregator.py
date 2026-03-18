from datetime import date

import pandas as pd
import streamlit as st

from config.settings import CACHE_TTL
from data.category_classifier import apply_categories
from data.fetchers.google_ads import GoogleAdsFetcher
from data.fetchers.microsoft_ads import MicrosoftAdsFetcher
from data.fetchers.yahoo_ads import YahooAdsFetcher


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_all_platforms(
    start_date: date,
    end_date: date,
    platforms: list[str],
) -> pd.DataFrame:
    """選択されたプラットフォームからデータを取得し統合する"""
    fetchers = {
        "Google": GoogleAdsFetcher,
        "Yahoo": YahooAdsFetcher,
        "Microsoft": MicrosoftAdsFetcher,
    }

    dfs = []
    for platform in platforms:
        fetcher_class = fetchers.get(platform)
        if not fetcher_class:
            continue
        try:
            fetcher = fetcher_class()
            df = fetcher.fetch_campaign_report(start_date, end_date)
            if not df.empty:
                dfs.append(df)
        except Exception as e:
            st.warning(f"{platform} Ads のデータ取得に失敗しました: {e}")

    if not dfs:
        from config.settings import REPORT_COLUMNS

        return pd.DataFrame(columns=REPORT_COLUMNS + ["category"])

    combined = pd.concat(dfs, ignore_index=True)
    combined = apply_categories(combined)
    return combined
