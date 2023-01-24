from pydantic import AmqpDsn, BaseSettings, PostgresDsn, RedisDsn


class Settings(BaseSettings):
    database_dsn: PostgresDsn = "postgresql://postgres@localhost:5432/postgres"
    rabbitmq_dsn: AmqpDsn = "amqp://guest:guest@localhost:5672/"
    redis_dsn: RedisDsn = "redis://localhost:6379/"

    workspace_id: str = "eed2b98d-3396-4972-be3e-3e744532f7cd"
    freshservice_api_key: str = "dqbA9LSZg9q9EIKxg82N"
    leader_election_enabled: bool = True


settings = Settings()
