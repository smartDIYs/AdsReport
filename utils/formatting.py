import pandas as pd


def format_currency(value) -> str:
    """通貨フォーマット: ¥1,234"""
    if pd.isna(value) or value is None:
        return "-"
    return f"¥{value:,.0f}"


def format_percent(value) -> str:
    """パーセントフォーマット: 1.23%"""
    if pd.isna(value) or value is None:
        return "-"
    return f"{value:.2f}%"


def format_number(value) -> str:
    """数値フォーマット: 1,234"""
    if pd.isna(value) or value is None:
        return "-"
    return f"{value:,.0f}"


def format_decimal(value) -> str:
    """小数フォーマット: 1.23"""
    if pd.isna(value) or value is None:
        return "-"
    return f"{value:,.2f}"


def safe_divide(numerator, denominator, default=None):
    """ゼロ除算安全な割り算"""
    if denominator is None or denominator == 0:
        return default
    return numerator / denominator
