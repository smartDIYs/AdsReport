import io
import time
from datetime import date

import pandas as pd
import requests

from config.settings import (
    REPORT_COLUMNS,
    YAHOO_ADS_API_BASE,
    YAHOO_ADS_CONFIG,
    YAHOO_ADS_TOKEN_URL,
)
from data.fetchers.base import AdsFetcherBase


class YahooAdsFetcher(AdsFetcherBase):
    platform_name = "Yahoo"

    def __init__(self):
        self.config = YAHOO_ADS_CONFIG
        self.account_id = self.config["account_id"]
        self.base_account_id = self.config.get("mcc_account_id") or self.account_id
        self.access_token = self._get_access_token()

    def _get_access_token(self) -> str:
        resp = requests.post(
            YAHOO_ADS_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": self.config["client_id"],
                "client_secret": self.config["client_secret"],
                "refresh_token": self.config["refresh_token"],
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _api_request(self, service: str, operation: str, payload: dict) -> dict:
        url = f"{YAHOO_ADS_API_BASE}{service}/{operation}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "x-z-base-account-id": str(self.base_account_id),
        }
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def _download_report(self, report_job_id: str) -> str:
        url = f"{YAHOO_ADS_API_BASE}ReportDefinitionService/download"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "x-z-base-account-id": str(self.base_account_id),
        }
        payload = {
            "accountId": int(self.account_id),
            "reportJobId": int(report_job_id),
        }
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.text

    def fetch_campaign_report(
        self, start_date: date, end_date: date
    ) -> pd.DataFrame:
        # Step 1: レポートジョブ登録
        add_payload = {
            "accountId": int(self.account_id),
            "operand": [
                {
                    "accountId": int(self.account_id),
                    "reportType": "ADGROUP",
                    "reportName": "AdsReport",
                    "reportDateRangeType": "CUSTOM_DATE",
                    "dateRange": {
                        "startDate": start_date.strftime("%Y%m%d"),
                        "endDate": end_date.strftime("%Y%m%d"),
                    },
                    "reportType": "ADGROUP",
                    "fields": [
                        "CAMPAIGN_ID",
                        "CAMPAIGN_NAME",
                        "ADGROUP_NAME",
                        "DAY",
                        "IMPS",
                        "CLICKS",
                        "COST",
                        "CONVERSIONS",
                    ],
                    "reportDownloadFormat": "CSV",
                    "reportDownloadEncode": "UTF8",
                }
            ],
        }
        result = self._api_request("ReportDefinitionService", "add", add_payload)
        values = result.get("rval", {}).get("values", [])
        if not values or not values[0].get("operationSucceeded"):
            return self._empty_dataframe()

        report_job_id = str(
            values[0]["reportDefinition"]["reportJobId"]
        )

        # Step 2: ステータスポーリング
        get_payload = {
            "accountId": int(self.account_id),
            "reportJobIds": [int(report_job_id)],
        }
        max_wait = 120
        elapsed = 0
        while elapsed < max_wait:
            result = self._api_request("ReportDefinitionService", "get", get_payload)
            values = result.get("rval", {}).get("values", [])
            if values:
                status = values[0].get("reportDefinition", {}).get("reportJobStatus")
                if status == "COMPLETED":
                    break
                if status == "FAILED":
                    return self._empty_dataframe()
            time.sleep(5)
            elapsed += 5

        if elapsed >= max_wait:
            return self._empty_dataframe()

        # Step 3: ダウンロード
        csv_text = self._download_report(report_job_id)
        df = pd.read_csv(io.StringIO(csv_text))

        column_map = {
            "キャンペーンID": "campaign_id",
            "キャンペーン名": "campaign_name",
            "広告グループ名": "ad_group_name",
            "日": "date",
            "インプレッション数": "impressions",
            "クリック数": "clicks",
            "コスト": "cost",
            "コンバージョン数": "conversions",
        }
        df = df.rename(columns=column_map)
        # 合計行（campaign_nameがNaN）を除外
        df = df.dropna(subset=["campaign_name"])
        df["platform"] = self.platform_name
        df["campaign_type"] = ""
        df["campaign_id"] = df["campaign_id"].astype(str)

        return self._validate_dataframe(df)
