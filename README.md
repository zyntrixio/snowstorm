# Snowstorm

Snowstorm intends to be the glue that sits between DevOps and Data Management, it's resposible for collecting data from a myriad of systems and storing the data in Postgres. This data is then collected and shipped to Snowflake via Airbyte and Prefect.

Postgres was chosen as the desired technology set as it gives clear seperation of responsibility between DevOps and Data Management while providing strong deduplication of records from unreliable sources.

 ### How to execute the Tests?
 
    Events Tests are there in the path `snowstrom/tests`

    Tests can be executed using below command:
    `pytest ./tests/test_events.py --days 30 --events 10`

    Here `days` is the no.of days you need to retain the events and `events` is the total no.of test events that need to be created.


