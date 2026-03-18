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
        resp.raise_for_status()
        return resp.json()["access_token"]

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
                start = text.find("<ReportDownloadUrl>") + len("<ReportDownloadUrl>")
                end = text.find("</ReportDownloadUrl>")
                if start > 0 and end > start:
                    return text[start:end]
                return None
            elif "<Status>Error</Status>" in text:
                return None
            time.sleep(5)
            elapsed += 5
        return None

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
        start_tag = "<ReportRequestId>"
        end_tag = "</ReportRequestId>"
        start_idx = resp_text.find(start_tag)
        if start_idx == -1:
            return self._empty_dataframe()
        start_idx += len(start_tag)
        end_idx = resp_text.find(end_tag, start_idx)
        report_request_id = resp_text[start_idx:end_idx]

        # Poll and download
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
