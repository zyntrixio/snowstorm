from time import sleep

from amqp.exceptions import NotFound
from kombu import Connection
from loguru import logger
from sqlalchemy.orm import Session

from snowstorm.database import Events, engine
from snowstorm.settings import settings


class Deploy_EventProcessor:
    def __init__(self, queue: str, forever: bool, timeout: int = 30) -> None:
        self.rabbitmq_dsn = settings.rabbitmq_dsn
        self.queue = queue
        self.forever = forever
        self.timeout = timeout

    def get_messages(self) -> None:
        while True:
            with (
                Connection(self.rabbitmq_dsn) as conn,
                conn.SimpleQueue(self.queue, queue_opts={"no_declare": True}) as queue,
            ):
                try:
                    message = queue.get(block=True, timeout=self.timeout)
                    self.process_message(message=message.payload)
                    message.ack()
                except NotFound:
                    sleep(120)
                except queue.Empty:
                    if not self.forever:
                        break

    def process_message(self, message: str) -> None:
        logger.warning("Processing event", extra={"queue_name": self.queue})
        try:
            event_date_time = message.pop("event_date_time")
            event_type = message.pop("event_type")
            event = {
                "event_date_time": event_date_time,
                "event_type": event_type,
                "json": message,
            }
        except KeyError:
            self.dead_letter(message)
            logger.warning("Message does not contain the required JSON fields", extra=message)
            return
        insert = Events(**event)
        with Session(engine) as session:
            session.add(insert)
            session.commit()

        if settings.debug_mode:
            logger.info("Event payload: {}", event)

    def dead_letter(self, message: str) -> None:
        with Connection(self.rabbitmq_dsn) as conn, conn.SimpleQueue("snowstorm_deadletter") as queue:
            queue.put(message)
