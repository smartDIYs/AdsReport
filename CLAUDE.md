# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

Google Ads・Yahoo Ads・Microsoft Ads の3プラットフォームから広告パフォーマンスデータをAPI取得し、キャンペーン別・商品カテゴリ別（LC/LM/PL/SCL/SLW）に集計表示するStreamlitダッシュボード。

## コマンド

```bash
# 仮想環境の有効化
source .venv/bin/activate

# ダッシュボード起動
streamlit run app.py --server.port 8501

# トークン生成（初回・期限切れ時）
python scripts/generate_google_token.py
python scripts/generate_yahoo_token.py
python scripts/generate_microsoft_token.py
```

## アーキテクチャ

### データフロー

```
sidebar.py（フィルター選択）
  → aggregator.py（st.cache_data TTL=1h）
    → 各 fetcher が統一スキーマ DataFrame を返す
      → Google: GAQL search_stream（MCC配下全アカウント自動検出）
      → Yahoo: REST 非同期レポート（add→poll→download CSV）、x-z-base-account-id ヘッダ必須
      → Microsoft: SOAP XML（Submit→Poll→ZIP/CSV）、当日データ不可のため end_date を前日に補正
    → pd.concat で統合
    → category_classifier.py でカテゴリ付与
  → KPIカード / キャンペーン別 / カテゴリ別ビュー
```

### 統一データスキーマ（REPORT_COLUMNS）

`platform, campaign_id, campaign_name, campaign_type, ad_group_name, date, impressions, clicks, cost, conversions`

各フェッチャーは `AdsFetcherBase._validate_dataframe()` でこのスキーマに正規化する。Google の cost_micros は `/1_000_000` で円変換。

### カテゴリ分類の優先順位

1. **手動マッピング**（manual_mapping）: campaign_id → category
2. **商品名マッピング**（product_mapping）: ショッピング広告の ad_group_name で完全一致（category.xlsx 由来）
3. **自動パターン**（auto_patterns）: 正規表現でキャンペーン名マッチ。SCL を LC より先に評価して誤マッチ防止
4. 未分類

ショッピング広告の判定: campaign_type に SHOPPING/PERFORMANCE_MAX を含む、または campaign_name に SHOPPING を含む場合。

### プラットフォーム固有の注意点

- **Google**: MCC アカウント（login_customer_id）経由で配下の全クライアントアカウントをループ取得
- **Yahoo**: biz-oauth.yahoo.co.jp で認証。トークン更新時は POST body に client_id/client_secret を含める（Basic認証ではない）。mcc_account_id と account_id が別
- **Microsoft**: consumers エンドポイント使用（個人MSアカウント）。SOAP XML の CustomDateRangeEnd は CustomDateRangeStart より前に記述（アルファベット順必須）

### 新プラットフォーム追加手順

1. `data/fetchers/new.py` に `AdsFetcherBase` 継承クラスを作成
2. `fetch_campaign_report()` で統一スキーマの DataFrame を返す
3. `aggregator.py` の fetchers 辞書に追加
4. `config/settings.py` の PLATFORMS に追加

## 言語

すべての応答・コメントは日本語で行う。
