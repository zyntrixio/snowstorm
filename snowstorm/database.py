from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base

from snowstorm.settings import settings

engine = create_engine(settings.database_dsn, echo=False)
base = declarative_base()


class APIStats(base):
    __tablename__ = "apistats"

    id = Column(String, primary_key=True)
    date_time = Column(DateTime)
    method = Column(String)
    path = Column(String)
    status_code = Column(Integer)
    response_time = Column(Float)
    user_agent = Column(String)
    client_ip = Column(String)
    ms_pop = Column(String)
    client_country = Column(String)


class APIStats_Summary(base):
    __tablename__ = "apistats_summary"

    date = Column(DateTime, primary_key=True)
    p50 = Column(Float)
    p95 = Column(Float)
    p99 = Column(Float)
    calls = Column(Integer)
    calls_by_status_code = Column(JSON)


class FreshService(base):
    __tablename__ = "freshservice"

    id = Column(Integer, primary_key=True, autoincrement=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    status = Column(String)
    channel = Column(String, nullable=True)
    service = Column(String, nullable=True)
    mi = Column(String, nullable=True)
    sla_breached = Column(Boolean, nullable=True)


class Events(base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    event_date_time = Column(DateTime)
    event_type = Column(String)
    json = Column(JSON)
