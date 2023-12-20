from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin
from kombu.transport.pyamqp import Message
from loguru import logger
from prometheus_client import Counter, start_wsgi_server
from sqlalchemy.orm import Session

from snowstorm.database import Events, engine
from snowstorm.settings import settings

c = Counter("snowstorm_events", "Number of events processed", ["event_type"])


class Deploy_EventProcessor(ConsumerMixin):
    def __init__(self, queues: str):
        self.queues = [Queue(queue, Exchange(queue, type="direct"), routing_key=queue) for queue in queues.split(",")]
        self.connection = Connection(str(settings.rabbitmq_dsn))
        try:
            start_wsgi_server(9100)
        except OSError:
            logger.warning("Prometheus metrics server already running")

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=self.queues, auto_declare=False, callbacks=[self.on_message])]

    def on_message(self, body: dict, message: Message) -> None:
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
        with Connection(str(settings.rabbitmq_dsn)) as conn, conn.SimpleQueue("snowstorm_deadletter") as queue:
            queue.put(body)
