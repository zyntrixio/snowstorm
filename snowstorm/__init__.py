import logging
import socket
from datetime import timedelta

import redis
from pythonjsonlogger import jsonlogger

from snowstorm.settings import settings

log = logging.getLogger()
logHandler = logging.StreamHandler()
logFmt = jsonlogger.JsonFormatter(timestamp=True)
logHandler.setFormatter(logFmt)
log.addHandler(logHandler)


def leader_election(job_name: str) -> bool:
    if settings.leader_election_enabled:
        r = redis.Redis.from_url(settings.redis_dsn)
        lock_key = f"snowstorm-{job_name}"
        hostname = socket.gethostname()
        is_leader = False

        with r.pipeline() as pipe:
            try:
                pipe.watch(lock_key)
                leader_host = pipe.get(lock_key)
                if leader_host in (hostname.encode(), None):
                    pipe.multi()
                    pipe.setex(lock_key, timedelta(minutes=3), hostname)
                    pipe.execute()
                    is_leader = True
            except redis.WatchError:
                pass
    else:
        is_leader = True
    if not is_leader:
        logging.warning("Leader Election Failed, exiting.")
    return is_leader
