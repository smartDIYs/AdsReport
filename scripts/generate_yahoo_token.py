"""
Yahoo Ads API のリフレッシュトークンを生成するスクリプト。

事前準備:
1. LY Corporation でアプリケーションを登録（ID連携利用・サーバーサイド）
2. .env に YAHOO_ADS_CLIENT_ID と YAHOO_ADS_CLIENT_SECRET を設定

使い方:
    python scripts/generate_yahoo_token.py
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
AUTH_URL = "https://biz-oauth.yahoo.co.jp/oauth/v1/authorize"
TOKEN_URL = "https://biz-oauth.yahoo.co.jp/oauth/v1/token"

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        print(f"コールバック受信: {self.path}")
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        print(f"パラメータ: {params}")
        auth_code = params.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("認証完了。このウィンドウを閉じてください。".encode("utf-8"))

    def log_message(self, format, *args):
        pass


def main():
    client_id = os.getenv("YAHOO_ADS_CLIENT_ID")
    client_secret = os.getenv("YAHOO_ADS_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("エラー: .env に YAHOO_ADS_CLIENT_ID と YAHOO_ADS_CLIENT_SECRET を設定してください。")
        sys.exit(1)

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": "yahooads",
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
            "client_secret": client_secret,
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
        },
    )
    if resp.status_code != 200:
        print(f"エラー: {resp.status_code}")
        print(f"レスポンス: {resp.text}")
        sys.exit(1)
    tokens = resp.json()

    print("\n=== トークン生成完了 ===")
    print(f"Refresh Token: {tokens['refresh_token']}")
    print("\nこの値を .env の YAHOO_ADS_REFRESH_TOKEN に設定してください。")


if __name__ == "__main__":
    main()
