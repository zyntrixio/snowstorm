import itertools
import json

import pendulum
import psycopg2
from azure.core.exceptions import ServiceResponseError
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient, LogsQueryResult, LogsQueryStatus
from loguru import logger
from redis import StrictRedis

from snowstorm.settings import settings


class MI_LloydsStats:
    def __init__(self):
        self.database_dsn = str(settings.database_dsn)
        self.hermes_dsn = self.database_dsn.replace("snowstorm", "hermes")
        self.harmonia_dsn = self.database_dsn.replace("snowstorm", "harmonia")
        self.redis_key = "snowstorm_mi_lloyds_stats"
        self.workspace_id = settings.workspace_id

    def users(self) -> dict:
        hermes_db = psycopg2.connect(self.hermes_dsn)
        query = """
        SELECT bundle_id, count(1) FROM "user" WHERE is_active IS true
        AND bundle_id IN ('com.bos.api2', 'com.halifax.api2', 'com.lloyds.api2')
        GROUP BY bundle_id;
        """
        with hermes_db.cursor() as cur:
            cur.execute(query)
            results = {k: v for k, v in cur.fetchall() if k is not None}

        results["total"] = sum([v for v in results.values()])
        return results

    def loyalty_accounts(self) -> dict:
        """
        Returns count of loyalty accounts for success, pending, and failed statuses by each loyalty scheme
        """
        hermes_db = psycopg2.connect(self.hermes_dsn)

        plan_ids = {
            "iceland": 105,
            "squaremeal": 216,
            "viator": 285,
            "the_works": 351,
            "itsu": 352,
            "slim_chickens": 386,
            "stonegate": 393,
        }

        success_results = {}
        success_query = """
        SELECT "user".bundle_id as channel, count(ubiquity_schemeaccountentry.id)
        AS pending_sqauremeal_lcards FROM ubiquity_schemeaccountentry
        INNER JOIN "user" ON ubiquity_schemeaccountentry.user_id = "user".id
        INNER JOIN scheme_schemeaccount ON ubiquity_schemeaccountentry.scheme_account_id = scheme_schemeaccount.id
        WHERE ubiquity_schemeaccountentry.link_status = 1
        AND scheme_schemeaccount.is_deleted = False
        AND scheme_schemeaccount.scheme_id = %s
        AND "user".bundle_id IN ('com.bos.api2', 'com.halifax.api2', 'com.lloyds.api2')
        GROUP BY channel;
        """

        pending_results = {}
        pending_query = """
        SELECT "user".bundle_id as channel, count(ubiquity_schemeaccountentry.id)
        AS pending_sqauremeal_lcards FROM ubiquity_schemeaccountentry
        INNER JOIN "user" ON ubiquity_schemeaccountentry.user_id = "user".id
        INNER JOIN scheme_schemeaccount ON ubiquity_schemeaccountentry.scheme_account_id = scheme_schemeaccount.id
        WHERE ubiquity_schemeaccountentry.link_status IN (0, 442, 443, 1001, 2001)
        AND scheme_schemeaccount.is_deleted = False
        AND scheme_schemeaccount.scheme_id = %s
        AND "user".bundle_id IN ('com.bos.api2', 'com.halifax.api2', 'com.lloyds.api2')
        GROUP BY channel;
        """

        failed_results = {}
        failed_query = """
        SELECT "user".bundle_id as channel, count(ubiquity_schemeaccountentry.id)
        AS pending_sqauremeal_lcards FROM ubiquity_schemeaccountentry
        INNER JOIN "user" ON ubiquity_schemeaccountentry.user_id = "user".id
        INNER JOIN scheme_schemeaccount ON ubiquity_schemeaccountentry.scheme_account_id = scheme_schemeaccount.id
        WHERE ubiquity_schemeaccountentry.link_status NOT IN (1, 0, 442, 443, 1001, 2001)
        AND scheme_schemeaccount.is_deleted = False
        AND scheme_schemeaccount.scheme_id = %s
        AND "user".bundle_id IN ('com.bos.api2', 'com.halifax.api2', 'com.lloyds.api2')
        GROUP BY channel;
        """

        for name, id in plan_ids.items():
            with hermes_db.cursor() as cur:
                cur.execute(success_query, (id,))
                result = {k: v for k, v in cur.fetchall() if k is not None}
                success_results[name] = result

                cur.execute(pending_query, (id,))
                result = {k: v for k, v in cur.fetchall() if k is not None}
                pending_results[name] = result

                cur.execute(failed_query, (id,))
                result = {k: v for k, v in cur.fetchall() if k is not None}
                failed_results[name] = result

        success_results["total"] = sum(itertools.chain(*[success_results[k].values() for k in success_results.keys()]))
        pending_results["total"] = sum(itertools.chain(*[pending_results[k].values() for k in pending_results.keys()]))
        failed_results["total"] = sum(itertools.chain(*[failed_results[k].values() for k in failed_results.keys()]))

        return {"success": success_results, "pending": pending_results, "failed": failed_results}

    def payment_accounts(self) -> dict:
        """
        Returns count of payment accounts for success, pending, and failed statuses
        """
        hermes_db = psycopg2.connect(self.hermes_dsn)
        results = {}

        queries = {
            "success": """
            SELECT "user".bundle_id AS channel, count(ubiquity_paymentcardaccountentry.id)
            AS successful_pcards FROM ubiquity_paymentcardaccountentry
            INNER JOIN "user" ON ubiquity_paymentcardaccountentry.user_id = "user".id
            INNER JOIN payment_card_paymentcardaccount
            ON ubiquity_paymentcardaccountentry.payment_card_account_id = payment_card_paymentcardaccount.id
            WHERE payment_card_paymentcardaccount.status = 1
            AND payment_card_paymentcardaccount.is_deleted = False
            AND "user".bundle_id IN ('com.bos.api2', 'com.halifax.api2', 'com.lloyds.api2')
            GROUP BY channel;
            """,
            "pending": """
            SELECT "user".bundle_id AS channel, count(ubiquity_paymentcardaccountentry.id)
            AS pending_pcards FROM ubiquity_paymentcardaccountentry
            INNER JOIN "user" ON ubiquity_paymentcardaccountentry.user_id = "user".id
            INNER JOIN payment_card_paymentcardaccount
            ON ubiquity_paymentcardaccountentry.payment_card_account_id = payment_card_paymentcardaccount.id
            WHERE payment_card_paymentcardaccount.status = 0
            AND payment_card_paymentcardaccount.is_deleted = False
            AND "user".bundle_id IN ('com.bos.api2', 'com.halifax.api2', 'com.lloyds.api2')
            GROUP BY channel;
            """,
            "failed": """
            SELECT "user".bundle_id AS channel, count(ubiquity_paymentcardaccountentry.id)
            AS failed_pcards FROM ubiquity_paymentcardaccountentry
            INNER JOIN "user" ON ubiquity_paymentcardaccountentry.user_id = "user".id
            INNER JOIN payment_card_paymentcardaccount
            ON ubiquity_paymentcardaccountentry.payment_card_account_id = payment_card_paymentcardaccount.id
            WHERE payment_card_paymentcardaccount.status not in (0, 1)
            AND payment_card_paymentcardaccount.is_deleted = False
            AND "user".bundle_id IN ('com.bos.api2', 'com.halifax.api2', 'com.lloyds.api2')
            GROUP BY channel;
            """,
        }

        for name, query in queries.items():
            with hermes_db.cursor() as cur:
                cur.execute(query)
                result = {k: v for k, v in cur.fetchall() if k is not None}
                results[name] = result

        results["success"]["total"] = sum(results["success"].values())
        results["pending"]["total"] = sum(results["pending"].values())
        results["failed"]["total"] = sum(results["failed"].values())

        return results

    def run_la_query(self, query: str) -> LogsQueryResult:
        credential = DefaultAzureCredential()
        client = LogsQueryClient(credential)
        for _ in range(3):
            try:
                req = client.query_workspace(
                    workspace_id=self.workspace_id, query=query, timespan=(pendulum.duration(days=1))
                )
            except ServiceResponseError:
                logger.warning("Failed, probably retrying")
                continue
            if req.status == LogsQueryStatus.PARTIAL:
                logger.warning("Failed, probably retrying")
                continue
            elif req.status == LogsQueryStatus.SUCCESS:
                return req.tables[0].rows

    def api_stats(self) -> dict:
        """
        Gets API Performance, Status Codes, and number of DELETE requests for past 24 hours
        """
        percentiles_query = """
        AzureDiagnostics
        | where Category == "FrontDoorAccessLog"
        | where requestUri_s startswith "https://api.gb.bink.com:443/v2"
        | where userAgent_s startswith "Apache-HttpClient"
        | summarize percentiles(todouble(timeTaken_s), 50, 95, 99)
        """
        percentiles = self.run_la_query(percentiles_query)[0]

        status_codes_query = """
        AzureDiagnostics
        | where Category == "FrontDoorAccessLog"
        | where requestUri_s startswith "https://api.gb.bink.com:443/v2"
        | where userAgent_s startswith "Apache-HttpClient"
        | summarize count() by httpStatusCode_d
        """
        status_codes = {k: v for (k, v) in self.run_la_query(status_codes_query)}
        total_calls = sum(status_codes.values())

        deletions = {}
        for endpoint in ["/v2/me", "/v2/loyalty_cards", "/v2/payment_accounts"]:
            delete_query = f"""
            AzureDiagnostics
            | where Category == "FrontDoorAccessLog"
            | where requestUri_s startswith "https://api.gb.bink.com:443{endpoint}"
            | where userAgent_s startswith "Apache-HttpClient"
            | where httpMethod_s == "DELETE"
            | summarize count()
            """
            deletions[endpoint] = self.run_la_query(delete_query)[0][0]

        results = {
            "percentiles": {
                "p50": round(percentiles[0], 3),
                "p95": round(percentiles[1], 3),
                "p99": round(percentiles[2], 3),
            },
            "calls": total_calls,
            "status_codes": status_codes,
            "deletions": deletions,
        }

        return results

    def run(self) -> dict:
        if settings.demo_mode:
            return {
                "users": {"com.bos.api2": 6, "com.halifax.api2": 9, "com.lloyds.api2": 284, "total": 299},
                "api_stats": {
                    "percentiles": {"p50": 0.037, "p95": 0.132, "p99": 0.379},
                    "calls": 2194,
                    "status_codes": {200: 1754, 201: 357, 202: 60, 499: 1, 422: 19, 400: 3},
                    "deletions": {"/v2/me": 6, "/v2/loyalty_cards": 15, "/v2/payment_accounts": 0},
                },
                "loyalty_accounts": {
                    "success": {
                        "iceland": {"com.bos.api2": 1, "com.halifax.api2": 1, "com.lloyds.api2": 8},
                        "squaremeal": {"com.bos.api2": 2, "com.halifax.api2": 1, "com.lloyds.api2": 6},
                        "viator": {"com.bos.api2": 1, "com.lloyds.api2": 6},
                        "wasabi": {},
                        "total": 26,
                    },
                    "pending": {
                        "iceland": {"com.lloyds.api2": 8},
                        "squaremeal": {},
                        "viator": {},
                        "wasabi": {},
                        "total": 8,
                    },
                    "failed": {
                        "iceland": {"com.bos.api2": 1},
                        "squaremeal": {},
                        "viator": {},
                        "wasabi": {},
                        "total": 1,
                    },
                },
                "payment_accounts": {
                    "success": {"com.bos.api2": 6, "com.halifax.api2": 7, "com.lloyds.api2": 389, "total": 402},
                    "pending": {"total": 0},
                    "failed": {"total": 0},
                },
            }
        redis = StrictRedis.from_url(str(settings.redis_dsn))
        if redis.exists(self.redis_key):
            return json.loads(redis.get(self.redis_key))

        users = self.users()
        loyalty_accounts = self.loyalty_accounts()
        payment_accounts = self.payment_accounts()
        api_stats = self.api_stats()
        results = {
            "users": users,
            "api_stats": api_stats,
            "loyalty_accounts": loyalty_accounts,
            "payment_accounts": payment_accounts,
        }
        redis.set(self.redis_key, json.dumps(results), ex=pendulum.duration(minutes=10))

        return results
