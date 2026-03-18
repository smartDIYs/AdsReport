from datetime import date

import pandas as pd

from config.settings import GOOGLE_ADS_CONFIG, REPORT_COLUMNS
from data.fetchers.base import AdsFetcherBase


class GoogleAdsFetcher(AdsFetcherBase):
    platform_name = "Google"

    def __init__(self):
        from google.ads.googleads.client import GoogleAdsClient

        self.client = GoogleAdsClient.load_from_dict(GOOGLE_ADS_CONFIG)
        self.login_customer_id = GOOGLE_ADS_CONFIG["login_customer_id"].replace("-", "")

    def _get_client_accounts(self) -> list[str]:
        """MCC配下のクライアントアカウントIDを取得する"""
        service = self.client.get_service("GoogleAdsService")
        query = """
            SELECT
                customer_client.id,
                customer_client.manager
            FROM customer_client
            WHERE customer_client.status = 'ENABLED'
                AND customer_client.manager = false
        """
        client_ids = []
        try:
            stream = service.search_stream(
                customer_id=self.login_customer_id, query=query
            )
            for batch in stream:
                for row in batch.results:
                    client_ids.append(str(row.customer_client.id))
        except Exception:
            # MCC でない場合は自身のIDを返す
            client_ids.append(self.login_customer_id)
        return client_ids

    def _fetch_for_account(
        self, customer_id: str, start_date: date, end_date: date
    ) -> list[dict]:
        """個別アカウントからレポートを取得する"""
        service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.advertising_channel_type,
                ad_group.name,
                segments.date,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions
            FROM ad_group
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND metrics.impressions > 0
            ORDER BY segments.date
        """

        rows = []
        stream = service.search_stream(customer_id=customer_id, query=query)
        for batch in stream:
            for row in batch.results:
                channel_type = row.campaign.advertising_channel_type.name
                rows.append(
                    {
                        "platform": self.platform_name,
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "campaign_type": channel_type,
                        "ad_group_name": row.ad_group.name,
                        "date": row.segments.date,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": row.metrics.cost_micros / 1_000_000,
                        "conversions": row.metrics.conversions,
                    }
                )
        return rows

    def fetch_campaign_report(
        self, start_date: date, end_date: date
    ) -> pd.DataFrame:
        client_ids = self._get_client_accounts()

        all_rows = []
        for cid in client_ids:
            try:
                rows = self._fetch_for_account(cid, start_date, end_date)
                all_rows.extend(rows)
            except Exception:
                continue

        if not all_rows:
            return self._empty_dataframe()

        df = pd.DataFrame(all_rows, columns=REPORT_COLUMNS)
        return self._validate_dataframe(df)
