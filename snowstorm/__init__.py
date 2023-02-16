import socket
from datetime import timedelta

import redis
from loguru import logger

from snowstorm.settings import settings


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
        logger.warning("Leader Election Failed, exiting.")
    return is_leader
