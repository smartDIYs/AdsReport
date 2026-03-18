from abc import ABC, abstractmethod
from datetime import date

import pandas as pd

from config.settings import REPORT_COLUMNS


class AdsFetcherBase(ABC):
    """広告プラットフォームAPI共通基底クラス"""

    platform_name: str = ""

    @abstractmethod
    def fetch_campaign_report(
        self, start_date: date, end_date: date
    ) -> pd.DataFrame:
        """キャンペーンレポートを取得し、統一スキーマのDataFrameを返す"""
        ...

    def _empty_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(columns=REPORT_COLUMNS)

    def _validate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """統一スキーマに合わせてカラムを整える"""
        for col in REPORT_COLUMNS:
            if col not in df.columns:
                df[col] = None
        df = df[REPORT_COLUMNS]
        numeric_cols = ["impressions", "clicks", "cost", "conversions"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df
