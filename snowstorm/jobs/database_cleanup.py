import logging

import pendulum
from sqlalchemy.orm import Session

from snowstorm import leader_election
from snowstorm.database import APIStats, Events, FreshService, engine

log = logging.getLogger(__name__)


class Job_DatabaseCleanup:
    def __init__(self, days: int) -> None:
        self.days = days

    def cleanup(self) -> None:
        if not leader_election(job_name="database_cleanup"):
            return None
        delta = pendulum.today().subtract(days=self.days)
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
