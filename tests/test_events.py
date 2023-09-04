import pendulum
from loguru import logger
from sqlalchemy.orm import Session

from snowstorm.database import Events, engine
from snowstorm.deployments.event_processor import Deploy_EventProcessor
from snowstorm.jobs.database_cleanup import Job_DatabaseCleanup
from snowstorm.jobs.events import Job_EventCreate

queue = "test_queue"


def test_create_event(test_event_count: int) -> None:
    """
    Create test events
    """
    events = Job_EventCreate(queue, test_event_count)
    events.create_event()


def test_process_events(days: int, test_event_count: int) -> None:
    global latest_events_count
    """
    Count of events in database before processing test events
    """
    past_events_count = return_events_count(days, False)
    latest_events_count = return_events_count(days)

    """
    Collects Events from RabbitMQ and stores in database
    """
    events_processor = Deploy_EventProcessor(queue, False, 1)
    events_processor.get_messages()

    """
    Count of events in database after processing test events
    """
    total_past_events_count = return_events_count(days, False)
    logger.info(f"Number of events older than {days} days in database: " + str(total_past_events_count))

    assert total_past_events_count == past_events_count + test_event_count
    """ The latest events count should remanins the same if no other new events
     created during the test from other sources"""
    assert return_events_count(days) >= latest_events_count


def test_clean_up_events(days: int) -> None:
    global latest_events_count
    """
    Removes records from database
    """
    clean = Job_DatabaseCleanup(days)
    clean.cleanup()

    """
    Asserts that there are no records in the database older than number of days passed
    """
    assert return_events_count(days, False) == 0
    assert return_events_count(days) >= latest_events_count


def return_events_count(days: int, latest: bool = True) -> int:
    """
    Reads events from events table in database that are older than number of days passed
    """
    delta = pendulum.today().subtract(days=days)
    with Session(engine) as session:
        if latest:
            events = session.query(Events).filter(Events.event_date_time > delta)
        else:
            events = session.query(Events).filter(Events.event_date_time <= delta)
            logger.warning(f"record count: {events.count()}")
            logger.info(events.count())
            session.commit()
    return events.count()
