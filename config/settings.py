import os
from pathlib import Path

try:
    import streamlit as st
    _secrets = dict(st.secrets) if st.secrets else {}
except Exception:
    _secrets = {}

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_secret(key: str, default: str = "") -> str:
    """st.secrets → 環境変数 → デフォルト値 の順に取得する"""
    return _secrets.get(key, os.getenv(key, default))


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CATEGORY_MAPPING_FILE = CONFIG_DIR / "category_mapping.yaml"

# カテゴリ定義
CATEGORIES = ["LC", "LM", "PL", "SCL", "SLW"]
UNCATEGORIZED = "未分類"

# プラットフォーム
PLATFORMS = ["Google", "Yahoo", "Microsoft"]

# 期間プリセット
DATE_PRESETS = {
    "今月": "this_month",
    "先月": "last_month",
    "先々月": "two_months_ago",
    "直近7日": "last_7_days",
    "直近30日": "last_30_days",
    "カスタム": "custom",
}

# KPI定義
KPI_COLUMNS = [
    "impressions",
    "clicks",
    "ctr",
    "cpc",
    "cost",
    "conversions",
    "conversion_rate",
    "cpa",
]

KPI_LABELS = {
    "impressions": "表示回数",
    "clicks": "クリック数",
    "ctr": "CTR",
    "cpc": "CPC",
    "cost": "費用",
    "conversions": "CV数",
    "conversion_rate": "CV率",
    "cpa": "CPA",
}

# 統一データスキーマ
REPORT_COLUMNS = [
    "platform",
    "campaign_id",
    "campaign_name",
    "campaign_type",
    "ad_group_name",
    "date",
    "impressions",
    "clicks",
    "cost",
    "conversions",
]

# Google Ads 認証情報
GOOGLE_ADS_CONFIG = {
    "developer_token": _get_secret("GOOGLE_ADS_DEVELOPER_TOKEN"),
    "client_id": _get_secret("GOOGLE_ADS_CLIENT_ID"),
    "client_secret": _get_secret("GOOGLE_ADS_CLIENT_SECRET"),
    "refresh_token": _get_secret("GOOGLE_ADS_REFRESH_TOKEN"),
    "login_customer_id": _get_secret("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
    "use_proto_plus": True,
}

# Yahoo Ads 認証情報
YAHOO_ADS_CONFIG = {
    "client_id": _get_secret("YAHOO_ADS_CLIENT_ID"),
    "client_secret": _get_secret("YAHOO_ADS_CLIENT_SECRET"),
    "refresh_token": _get_secret("YAHOO_ADS_REFRESH_TOKEN"),
    "account_id": _get_secret("YAHOO_ADS_ACCOUNT_ID"),
    "mcc_account_id": _get_secret("YAHOO_ADS_MCC_ACCOUNT_ID"),
}
YAHOO_ADS_TOKEN_URL = "https://biz-oauth.yahoo.co.jp/oauth/v1/token"
YAHOO_ADS_API_BASE = "https://ads-search.yahooapis.jp/api/v19/"

# Microsoft Ads 認証情報
MICROSOFT_ADS_CONFIG = {
    "client_id": _get_secret("MICROSOFT_ADS_CLIENT_ID"),
    "developer_token": _get_secret("MICROSOFT_ADS_DEVELOPER_TOKEN"),
    "refresh_token": _get_secret("MICROSOFT_ADS_REFRESH_TOKEN"),
    "account_id": _get_secret("MICROSOFT_ADS_ACCOUNT_ID"),
    "customer_id": _get_secret("MICROSOFT_ADS_CUSTOMER_ID"),
}

# キャッシュTTL（秒）
CACHE_TTL = 3600
