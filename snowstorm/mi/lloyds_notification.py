import requests

from snowstorm import leader_election
from snowstorm.mi.lloyds_stats import MI_LloydsStats
from snowstorm.settings import settings

token = settings.webserver_auth_token


class Notification_Lloyds:
    def __init__(self) -> None:
        self.webhook_url = "https://hellobink.webhook.office.com/webhookb2/66f08760-f657-42af-bf88-4f7e4c009af1@a6e2367a-92ea-4e5a-b565-723830bcc095/IncomingWebhook/93166ec813db41939a825e5537ae8e82/48aca6b1-4d56-4a15-bc92-8aa9d97300df"  # noqa

    def send(self) -> None:
        if not leader_election(job_name="mi_lloyds_notification"):
            return None
        stats = MI_LloydsStats()
        data = stats.run()
        msg = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.0",
                        "body": [
                            {
                                "type": "Container",
                                "id": "050f47d7-85af-a2eb-8940-a807faf71d90",
                                "padding": "None",
                                "items": [
                                    {
                                        "type": "ColumnSet",
                                        "id": "b2094222-2141-c4a4-7d1a-29213436c08a",
                                        "columns": [
                                            {
                                                "type": "Column",
                                                "id": "983af5a8-c74f-024e-9aeb-b230a6f0dd54",
                                                "padding": "None",
                                                "width": "stretch",
                                                "items": [
                                                    {
                                                        "type": "TextBlock",
                                                        "id": "2c65c81f-7b95-00d9-b76a-fb34ed27706c",
                                                        "text": "User Stats (Active)",
                                                        "wrap": True,
                                                        "size": "Medium",
                                                        "weight": "Bolder",
                                                    },
                                                    {
                                                        "type": "FactSet",
                                                        "id": "f698545d-a980-7bc9-0ca9-95bc943f9128",
                                                        "facts": [
                                                            {
                                                                "title": "Users",
                                                                "value": data["users"]["total"],
                                                            },
                                                            {
                                                                "title": "Payment Cards",
                                                                "value": data["payment_accounts"]["success"]["total"],
                                                            },
                                                            {
                                                                "title": "Loyalty Cards",
                                                                "value": data["loyalty_accounts"]["success"]["total"],
                                                            },
                                                        ],
                                                    },
                                                ],
                                            },
                                            {
                                                "type": "Column",
                                                "id": "3df978c2-0821-7584-6bc9-6a87b74e27a5",
                                                "padding": "None",
                                                "width": "stretch",
                                                "items": [
                                                    {
                                                        "type": "TextBlock",
                                                        "id": "0215e59d-5ee2-a8bb-c4e1-80102e45a4c1",
                                                        "text": "API Stats (Past 24h)",
                                                        "wrap": True,
                                                        "size": "Medium",
                                                        "weight": "Bolder",
                                                    },
                                                    {
                                                        "type": "FactSet",
                                                        "id": "069a2591-b888-1e52-c4be-5ff756e8c1ee",
                                                        "facts": [
                                                            {
                                                                "title": "API Calls",
                                                                "value": data["api_stats"]["calls"],
                                                            },
                                                            {
                                                                "title": "P50",
                                                                "value": data["api_stats"]["percentiles"]["p50"],
                                                            },
                                                            {
                                                                "title": "P95",
                                                                "value": data["api_stats"]["percentiles"]["p95"],
                                                            },
                                                            {
                                                                "title": "P99",
                                                                "value": data["api_stats"]["percentiles"]["p99"],
                                                            },
                                                        ],
                                                    },
                                                ],
                                            },
                                        ],
                                        "padding": "None",
                                    }
                                ],
                            },
                            {
                                "type": "Container",
                                "id": "5ef0b945-268a-6310-ffb0-6f020979ed88",
                                "padding": "None",
                                "items": [
                                    {
                                        "type": "ActionSet",
                                        "id": "a48b3544-02ec-0715-707d-1759aeb04270",
                                        "actions": [
                                            {
                                                "type": "Action.OpenUrl",
                                                "id": "b528d37b-a513-c7cf-014a-bc8004efb4f5",
                                                "title": "Open Dashboard",
                                                "url": f"https://stats.gb.bink.com/lbg?auth={token}",
                                            }
                                        ],
                                    }
                                ],
                            },
                        ],
                        "padding": "None",
                    },
                }
            ],
        }

        requests.post(self.webhook_url, json=msg)
