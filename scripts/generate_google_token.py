"""
Google Ads API のリフレッシュトークンを生成するスクリプト。

事前準備:
1. Google Cloud Console で OAuth2 クライアント（デスクトップアプリ）を作成
2. Google Ads API の Developer Token を取得
3. .env に GOOGLE_ADS_CLIENT_ID と GOOGLE_ADS_CLIENT_SECRET を設定

使い方:
    python scripts/generate_google_token.py
"""

import os
import sys

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/adwords"]


def main():
    client_id = os.getenv("GOOGLE_ADS_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_ADS_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("エラー: .env に GOOGLE_ADS_CLIENT_ID と GOOGLE_ADS_CLIENT_SECRET を設定してください。")
        sys.exit(1)

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    credentials = flow.run_local_server(port=8080)

    print("\n=== トークン生成完了 ===")
    print(f"Refresh Token: {credentials.refresh_token}")
    print("\nこの値を .env の GOOGLE_ADS_REFRESH_TOKEN に設定してください。")


if __name__ == "__main__":
    main()
