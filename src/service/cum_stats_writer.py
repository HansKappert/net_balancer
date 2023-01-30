import requests
import urllib.parse
import json
import logging
import time
import pytz
from datetime                        import date, datetime, timedelta
from common.database_logging_handler import database_logging_handler

class cum_stats_writer:
    def __init__(self, database) -> None:
        self.persistence = database
        self.logger = logging.getLogger(__name__)
        log_handler = logging.StreamHandler()
        log_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(log_handler)
        
        log_handler = database_logging_handler(self.persistence)
        log_handler.setLevel(logging.INFO)
        self.logger.addHandler(log_handler)

        pass

    def start(self):
        while True:
            for last_days in range(0,1):
                target_date = datetime(date.today().year,date.today().month, date.today().day,0,0,0) + timedelta(days=last_days)
                for hour in range(0,24):
                    target_date_hour = target_date + timedelta(hours=hour)
                    if target_date_hour < datetime.now() - timedelta(hours=1):
                        existing_cum_stats = self.persistence.get_cum_stats_for_date_hour(target_date_hour)
                        if len(existing_cum_stats) == 0:
                            self.persistence.accumulate_date_hour(target_date_hour)

            next_time = datetime(date.today().year,date.today().month, date.today().day,datetime.now().hour,0,0) + timedelta(hours=1)
            timedelta_until_midnight = next_time - datetime.now()
            seconds_until_next_time = timedelta_until_midnight.seconds
            self.logger.info(f"Waiting {seconds_until_next_time} seconds to accumulate next hour's stats")
            time.sleep(seconds_until_next_time + 5) # take some extra seconds to make way for price_writer.py 
