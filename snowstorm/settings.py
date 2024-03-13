"""Main settings module for Snowstorm."""

from pydantic import AmqpDsn, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Main settings class for Snowstorm."""

    database_dsn: PostgresDsn = "postgresql://postgres@localhost:5432/postgres"
    rabbitmq_dsn: AmqpDsn = "amqp://guest:guest@localhost:5672/"

    freshservice_api_key: str = "dqbA9LSZg9q9EIKxg82N"

    storage_account_name: str | None = None
    storage_account_auth: str | None = None
    storage_account_container: str = "viator"

    mailgun_key: str = "b09950929bd21cbece22c22b2115736d-e5e67e3e-068f44cc"
    debug_mode: bool = False


settings = Settings()
