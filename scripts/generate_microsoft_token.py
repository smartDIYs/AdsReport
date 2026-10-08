"""
Microsoft Ads API のリフレッシュトークンを生成するスクリプト。

ローカルサーバー（http://localhost:8080/callback）で認可コードを受け取り、
取得したリフレッシュトークンで .env を更新し、クリップボードにもコピーする。

事前準備:
1. .env に MICROSOFT_ADS_CLIENT_ID を設定
2. Azure アプリの「モバイルとデスクトップ」リダイレクトURIに http://localhost:8080/callback を登録

使い方:
    python scripts/generate_microsoft_token.py
"""

import os
import re
import subprocess
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

REDIRECT_URI = "http://localhost:8080/callback"
AUTH_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize"
TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
SCOPE = "https://ads.microsoft.com/msads.manage offline_access"


auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        auth_code = params.get("code", [None])[0]
        error = params.get("error_description", params.get("error", [""]))[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        message = "認証完了。このウィンドウを閉じてください。" if auth_code else f"認証失敗: {error}"
        self.wfile.write(message.encode("utf-8"))

    def log_message(self, format, *args):
        pass


def _update_env(refresh_token):
    """.env の MICROSOFT_ADS_REFRESH_TOKEN を書き換える"""
    if not ENV_PATH.exists():
        return False
    content = ENV_PATH.read_text()
    line = f"MICROSOFT_ADS_REFRESH_TOKEN={refresh_token}"
    if re.search(r"^MICROSOFT_ADS_REFRESH_TOKEN=.*$", content, flags=re.M):
        content = re.sub(r"^MICROSOFT_ADS_REFRESH_TOKEN=.*$", lambda _: line, content, flags=re.M)
    else:
        content = content.rstrip("\n") + f"\n{line}\n"
    ENV_PATH.write_text(content)
    return True


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
        "prompt": "select_account",
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    print(f"ブラウザで認証してください: {url}", flush=True)
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
    try:
        subprocess.run(["pbcopy"], input=tokens["refresh_token"].encode(), check=True)
        print("リフレッシュトークンをクリップボードにコピーしました。")
    except (OSError, subprocess.CalledProcessError):
        print(f"Refresh Token: {tokens['refresh_token']}")
    if _update_env(tokens["refresh_token"]):
        print("\n.env の MICROSOFT_ADS_REFRESH_TOKEN を更新しました。")
    else:
        print("\nこの値を .env の MICROSOFT_ADS_REFRESH_TOKEN に設定してください。")
    print("Streamlit Cloud の Secrets も同じ値に更新し、アプリを Reboot してください。")


if __name__ == "__main__":
    main()
