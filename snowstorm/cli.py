import logging

import click

from snowstorm.deploy import Deploy_EventProcessor
from snowstorm.jobs import Job_APIStats, Job_DatabaseCleanup, Job_EventCreate, Job_FreshService

log = logging.getLogger(__name__)


@click.group()
def cli():
    """
    Snowstorm ships data from anything to a PostgreSQL Database
    for consumption by Airbyte/Prefect
    """
    pass


@cli.group()
def job():
    """
    Tasks designed to be executed as Kubernetes CronJobs
    """


@cli.group()
def deploy():
    """
    Tasks designed to be executed as Kubernetes Deployments
    """


@job.command(name="apistats")
@click.option("-r", "--retries", default=10, help="Number of retries to execute on failure", show_default=True)
@click.option("-d", "--days", default=1, help="Number of days worth of logs to collect", show_default=True)
@click.option("-d", "--domain", default="api.gb.bink.com", help="Domain to use for log collection", show_default=True)
def apistats(retries: int, days: int, domain: str):
    """
    Collects API Stats from Log Analytics
    """
    apistats = Job_APIStats(retries=retries, days=days, domain=domain)
    apistats.store_logs()


@job.command(name="create_events")
@click.option("-q", "--queue", default="snowstorm_test", help="Queue Name to add events to", show_default=True)
@click.option("-c", "--count", default=100, help="Number of Events to Create", show_default=True)
def create_events(queue: str, count: int):
    """
    Creates fake events in RabbitMQ
    """
    create_events = Job_EventCreate(queue_name=queue, message_count=count)
    create_events.create_event()


@job.command(name="freshservice")
@click.option("-d", "--days", default=1, help="Days worth of tickets to collect", show_default=True)
@click.option("-s", "--rate_limit_timeout", default=60, help="Seconds to sleep after rate limit", show_default=True)
def freshservice(days: int, rate_limit_timeout: str):
    """
    Collects Data from FreshService
    """
    fs = Job_FreshService(days=days, rate_limit_timeout=rate_limit_timeout)
    fs.fetch_stats()


@job.command(name="cleanup")
@click.option("-d", "--days", default=35, help="Days to keep", show_default=True)
def cleanup(days: int):
    """
    Removes old records from database
    """
    clean = Job_DatabaseCleanup(days=days)
    clean.cleanup()


@deploy.command(name="events")
@click.option("-q", "--queues", default="snowstorm_test", help="Queues to use, comma seperated", show_default=True)
def event_processor(queues: str):
    """
    Collects Olympus Events from RabbitMQ
    """
    event_processor = Deploy_EventProcessor(queues=queues)
    event_processor.get_messages()


if __name__ == "__main__":
    cli()
