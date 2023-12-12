import click
import uvicorn

from snowstorm.deployments.event_processor import Deploy_EventProcessor
from snowstorm.jobs.apistats import Job_APIStats
from snowstorm.jobs.database_cleanup import Job_DatabaseCleanup
from snowstorm.jobs.events import Job_EventCreate
from snowstorm.jobs.freshservice import Job_FreshService
from snowstorm.jobs.viator_reports import Job_ViatorReports
from snowstorm.mi.lloyds_notification import Notification_Lloyds


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
    pass


@cli.group()
def deploy():
    """
    Tasks designed to be executed as Kubernetes Deployments
    """
    pass


@cli.group()
def mi():
    """
    Management Information: Includes Jobs for Stats Collection, Teams Notifications, and a Web Server
    """
    pass


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


@job.command(name="viator")
def viator_reports():
    """
    Sends Viator Reports
    """
    report = Job_ViatorReports()
    report.run()


@deploy.command(name="events")
@click.option("-q", "--queues", default="snowstorm_test", help="Queues to process, comma seperated", show_default=True)
def event_processor(queues: str):
    """
    Collects Olympus Events from RabbitMQ
    """
    Deploy_EventProcessor(queues=queues).run()


@mi.command(name="notification")
def mi_lloyds_notification():
    """
    Send a notification to Microsoft Teams with Lloyds Stats
    """
    notification = Notification_Lloyds()
    notification.send()


@mi.command(name="webserver")
def mi_webserver():
    """
    Launch a WebServer on 0.0.0.0:6502 with latest Lloyds Stats
    """
    uvicorn.run("snowstorm.mi.webserver:app", host="0.0.0.0", port=6502)


if __name__ == "__main__":
    cli()
