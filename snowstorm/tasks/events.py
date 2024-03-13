"""Event Processor and Event Create Tasks."""

from random import choice, randint

import pendulum
from faker import Faker
from faker.providers import internet
from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin
from kombu.transport.pyamqp import Message
from loguru import logger
from prometheus_client import Counter, start_wsgi_server
from sqlalchemy.orm import Session

from snowstorm.database import Events, engine
from snowstorm.settings import settings

c = Counter("snowstorm_events", "Number of events processed", ["event_type"])


class EventProcessor(ConsumerMixin):
    """Event Processor Class."""

    def __init__(self, queues: str):
        """Initialize EventProcessor."""
        self.queues = [Queue(queue, Exchange(queue, type="direct"), routing_key=queue) for queue in queues.split(",")]
        self.connection = Connection(str(settings.rabbitmq_dsn))
        try:
            start_wsgi_server(9100)
        except OSError:
            logger.warning("Prometheus metrics server already running")

    def get_consumers(self, Consumer, channel):  # noqa: ANN201, N803, ANN001, ARG002
        """Return a list of consumers."""
        return [Consumer(queues=self.queues, auto_declare=False, callbacks=[self.on_message])]

    def on_message(self, body: dict, message: Message) -> None:
        """Process the message."""
        logger.info(f"Processing event for queue: {message.delivery_info['routing_key']}")
        try:
            event_date_time = body.pop("event_date_time")
            event_type = body.pop("event_type")
            event = {
                "event_date_time": event_date_time,
                "event_type": event_type,
                "json": body,
            }
        except KeyError:
            self.dead_letter(body)
            logger.warning("Message does not contain the required JSON fields", extra=body)
            return
        insert = Events(**event)
        with Session(engine) as session:
            session.add(insert)
            session.commit()
        if settings.debug_mode:
            logger.info("Event payload: {}", event)
        c.labels(event_type=event_type).inc()
        message.ack()

    def dead_letter(self, body: str) -> None:
        """Send the message to the dead letter queue."""
        with Connection(str(settings.rabbitmq_dsn)) as conn, conn.SimpleQueue("snowstorm_deadletter") as queue:
            queue.put(body)


class EventCreate:
    """Event Create Class."""

    def __init__(self, queue_name: str, message_count: int) -> None:
        """Initialize EventCreate."""
        self.rabbitmq_dsn = str(settings.rabbitmq_dsn)
        self.queue_name = queue_name
        self.message_count = message_count
        self.fake = Faker()
        self.fake.add_provider(internet)

    def create_event(self) -> None:
        """Create fake events."""
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
            with Connection(str(self.rabbitmq_dsn)) as conn, conn.SimpleQueue(self.queue_name) as queue:
                queue.put(msg_payload)
