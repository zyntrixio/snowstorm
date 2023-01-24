# Snowstorm

Snowstorm intends to be the glue that sits between DevOps and Data Management, it's resposible for collecting data from a myriad of systems and storing the data in Postgres. This data is then collected and shipped to Snowflake via Airbyte and Prefect.

Postgres was chosen as the desired technology set as it gives clear seperation of responsibility between DevOps and Data Management while providing strong deduplication of records from unreliable sources.
