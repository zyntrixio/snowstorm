"""Pulls data from Olympus Applications for ingest into Data Warehouse."""

import typer
from typing_extensions import Annotated

cli = typer.Typer()


@cli.command()
def database_cleanup(days: Annotated[int, typer.Option(help="Number of days to keep")]) -> None:
    """Remove old records from database."""
    from snowstorm.tasks.database_cleanup import DatabaseCleanup

    clean = DatabaseCleanup(days=days)
    clean.cleanup()


@cli.command()
def event_processor(queues: Annotated[str, typer.Option(help="Comma seperated list of queues")]) -> None:
    """Collect Olympus Events from RabbitMQ."""
    from snowstorm.tasks.events import EventProcessor

    EventProcessor(queues=queues).run()


@cli.command()
def event_create(
    queue: Annotated[str, typer.Option(help="Name of the queue to populate")],
    count: Annotated[int, typer.Option(help="Number of items to add")],
) -> None:
    """Create fake events in RabbitMQ."""
    from snowstorm.tasks.events import EventCreate

    create_events = EventCreate(queue_name=queue, message_count=count)
    create_events.create_event()


@cli.command()
def freshservice(
    days: Annotated[int, typer.Option(help="Number of days worth of data to collect")],
    rate_limit_timeout: Annotated[str, typer.Option(help="Rate limit timeout in seconds")],
) -> None:
    """Collect Data from FreshService."""
    from snowstorm.tasks.freshservice import FreshServiceStats

    fs = FreshServiceStats(days=days, rate_limit_timeout=rate_limit_timeout)
    fs.fetch_stats()
