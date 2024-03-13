# Snowstorm

Snowstorm is the glue that sits between Bink Applications and Data Warehouse, it's resposible for collecting data from a myriad of systems via either a AMQP or HTTP interface and storing the resulting data in Postgres. This data is then collected and shipped to Snowflake via Airbyte and Prefect.
