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
        dt = datetime.now()
        unix_ts = time.mktime(dt.timetuple())
        self.db.write_statistics(unix_ts,self.data_model.current_production, self.data_model.current_consumption, self.data_model.get_consumer("Tesla").consumption_power_now)

    def start(self):
        self.state = "running"
        while self.state == "running":
            self.write_stats()
            time.sleep(10)

    def stop(self):
        self.state = "stopped"

