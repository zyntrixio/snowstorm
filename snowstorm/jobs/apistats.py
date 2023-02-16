import pendulum
from azure.core.exceptions import ServiceResponseError
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from loguru import logger
from sqlalchemy.orm import Session

from snowstorm import leader_election
from snowstorm.database import APIStats, engine
from snowstorm.settings import settings


class Job_APIStats:
    def __init__(self, retries: int, days: int, domain: str) -> None:
        self.workspace_id = settings.workspace_id
        self.domain = domain
        self.retries = retries
        self.days = days

    def fetch_logs(self, start_date: pendulum.DateTime, end_date: pendulum.DateTime) -> list:
        credential = DefaultAzureCredential()
        client = LogsQueryClient(credential)
        query = f"""
        AzureDiagnostics
        | where Category == "FrontDoorAccessLog"
        | where requestUri_s startswith "https://{self.domain}:443/ubiquity"
             or requestUri_s startswith "https://{self.domain}:443/v2"
        | extend path = replace_regex(
            replace_regex(tostring(parse_url(requestUri_s)["Path"]), @"hash-.+", @"{{id}}"), @"/\\d+", @"/{{id}}")
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
                logger.warning(f"Running query, attempt {retry} of {self.retries}")
                response = client.query_workspace(
                    workspace_id=self.workspace_id, query=query, timespan=(start_date, end_date)
                )
            except ServiceResponseError:
                logger.warning("Service Response Error")
                continue
            if response.status == LogsQueryStatus.PARTIAL:
                logger.warning("Partial Results, Retrying")
                continue
            elif response.status == LogsQueryStatus.SUCCESS:
                return response.tables[0].rows

    def store_logs(self) -> None:
        if not leader_election(job_name="apistats"):
            return None
        for day in range(self.days):
            start_date = pendulum.today().subtract(days=day, hours=1)
            end_date = start_date.add(days=1, hours=1)
            logs = self.fetch_logs(start_date=start_date, end_date=end_date)
            log_count = len(logs)
            with Session(engine) as session:
                for iteration, element in enumerate(logs, 1):
                    if iteration % 100 == 0 or iteration == log_count:
                        logger.warning(f"Inserting Record {iteration} of {log_count}")
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
