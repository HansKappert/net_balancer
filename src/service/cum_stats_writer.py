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
            for last_days in range(-10,1):
                today = datetime(date.today().year,date.today().month, date.today().day,0,0,0) + timedelta(days=last_days)
                yesterday = today - timedelta(days=1)
                existing_cum_stats = self.persistence.get_cum_stats_for_date_hour(yesterday)
                if len(existing_cum_stats) == 0:
                    for hour in range(0,24):
                        target_hour = yesterday + timedelta(hours=hour)
                        self.persistence.accumulate_date_hour(target_hour)

            midnight = today + timedelta(days=1)
            timedelta_until_midnight = midnight - datetime.now()
            seconds_until_midnight = timedelta_until_midnight.seconds
            self.logger.info(f"Waiting {seconds_until_midnight} seconds. After midnight we'll accumulate today's stats")
            time.sleep(seconds_until_midnight + 6) # take some extra seconds to make way for price_writer.py 
