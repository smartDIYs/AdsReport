import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

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
    "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
    "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID", ""),
    "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET", ""),
    "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN", ""),
    "login_customer_id": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", ""),
    "use_proto_plus": True,
}

# Yahoo Ads 認証情報
YAHOO_ADS_CONFIG = {
    "client_id": os.getenv("YAHOO_ADS_CLIENT_ID", ""),
    "client_secret": os.getenv("YAHOO_ADS_CLIENT_SECRET", ""),
    "refresh_token": os.getenv("YAHOO_ADS_REFRESH_TOKEN", ""),
    "account_id": os.getenv("YAHOO_ADS_ACCOUNT_ID", ""),
    "mcc_account_id": os.getenv("YAHOO_ADS_MCC_ACCOUNT_ID", ""),
}
YAHOO_ADS_TOKEN_URL = "https://biz-oauth.yahoo.co.jp/oauth/v1/token"
YAHOO_ADS_API_BASE = "https://ads-search.yahooapis.jp/api/v19/"

# Microsoft Ads 認証情報
MICROSOFT_ADS_CONFIG = {
    "client_id": os.getenv("MICROSOFT_ADS_CLIENT_ID", ""),
    "developer_token": os.getenv("MICROSOFT_ADS_DEVELOPER_TOKEN", ""),
    "refresh_token": os.getenv("MICROSOFT_ADS_REFRESH_TOKEN", ""),
    "account_id": os.getenv("MICROSOFT_ADS_ACCOUNT_ID", ""),
    "customer_id": os.getenv("MICROSOFT_ADS_CUSTOMER_ID", ""),
}

# キャッシュTTL（秒）
CACHE_TTL = 3600
