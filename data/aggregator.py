from datetime import date

import pandas as pd
import streamlit as st

from config.settings import CACHE_TTL, REPORT_COLUMNS
from data.category_classifier import apply_categories
from data.fetchers.google_ads import GoogleAdsFetcher
from data.fetchers.microsoft_ads import MicrosoftAdsFetcher
from data.fetchers.yahoo_ads import YahooAdsFetcher


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _fetch_raw(
    start_date: date,
    end_date: date,
    platforms: list[str],
) -> pd.DataFrame:
    """各プラットフォームAPIから生データを取得して統合する（API通信のみキャッシュする）"""
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
        return pd.DataFrame(columns=REPORT_COLUMNS)

    return pd.concat(dfs, ignore_index=True)


def fetch_all_platforms(
    start_date: date,
    end_date: date,
    platforms: list[str],
) -> pd.DataFrame:
    """選択されたプラットフォームからデータを取得し、カテゴリを付与して返す。

    カテゴリ付与はキャッシュ対象外に置いている。キャッシュ済みの分類結果が
    残ると category_mapping.yaml を更新しても反映されないため、分類だけは
    毎回やり直す（対象は1か月あたり数千行程度で処理コストは無視できる）。
    """
    df = _fetch_raw(start_date, end_date, platforms).copy()
    return apply_categories(df)
