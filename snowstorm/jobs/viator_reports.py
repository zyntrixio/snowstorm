from typing import Union

import pendulum
import requests
from azure.storage.blob import BlobClient, BlobSasPermissions, ContainerClient, generate_blob_sas
from loguru import logger

from snowstorm import leader_election
from snowstorm.settings import settings


class Job_ViatorReports:
    def __init__(self) -> None:
        self.mail_to = ["nlewis@tripadvisor.com", "mchattertonwhite@tripadvisor.com", "ejordan@tripadvisor.com"]
        self.mail_bcc = ["kkrastev@bink.com", "sgraham@bink.com"]
        self.teams_webhook = "https://hellobink.webhook.office.com/webhookb2/bf220ac8-d509-474f-a568-148982784d19@a6e2367a-92ea-4e5a-b565-723830bcc095/IncomingWebhook/4fa9be428a2347f2a6f02d2758359d85/48aca6b1-4d56-4a15-bc92-8aa9d97300df"  # noqa
        self.storage_account_name = settings.storage_account_name
        self.storage_account_auth = settings.storage_account_auth
        self.storage_account_container = settings.storage_account_container

    def list_blobs(self) -> list:
        try:
            container = ContainerClient(
                account_url=f"https://{self.storage_account_name}.blob.core.windows.net/",
                credential=self.storage_account_auth,
                container_name=self.storage_account_container,
            )
            return [blob for blob in container.list_blob_names()]
        except Exception as e:
            logger.exception(e)

    def process_blob(self, blob_name: str) -> Union[str, None]:
        try:
            blob = BlobClient(
                account_url=f"https://{self.storage_account_name}.blob.core.windows.net/",
                credential=self.storage_account_auth,
                container_name=self.storage_account_container,
                blob_name=blob_name,
            )
            if "snowstorm_processed" in blob.get_blob_tags():
                logger.info(f"Blob: {blob_name}, Already Processed")
                return None
            else:
                logger.info(f"Blob: {blob_name}, Requires Processing")
                token = generate_blob_sas(
                    account_name=self.storage_account_name,
                    account_key=self.storage_account_auth,
                    container_name=self.storage_account_container,
                    blob_name=blob_name,
                    permission=BlobSasPermissions(read=True),
                    start=pendulum.today(),
                    expiry=pendulum.today().add(days=7),
                )
                blob.set_blob_tags({"snowstorm_processed": True})
                url = (
                    f"https://{self.storage_account_name}.blob.core.windows.net/"
                    f"{self.storage_account_container}/{blob_name}?{token}"
                )
                return url
        except Exception as e:
            logger.exception(e)

    def send_email(self, url: str) -> None:
        logger.info(f"Sending Email to: {self.mail_to}")
        try:
            r = requests.post(
                "https://api.eu.mailgun.net/v3/bink.com/messages",
                auth=("api", settings.mailgun_key),
                data={
                    "from": "noreply@bink.com",
                    "to": ",".join(self.mail_to),
                    "bcc": ",".join(self.mail_bcc),
                    "subject": "Viator Discounts weekly transactions",
                    "text": f"Hi Viator team, Please see the latest Viator transactional data file: {url}",
                },
            )
            r.raise_for_status()
        except Exception as e:
            logger.exception(e)

    def send_teams_notification(self, url: str) -> None:
        logger.info("Sending Microsoft Teams Notification")
        try:
            r = requests.post(
                self.teams_webhook,
                json={
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "5BE0CA",
                    "summary": "Viator Report Email Sent",
                    "Sections": [
                        {
                            "activityTitle": "Viator Report Email Sent",
                            "facts": [
                                {"name": "To", "value": ", ".join(self.mail_to)},
                                {"name": "BCC", "value": ", ".join(self.mail_bcc)},
                                {"name": "URL", "value": url},
                            ],
                            "markdown": True,
                        }
                    ],
                },
            )
            r.raise_for_status()
        except Exception as e:
            logger.exception(e)

    def run(self) -> None:
        if not leader_election(job_name="viator_reports"):
            return None
        blobs = self.list_blobs()
        logger.info(f"Blobs to process: {blobs}")
        for blob in blobs:
            logger.info(f"Processing Blob: {blob}")
            url = self.process_blob(blob_name=blob)
            if url is not None:
                self.send_email(url=url)
                self.send_teams_notification(url=url)
