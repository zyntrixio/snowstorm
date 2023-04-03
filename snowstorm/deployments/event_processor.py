import json
from time import sleep

import pika
from loguru import logger
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties
from sqlalchemy.orm import Session

from snowstorm.database import Events, engine
from snowstorm.settings import settings


class Deploy_EventProcessor:
    def __init__(self, queues: str) -> None:
        self.rabbitmq_dsn = settings.rabbitmq_dsn
        self.queue_names = queues

    def get_messages(self) -> None:
        while True:
            try:
                with pika.BlockingConnection(pika.URLParameters(self.rabbitmq_dsn)) as conn:
                    channel = conn.channel()
                    for queue in self.queue_names.split(","):
                        channel.basic_consume(
                            queue=queue,
                            on_message_callback=self.process_event,
                            auto_ack=False,
                        )
                    try:
                        channel.start_consuming()
                    except KeyboardInterrupt:
                        channel.stop_consuming()
                        break
            except (pika.exceptions.ChannelClosedByBroker, pika.exceptions.AMQPConnectionError):
                sleep(60)
                continue

    def dead_letter(self, msg: bytes) -> None:
        with pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_dsn)) as connection:
            channel = connection.channel()
            channel.queue_declare(queue="snowstorm_deadletter", durable=True)
            channel.basic_publish(exchange="", routing_key="snowstorm_deadletter", body=json.dumps(msg.decode()))

    def process_event(
        self, ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, message: bytes
    ) -> None:
        logger.warning("Processing event", extra={"queue_name": method.routing_key})
        try:
            raw_msg = json.loads(message.decode())
            event_date_time = raw_msg.pop("event_date_time")
            event_type = raw_msg.pop("event_type")
            event = {
                "event_date_time": event_date_time,
                "event_type": event_type,
                "json": raw_msg,
            }
        except KeyError:
            self.dead_letter(message)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.warning("Message does not contain the required JSON fields", extra=raw_msg)
            return

        retries = 3
        while True:
            try:
                insert = Events(**event)
                with Session(engine) as session:
                    session.add(insert)
                    session.commit()
                ch.basic_ack(delivery_tag=method.delivery_tag)
                break
            except Exception as ex:
                retries -= 1
                if retries < 1:
                    logger.warning(msg="Event processing failed, sending to Dead Letter Queue", exc_info=ex)
                    self.dead_letter(message.decode())
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    break
                else:
                    logger.warning(msg="Event processing failed, retrying", exc_info=ex)
                    continue
