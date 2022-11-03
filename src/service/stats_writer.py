from datetime import datetime
import time
import os

from common.model       import model
from common.persistence import persistence
from common.P1datagram  import P1datagram

class stats_writer:

    def __init__(self, data_model : model, db : persistence) -> None:
        self.data_model = data_model
        self.db = db
        self.state = "stopped"        

    def write_stats(self):
        when = datetime.now()
        current_price_kwh = self.db.get_price_at_datetime(when)
        current_price_kwm = current_price_kwh / 60
        current_price_kw10s = current_price_kwm / 6
        current_price_w10s  = current_price_kw10s / 1000
        consumption = self.data_model.current_consumption
        tesla_consumption = self.data_model.get_consumer("Tesla").consumption_power_now
        production  = self.data_model.current_production
        cost        = consumption * current_price_w10s
        profit      = production  * current_price_w10s
        tesla_cost  = tesla_consumption * current_price_w10s
        self.db.write_statistics(
                                when,
                                production,
                                 -1 * consumption,
                                tesla_consumption,
                                current_price_kwh,
                                current_price_kwh,
                                cost,
                                profit,
                                tesla_cost
                                )

    def start(self):
        self.state = "running"
        while self.state == "running":
            self.write_stats()
            time.sleep(10)

    def stop(self):
        self.state = "stopped"

