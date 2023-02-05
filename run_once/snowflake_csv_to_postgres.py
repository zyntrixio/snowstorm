"""
This did require running `dos2unix` and removing the header row before running.
Snowflake/Tableau use UTF-16 for some reason unknown to man-nor-beast
"""

import csv
import json
import sys

from sqlalchemy.orm import Session

from snowstorm.database import Events, engine

event_data = []

with open(sys.argv[1], "r") as f:
    data = csv.reader(f)
    next(data, None)
    for row in data:
        event_data.append(row)


with Session(engine) as session:
    event_count = len(event_data)
    for iteration, element in enumerate(event_data, 1):
        if iteration % 100 == 0 or iteration == event_count:
            print(f"Inserting Record {iteration} of {event_count}")
        insert = Events(
            id=int(element[0]),
            json=json.loads(element[1]),
            event_type=element[2],
            event_date_time=element[3],
        )
        session.merge(insert)
    session.commit()
