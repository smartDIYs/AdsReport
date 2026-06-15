import io
import time
from datetime import date

import pandas as pd
import requests

from config.settings import MICROSOFT_ADS_CONFIG, REPORT_COLUMNS
from data.fetchers.base import AdsFetcherBase

TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
REPORTING_URL = "https://reporting.api.bingads.microsoft.com/Reporting/v13/GenerateReport"
SCOPE = "https://ads.microsoft.com/msads.manage offline_access"


class MicrosoftAdsFetcher(AdsFetcherBase):
    platform_name = "Microsoft"

    def __init__(self):
        self.config = MICROSOFT_ADS_CONFIG
        self.access_token = self._get_access_token()

    def _get_access_token(self) -> str:
        resp = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": self.config["client_id"],
                "refresh_token": self.config["refresh_token"],
                "scope": SCOPE,
            },
        )
        if resp.status_code != 200:
            error = ""
            try:
                error = resp.json().get("error", "")
            except Exception:
                pass
            if error == "invalid_grant":
                raise RuntimeError(
                    "Microsoft のリフレッシュトークンが失効しています。再認証が必要です。"
                    "ローカルで `python scripts/generate_microsoft_token.py` を実行してトークンを再生成し、"
                    "Streamlit Secrets（および .env）の MICROSOFT_ADS_REFRESH_TOKEN を更新してください。"
                )
            raise RuntimeError(
                f"Microsoft のアクセストークン取得に失敗しました: {resp.status_code} {resp.text[:200]}"
            )
        return resp.json()["access_token"]

    @staticmethod
    def _extract(text: str, start_tag: str, end_tag: str):
        """XML から start_tag と end_tag に挟まれた値を取り出す"""
        start = text.find(start_tag)
        if start == -1:
            return None
        start += len(start_tag)
        end = text.find(end_tag, start)
        if end == -1:
            return None
        return text[start:end]

    @classmethod
    def _extract_fault(cls, text: str) -> str:
        """SOAP レスポンスからエラー理由を抽出する"""
        for tag in ("faultstring", "Message", "ErrorCode"):
            val = cls._extract(text, f"<{tag}>", f"</{tag}>")
            if val:
                return val
        return text[:200]

    def _soap_request(self, body: str) -> str:
        """SOAP リクエストを送信する"""
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "SubmitGenerateReport",
            "AuthenticationToken": self.access_token,
            "CustomerAccountId": str(self.config["account_id"]),
            "CustomerId": str(self.config["customer_id"]),
            "DeveloperToken": self.config["developer_token"],
        }
        resp = requests.post(
            "https://reporting.api.bingads.microsoft.com/Api/Advertiser/Reporting/v13/ReportingService.svc",
            data=body.encode("utf-8"),
            headers=headers,
        )
        return resp.text

    def _poll_report(self, report_request_id: str) :
        """レポートのステータスをポーリングし、完了したらダウンロードURLを返す"""
        poll_body = f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
  <s:Header>
    <h:AuthenticationToken xmlns:h="https://bingads.microsoft.com/Reporting/v13">{self.access_token}</h:AuthenticationToken>
    <h:CustomerAccountId xmlns:h="https://bingads.microsoft.com/Reporting/v13">{self.config["account_id"]}</h:CustomerAccountId>
    <h:CustomerId xmlns:h="https://bingads.microsoft.com/Reporting/v13">{self.config["customer_id"]}</h:CustomerId>
    <h:DeveloperToken xmlns:h="https://bingads.microsoft.com/Reporting/v13">{self.config["developer_token"]}</h:DeveloperToken>
  </s:Header>
  <s:Body>
    <PollGenerateReportRequest xmlns="https://bingads.microsoft.com/Reporting/v13">
      <ReportRequestId>{report_request_id}</ReportRequestId>
    </PollGenerateReportRequest>
  </s:Body>
</s:Envelope>"""

        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "PollGenerateReport",
        }
        max_wait = 120
        elapsed = 0
        while elapsed < max_wait:
            resp = requests.post(
                "https://reporting.api.bingads.microsoft.com/Api/Advertiser/Reporting/v13/ReportingService.svc",
                data=poll_body.encode("utf-8"),
                headers=headers,
            )
            text = resp.text
            if "<Status>Success</Status>" in text:
                # レポート生成成功。URL が無い場合は対象期間にデータが無い（正常）
                return self._extract(text, "<ReportDownloadUrl>", "</ReportDownloadUrl>")
            elif "<Status>Error</Status>" in text:
                raise RuntimeError(
                    f"Microsoft のレポート生成がエラーになりました: {self._extract_fault(text)}"
                )
            time.sleep(5)
            elapsed += 5
        raise RuntimeError("Microsoft のレポート生成がタイムアウトしました（120秒）")

    def fetch_campaign_report(
        self, start_date: date, end_date: date
    ) -> pd.DataFrame:
        from datetime import timedelta

        # Microsoft Ads は当日データが未確定のためエラーになる場合がある
        if end_date >= date.today():
            end_date = date.today() - timedelta(days=1)
        if start_date > end_date:
            return self._empty_dataframe()

        submit_body = f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
  <s:Header>
    <h:AuthenticationToken xmlns:h="https://bingads.microsoft.com/Reporting/v13">{self.access_token}</h:AuthenticationToken>
    <h:CustomerAccountId xmlns:h="https://bingads.microsoft.com/Reporting/v13">{self.config["account_id"]}</h:CustomerAccountId>
    <h:CustomerId xmlns:h="https://bingads.microsoft.com/Reporting/v13">{self.config["customer_id"]}</h:CustomerId>
    <h:DeveloperToken xmlns:h="https://bingads.microsoft.com/Reporting/v13">{self.config["developer_token"]}</h:DeveloperToken>
  </s:Header>
  <s:Body>
    <SubmitGenerateReportRequest xmlns="https://bingads.microsoft.com/Reporting/v13">
      <ReportRequest xmlns:i="http://www.w3.org/2001/XMLSchema-instance" i:type="AdGroupPerformanceReportRequest">
        <ExcludeColumnHeaders>false</ExcludeColumnHeaders>
        <ExcludeReportFooter>true</ExcludeReportFooter>
        <ExcludeReportHeader>true</ExcludeReportHeader>
        <Format>Csv</Format>
        <FormatVersion>2.0</FormatVersion>
        <ReportName>AdsReport</ReportName>
        <ReturnOnlyCompleteData>false</ReturnOnlyCompleteData>
        <Aggregation>Daily</Aggregation>
        <Columns>
          <AdGroupPerformanceReportColumn>TimePeriod</AdGroupPerformanceReportColumn>
          <AdGroupPerformanceReportColumn>CampaignId</AdGroupPerformanceReportColumn>
          <AdGroupPerformanceReportColumn>CampaignName</AdGroupPerformanceReportColumn>
          <AdGroupPerformanceReportColumn>AdGroupName</AdGroupPerformanceReportColumn>
          <AdGroupPerformanceReportColumn>Impressions</AdGroupPerformanceReportColumn>
          <AdGroupPerformanceReportColumn>Clicks</AdGroupPerformanceReportColumn>
          <AdGroupPerformanceReportColumn>Spend</AdGroupPerformanceReportColumn>
          <AdGroupPerformanceReportColumn>Conversions</AdGroupPerformanceReportColumn>
        </Columns>
        <Scope>
          <AccountIds xmlns:a="http://schemas.microsoft.com/2003/10/Serialization/Arrays">
            <a:long>{self.config["account_id"]}</a:long>
          </AccountIds>
        </Scope>
        <Time>
          <CustomDateRangeEnd>
            <Day>{end_date.day}</Day>
            <Month>{end_date.month}</Month>
            <Year>{end_date.year}</Year>
          </CustomDateRangeEnd>
          <CustomDateRangeStart>
            <Day>{start_date.day}</Day>
            <Month>{start_date.month}</Month>
            <Year>{start_date.year}</Year>
          </CustomDateRangeStart>
        </Time>
      </ReportRequest>
    </SubmitGenerateReportRequest>
  </s:Body>
</s:Envelope>"""

        # Submit report
        resp_text = self._soap_request(submit_body)

        # Extract ReportRequestId
        report_request_id = self._extract(
            resp_text, "<ReportRequestId>", "</ReportRequestId>"
        )
        if not report_request_id:
            raise RuntimeError(
                f"Microsoft のレポート作成リクエストに失敗しました: {self._extract_fault(resp_text)}"
            )

        # Poll and download（URL が無い場合は対象期間にデータが無い＝正常）
        download_url = self._poll_report(report_request_id)
        if not download_url:
            return self._empty_dataframe()

        # Download CSV
        download_url = download_url.replace("&amp;", "&")
        resp = requests.get(download_url)
        resp.raise_for_status()

        # Handle zip file
        import zipfile
        z = zipfile.ZipFile(io.BytesIO(resp.content))
        csv_name = z.namelist()[0]
        csv_data = z.read(csv_name).decode("utf-8-sig")

        df = pd.read_csv(io.StringIO(csv_data))

        column_map = {
            "TimePeriod": "date",
            "CampaignId": "campaign_id",
            "CampaignName": "campaign_name",
            "CampaignType": "campaign_type",
            "AdGroupName": "ad_group_name",
            "Impressions": "impressions",
            "Clicks": "clicks",
            "Spend": "cost",
            "Conversions": "conversions",
        }

        available = [c for c in column_map if c in df.columns]
        df = df[available].rename(columns=column_map)
        df["platform"] = self.platform_name
        df["campaign_id"] = df["campaign_id"].astype(str)

        return self._validate_dataframe(df)
