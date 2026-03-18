# 広告レポートダッシュボード

Google Ads・Yahoo Ads・Microsoft Ads の3プラットフォームから広告パフォーマンスデータをAPI取得し、キャンペーン別・商品カテゴリ別に集計表示するStreamlitダッシュボードです。

## 機能

- **3プラットフォーム統合**: Google Ads / Yahoo Ads / Microsoft Ads のデータを一画面で確認
- **KPIサマリー**: 表示回数・クリック数・CTR・CPC・費用・CV数・CV率・CPA を一覧表示
- **キャンペーン別ビュー**: キャンペーンごとの集計テーブル・棒グラフ
- **カテゴリ別ビュー**: 商品カテゴリ（LC/LM/PL/SCL/SLW）ごとの集計テーブル・円グラフ・棒グラフ
- **カテゴリ自動分類**: キャンペーン名・広告グループ名からの自動判定 + 商品名マッピング（category.xlsx）
- **期間プリセット**: 今月 / 先月 / 先々月 / 直近7日 / 直近30日 / カスタム
- **フィルター**: プラットフォーム・カテゴリの絞り込み
- **CSVエクスポート**: utf-8-sig エンコードで文字化けなし

## セットアップ

### 1. 環境構築

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 認証情報の設定

`.env.example` を `.env` にコピーし、各プラットフォームの認証情報を記入します。

```bash
cp .env.example .env
```

#### Google Ads

| 項目 | 取得元 |
|---|---|
| DEVELOPER_TOKEN | Google Ads 管理画面 → ツールと設定 → APIセンター |
| CLIENT_ID / CLIENT_SECRET | Google Cloud Console → OAuth2クライアント（デスクトップアプリ） |
| LOGIN_CUSTOMER_ID | MCC アカウントID（ハイフンなし） |
| REFRESH_TOKEN | `python scripts/generate_google_token.py` で生成 |

#### Yahoo Ads

| 項目 | 取得元 |
|---|---|
| CLIENT_ID / CLIENT_SECRET | Yahoo!広告 API 管理画面でアプリ登録 |
| ACCOUNT_ID | Yahoo!広告の広告アカウントID |
| MCC_ACCOUNT_ID | Yahoo!広告のMCCアカウントID |
| REFRESH_TOKEN | `python scripts/generate_yahoo_token.py` で生成 |

#### Microsoft Ads

| 項目 | 取得元 |
|---|---|
| CLIENT_ID | Azure AD → アプリの登録（パブリッククライアント） |
| DEVELOPER_TOKEN | Microsoft Advertising → ツール → 開発者トークン |
| ACCOUNT_ID / CUSTOMER_ID | Microsoft Advertising 管理画面 |
| REFRESH_TOKEN | `python scripts/generate_microsoft_token.py` で生成 |

### 3. トークン生成

各プラットフォームのリフレッシュトークンを生成します。

```bash
python scripts/generate_google_token.py
python scripts/generate_yahoo_token.py
python scripts/generate_microsoft_token.py
```

### 4. ダッシュボード起動

```bash
streamlit run app.py --server.port 8501
```

ブラウザで http://localhost:8501 を開きます。

## アーキテクチャ

```
sidebar.py（フィルター選択）
  → aggregator.py（st.cache_data TTL=1h）
    → 各 fetcher が統一スキーマ DataFrame を返す
      → Google: GAQL search_stream（MCC配下全アカウント自動検出）
      → Yahoo: REST 非同期レポート（add→poll→download CSV）
      → Microsoft: SOAP XML（Submit→Poll→ZIP/CSV）
    → pd.concat で統合
    → category_classifier.py でカテゴリ付与
  → KPIカード / キャンペーン別 / カテゴリ別ビュー
```

### カテゴリ分類の優先順位

1. **手動マッピング**: campaign_id → category（category_mapping.yaml）
2. **商品名マッピング**: ショッピング広告の広告グループ名で完全一致（category.xlsx 由来）
3. **自動パターン**: 正規表現でキャンペーン名マッチ
4. 未分類

## 技術スタック

- Python / Streamlit（ダッシュボードUI）
- pandas（データ集計）
- Plotly Express（チャート）
- google-ads（Google Ads API）
- requests（Yahoo Ads REST API / Microsoft Ads SOAP API）
