from random import choice, randint

import pendulum
from faker import Faker
from faker.providers import internet
from kombu import Connection
from loguru import logger

from snowstorm.settings import settings


class Job_EventCreate:
    def __init__(self, queue_name: str, message_count: int) -> None:
        self.rabbitmq_dsn = settings.rabbitmq_dsn
        self.queue_name = queue_name
        self.message_count = message_count
        self.fake = Faker()
        self.fake.add_provider(internet)

    def create_event(self) -> None:
        for _ in range(self.message_count):
            event_date_time = pendulum.today().subtract(
                days=randint(0, 1000),
                hours=randint(0, 24),
                minutes=randint(0, 60),
                seconds=randint(0, 60),
                microseconds=randint(0, 999999),
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
            logger.warning("Creating Event", extra=msg_payload)
            with Connection(self.rabbitmq_dsn) as conn, conn.SimpleQueue(self.queue_name) as queue:
                queue.put(msg_payload)
