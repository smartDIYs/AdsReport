import re
from pathlib import Path

import pandas as pd
import yaml

from config.settings import CATEGORY_MAPPING_FILE, UNCATEGORIZED


def load_mapping_config(path: Path = CATEGORY_MAPPING_FILE) -> dict:
    """カテゴリマッピング設定を読み込む"""
    if not path.exists():
        return {"auto_patterns": {}, "manual_mapping": {}}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"auto_patterns": {}, "manual_mapping": {}}


def save_mapping_config(config: dict, path: Path = CATEGORY_MAPPING_FILE) -> None:
    """カテゴリマッピング設定を保存する"""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


def classify_category(
    campaign_id: str,
    campaign_name: str,
    campaign_type: str,
    ad_group_name: str,
    config: dict,
) -> str:
    """
    カテゴリを判定する。
    優先順位: 手動マッピング → 自動パターン → 未分類
    ショッピング広告はad_group_nameで判定、通常はcampaign_nameで判定。
    """
    manual = config.get("manual_mapping") or {}
    if str(campaign_id) in manual:
        return manual[str(campaign_id)]

    auto_patterns = config.get("auto_patterns") or {}
    product_mapping = config.get("product_mapping") or {}
    campaign_type_str = str(campaign_type or "").upper()
    campaign_name_str = str(campaign_name or "").upper()
    is_shopping = (
        "SHOPPING" in campaign_type_str
        or "PERFORMANCE_MAX" in campaign_type_str
        or "SHOPPING" in campaign_name_str
    )

    # ショッピング広告: 商品名マッピング → 自動パターン
    if is_shopping and ad_group_name:
        ag = str(ad_group_name).strip()
        if ag in product_mapping:
            return product_mapping[ag]

    target_text = ad_group_name if is_shopping and ad_group_name else campaign_name
    target_text = str(target_text or "")

    # パターンマッチ（SCL→LC→LM→PL→SLWの順で定義されている想定）
    for category, pattern in auto_patterns.items():
        if re.search(pattern, target_text):
            return category

    return UNCATEGORIZED


def apply_categories(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrameにカテゴリ列を追加する"""
    if df.empty:
        df["category"] = pd.Series(dtype=str)
        return df

    config = load_mapping_config()
    df["category"] = df.apply(
        lambda row: classify_category(
            row.get("campaign_id", ""),
            row.get("campaign_name", ""),
            row.get("campaign_type", ""),
            row.get("ad_group_name", ""),
            config,
        ),
        axis=1,
    )
    return df
