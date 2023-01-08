import requests
import urllib.parse
import json
import logging
import time
import pytz
from datetime                        import date, datetime, timedelta
from common.persistence              import persistence
from common.database_logging_handler import database_logging_handler

class prices_writer:
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
        base_url   = "https://api.energyzero.nl/v1/energyprices"
        url_params = "?fromDate={}&tillDate={}&interval=4&usageType=1&inclBtw=true"
        CET = pytz.timezone('CET')

        while True:
            today = datetime(date.today().year,date.today().month, date.today().day,0,0,0)
            for d in range(-10,2):
                target_date = today + timedelta(days=d)
                day_prices = self.persistence.get_day_prices(target_date)
                if len(day_prices) == 0:
                    self.logger.info(f"Fetching prices for {target_date}")
                    date_end   = target_date + timedelta(hours=23)
                    url        = base_url + url_params.format(urllib.parse.quote(target_date.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")), 
                                                              urllib.parse.quote(   date_end.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")))
                    response = requests.get(url)
                    if response.status_code != 200:
                        self.logger.print("HTTP status code: {} {}".format(response.status_code, response.reason) )
                    else: 
                        json_response = json.loads(response.text)
                        for idx, p in enumerate(json_response["Prices"]):
                            dt_str = p["readingDate"].replace("Z"," +0000")
                            dt = datetime.strptime(dt_str,'%Y-%m-%dT%H:%M:%S %z')
                            cet_dt = dt + timedelta(seconds=CET._utcoffset.seconds)
                            price = float(p['price'])
                            self.logger.info(f"Got new price for {cet_dt}: {price}")
                            self.persistence.write_prices(cet_dt, price)
                    time.sleep(1)

            # at 15u prices for the next day are available. So we'll collect them at 15:05
            fifteen_hour_five = today + timedelta(hours=15) + timedelta(minutes=5)
            timedelta_until_next_run = fifteen_hour_five - datetime.now() 
            seconds_until_next_run = timedelta_until_next_run.seconds
            self.logger.info(f"Waiting {seconds_until_next_run} seconds to get new price information")
            time.sleep(seconds_until_next_run)
