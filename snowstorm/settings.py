from pydantic import AmqpDsn, BaseSettings, PostgresDsn, RedisDsn


class Settings(BaseSettings):
    database_dsn: PostgresDsn = "postgresql://postgres@localhost:5432/postgres"
    rabbitmq_dsn: AmqpDsn = "amqp://guest:guest@localhost:5672/"
    redis_dsn: RedisDsn = "redis://localhost:6379/"

    leader_election_enabled: bool = True
    freshservice_api_key: str = "dqbA9LSZg9q9EIKxg82N"
    workspace_id: str = "eed2b98d-3396-4972-be3e-3e744532f7cd"
    webserver_auth_token: str = "4e97f9c1-c259-4858-99d4-191800b75946"
    demo_mode: bool = False

    storage_account_name: str = "binkuksouthtableau"
    storage_account_auth: str = (
        "GaMOLH0tSGZwxMC95P6OiOWfCa8duyLM04YcIJI7lsFYrRlR20GXpy9j0dK/UNafIchpsW3+lFfp+AStfYWhMQ=="
    )
    storage_account_container: str = "viator"

    mailgun_key: str = "b09950929bd21cbece22c22b2115736d-e5e67e3e-068f44cc"


settings = Settings()
