import logging
from datetime                        import datetime,timedelta
from common.persistence import persistence
from service.abc_energy_consumer import energy_consumer
from common.database_logging_handler import database_logging_handler

class model:
    def __init__(self, db:persistence) -> None:
        self._persistence = db
        self._surplus = 0 # the last calculated value.
        self._balance = 0
        self._log_retention = 0
        # last readings
        self._current_consumption = 0
        self._current_production = 0
        self._current_gas_reading = 0
        self._past_surplusses = []
        self._consumers = []
        self.logger = logging.getLogger(__name__)

        
        log_handler = logging.StreamHandler()
        log_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(log_handler)
        
        log_handler = database_logging_handler(self.persistence)
        log_handler.setLevel(logging.INFO)
        self.logger.addHandler(log_handler)
    
    def get_consumer(self, name:str):
        for c in self._consumers:
            if c.name == name:
                return c

    @property
    def persistence(self):
        return self._persistence

    @property
    def surplus(self):
        self._surplus = self.persistence.get_surplus()
        return self._surplus
    @surplus.setter
    def surplus(self,value):
        self._surplus = value
        self.persistence.set_surplus(value)
        self._past_surplusses.append(value)
        if len(self._past_surplusses) > 50:
            self._past_surplusses = self._past_surplusses[1:]

    def reset_average_surplus(self):
        self._past_surplusses = []
    
    def average_surplus(self, periods):
        """
        returns the average surplus of the given period
        we could have also used numpy's average function, but I had difficulties installing numpy on an OrangePi
        """
        ll = ""
        subset = self._past_surplusses[-periods:]

        b = []
        if len(subset) == 0:
            return None
        mn= min(subset)
        for i in subset:
            if i < -1500 and i<0 and mn > i*4:
                continue
            b.append(i) 
        
        if len(b) < 3:
            self.logger.info("Te weinig bruikbare surplusdata elementen uit {}: {}".format(subset,b))
            return None
        av = sum(b)/len(b)

        return av
        
    # @property
    # def balance(self):
    #     self._balance = self.persistence.get_balance()
    #     return self._balance
    # @balance.setter
    # def balance(self,value):
    #     self._balance = value
    #     self.persistence.set_balance(value)

    @property
    def current_consumption(self):
        self._current_consumption = self.persistence.get_current_consumption()
        return self._current_consumption
    @current_consumption.setter
    def current_consumption(self,value):
        self._current_consumption = value
        self.surplus = self._current_production - self._current_consumption
        self.persistence.set_current_consumption(value)

    @property
    def current_production(self):
        self._current_production = self.persistence.get_current_production()
        return self._current_production
    @current_production.setter
    def current_production(self,value):
        self._current_production = value
        # We wait until the current consumption is set.
        # self.surplus = self._current_production - self._current_consumption
        self.persistence.set_current_production(value)


    @property
    def current_gas_reading(self):
        self._current_gas_reading = self.persistence.get_current_gas_reading()
        return self._current_gas_reading
    @current_gas_reading.setter
    def current_gas_reading(self,value):
        self._current_gas_reading = value
        self.persistence.set_current_gas_reading(value)


    @property
    def log_retention(self):
        self._log_retention = self.persistence.get_log_retention()
        return self._log_retention
    @log_retention.setter
    def log_retention(self,value):
        self._log_retention = value
        self.persistence.set_log_retention(value)


    @property
    def stats_retention(self):
        self._stats_retention = self.persistence.get_stats_retention()
        return self._stats_retention
    @stats_retention.setter
    def stats_retention(self,value):
        self._stats_retention = value
        self.persistence.set_stats_retention(value)


    def add_consumer(self, consumer : energy_consumer):
        self._consumers.append(consumer)
    
    @property
    def consumers(self):
        return self._consumers

    def get_current_and_average_price(self):
        total = 0
        current_price = 0
        datum = datetime.strptime(datetime.today().strftime("%Y-%m-%d"),"%Y-%m-%d")
        prices = self.persistence.get_day_prices(datum)
        for row in prices:
            dt = datetime.fromtimestamp(int(row[0]))
            hour = dt.hour   
            total += row[1]
            if hour == datetime.now().hour:
                current_price = row[1]
        return current_price, total/24    