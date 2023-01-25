import json
import logging
from datetime import date, timedelta
from random import choice, randint
from time import sleep

import pika
import requests
from azure.core.exceptions import ServiceResponseError
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from faker import Faker
from faker.providers import internet
from sqlalchemy.orm import Session

from snowstorm import leader_election
from snowstorm.database import APIStats, Events, FreshService, engine
from snowstorm.settings import settings

log = logging.getLogger(__name__)


class Job_APIStats:
    def __init__(self, retries: int, days: int, domain: str) -> None:
        self.workspace_id = settings.workspace_id
        self.domain = domain
        self.retries = retries
        self.days = days

    def fetch_logs(self) -> list:
        credential = DefaultAzureCredential()
        client = LogsQueryClient(credential)
        query = f"""
        AzureDiagnostics
        | where Category == "FrontDoorAccessLog"
        | where requestUri_s startswith "https://{self.domain}:443/ubiquity"
             or requestUri_s startswith "https://{self.domain}:443/v2"
        | extend path = replace_regex(
            replace_regex(tostring(parse_url(requestUri_s)["Path"]), @"hash-.+", @"{{id}}"), @"/\\d+", @"{{id}}")
        | project
            _ItemId,
            TimeGenerated,
            httpMethod_s,
            path,
            httpStatusCode_d,
            timeTaken_s,
            userAgent_s,
            clientIp_s,
            pop_s,
            clientCountry_s
        """
        for retry in range(self.retries):
            try:
                log.warning(f"Running query, attempt {retry} of {self.retries}")
                response = client.query_workspace(
                    workspace_id=self.workspace_id, query=query, timespan=timedelta(days=self.days, hours=1)
                )
            except ServiceResponseError:
                log.warning("Failed, probably retrying")
                continue
            if response.status == LogsQueryStatus.PARTIAL:
                log.warning("Failed, probably retrying")
                continue
            elif response.status == LogsQueryStatus.SUCCESS:
                return response.tables[0].rows

    def store_logs(self) -> None:
        if not leader_election(job_name="apistats"):
            return None
        logs = self.fetch_logs()
        log_count = len(logs)
        with Session(engine) as session:
            for iteration, element in enumerate(logs, 1):
                if iteration % 100 == 0 or iteration == log_count:
                    logging.warning(f"Inserting Record {iteration} of {log_count}")
                insert = APIStats(
                    id=element[0],
                    date_time=element[1],
                    method=element[2],
                    path=element[3],
                    status_code=element[4],
                    response_time=element[5],
                    user_agent=element[6],
                    client_ip=element[7],
                    ms_pop=element[8],
                    client_country=element[9],
                )
                session.merge(insert)
            session.commit()


class Job_FreshService:
    def __init__(self, days: int, rate_limit_timeout: int) -> None:
        self.status_mapping = {2: "Open", 3: "Pending", 4: "Resolved", 5: "Closed"}
        self.days = days
        self.api_key = settings.freshservice_api_key
        self.rate_limit_timeout = rate_limit_timeout

    def fetch_stats(self) -> None:
        if not leader_election(job_name="freshservice"):
            return None
        page = 1
        tickets = []
        while True:
            log.warning(f"Processing page {page}")
            lookup = requests.get(
                "https://bink.freshservice.com/api/v2/tickets",
                params={
                    "page": page,
                    "per_page": 100,
                    "updated_since": date.today() - timedelta(days=self.days, hours=1),
                },
                auth=(self.api_key, "X"),
            )
            if lookup.status_code == 429:
                log.warning(f"Rate limit hit, sleeping {self.rate_limit_timeout} seconds")
                sleep(self.rate_limit_sleep)
                continue
            if len(lookup.json()["tickets"]) != 0:
                page += 1
                for ticket in lookup.json()["tickets"]:
                    tickets.append(ticket)
            else:
                log.warning("No pages remaining", extra={"ticket_count": len(tickets)})
                break

        with Session(engine) as session:
            for ticket in tickets:
                sla = ticket["custom_fields"]["incident_sla_resolution"]
                insert = FreshService(
                    id=ticket["id"],
                    created_at=ticket["created_at"],
                    updated_at=ticket["updated_at"],
                    status=self.status_mapping[ticket["status"]],
                    channel=ticket["custom_fields"]["channel"] if ticket["custom_fields"]["channel"] != "N/A" else None,
                    service=ticket["custom_fields"]["service"],
                    mi=ticket["custom_fields"]["mi"],
                    sla_breached=True if sla == "Breached" else False if sla == "Achieved" else None,
                )
                session.merge(insert)
            session.commit()


class Job_DatabaseCleanup:
    def __init__(self, days: int) -> None:
        self.days = days

    def cleanup(self) -> None:
        if not leader_election(job_name="database_cleanup"):
            return None
        delta = date.today() - timedelta(days=self.days)
        with Session(engine) as session:
            apistats = session.query(APIStats).filter(APIStats.date_time <= delta)
            logging.warning("apistats records found", extra={"record_count": apistats.count()})
            apistats.delete()

            freshservice = session.query(FreshService).filter(FreshService.updated_at <= delta)
            logging.warning("freshservice records found", extra={"record_count": freshservice.count()})
            freshservice.delete

            events = session.query(Events).filter(Events.event_date_time <= delta)
            logging.warning("events records found", extra={"record_count": events.count()})
            events.delete()

            session.commit()


class Job_EventCreate:
    def __init__(self, queue_name: str, message_count: int) -> None:
        self.rabbitmq_dsn = settings.rabbitmq_dsn
        self.queue_name = queue_name
        self.message_count = message_count
        self.fake = Faker()
        self.fake.add_provider(internet)

    def create_event(self) -> None:
        with pika.BlockingConnection(pika.URLParameters(self.rabbitmq_dsn)) as conn:
            channel = conn.channel()
            channel.queue_declare(queue=self.queue_name)
            for _ in range(self.message_count):
                event_date_time = date.today() - timedelta(
                    days=randint(0, 1000),
                    hours=randint(0, 24),
                    minutes=randint(0, 60),
                    seconds=randint(0, 60),
                )
                event_types = [
                    "user.session.start",
                    "lc.auth.failed",
                    "lc.addandauth.success",
                    "lc.register.request",
                    "lc.join.request",
                    "user.created",
                    "lc.auth.success",
                    "lc.register.success",
                    "lc.join.failed",
                    "user.deleted",
                    "lc.auth.request",
                    "transaction.exported",
                    "lc.join.success",
                    "lc.statuschange",
                    "lc.addandauth.request",
                    "payment.account.status.change",
                    "lc.addandauth.failed",
                    "payment.account.added",
                    "payment.account.removed",
                    "lc.register.failed",
                    "lc.removed",
                ]
                msg_payload = {
                    "event_type": choice(event_types),
                    "origin": "channel",
                    "channel": "bink",
                    "event_date_time": event_date_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "external_user_ref": str(randint(100000000, 999999999)),
                    "internal_user_ref": randint(1, 999),
                    "email": self.fake.free_email(),
                }
                logging.warning("Creating Event", extra=msg_payload)
                channel.basic_publish(
                    exchange="",
                    routing_key=self.queue_name,
                    body=json.dumps(msg_payload),
                )
