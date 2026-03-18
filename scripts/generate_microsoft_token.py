"""
Microsoft Ads API のリフレッシュトークンを生成するスクリプト。

事前準備:
1. Azure AD でアプリケーションを登録
2. .env に MICROSOFT_ADS_CLIENT_ID を設定

使い方:
    python scripts/generate_microsoft_token.py
"""

import os
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from dotenv import load_dotenv

load_dotenv()

REDIRECT_URI = "http://localhost:8080/callback"
AUTH_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize"
TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
SCOPE = "https://ads.microsoft.com/msads.manage offline_access"

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        print(f"コールバック受信: {self.path}")
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        auth_code = params.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("認証完了。このウィンドウを閉じてください。".encode("utf-8"))

    def log_message(self, format, *args):
        pass


def main():
    client_id = os.getenv("MICROSOFT_ADS_CLIENT_ID")

    if not client_id:
        print("エラー: .env に MICROSOFT_ADS_CLIENT_ID を設定してください。")
        sys.exit(1)

    params = {
        "client_id": client_id,
        "scope": SCOPE,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    print(f"ブラウザで認証してください: {url}")
    webbrowser.open(url)

    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.handle_request()

    if not auth_code:
        print("エラー: 認証コードを取得できませんでした。")
        sys.exit(1)

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPE,
        },
    )

    if resp.status_code != 200:
        print(f"エラー: {resp.status_code}")
        print(f"レスポンス: {resp.text}")
        sys.exit(1)

    tokens = resp.json()

    print("\n=== トークン生成完了 ===")
    print(f"Refresh Token: {tokens['refresh_token']}")
    print("\nこの値を .env の MICROSOFT_ADS_REFRESH_TOKEN に設定してください。")


if __name__ == "__main__":
    main()
