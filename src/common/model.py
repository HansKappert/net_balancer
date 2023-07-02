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
        self._meter_reading_delivered_by_client_low    = 0
        self._meter_reading_delivered_by_client_normal = 0
        self._meter_reading_delivered_to_client_low    = 0
        self._meter_reading_delivered_to_client_normal = 0
        
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
        # the list _past_surplusses contains negative values
        last_n_surplusses = self._past_surplusses[-periods:]

        usable_surplusses = []
        if len(last_n_surplusses) == 0:
            return None
        mn= min(last_n_surplusses)
        for i in last_n_surplusses:
            if i < -800 and i<0 and mn > i*4: # dit doen we om de spikes er uit te halen.
                continue
            usable_surplusses.append(i) 
        
        if len(usable_surplusses) == 0 and len(last_n_surplusses) == periods:  
            # This can happen if for instance the car is charging at full speed.
            # All values in last_n_surplusses are below -800
            # In that case, use the average of the subset.
            for i in last_n_surplusses:
                usable_surplusses.append(i) 

        if len(usable_surplusses) < 3:
            self.logger.debug("Not enough usable data in {}. Usable elements are {}".format(last_n_surplusses,usable_surplusses))
            return None
        
        av = sum(usable_surplusses)/len(usable_surplusses)
        self.logger.debug(f"Average surplus: {av}")
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
    def meter_reading_delivered_by_client_low(self):
        self._meter_reading_delivered_by_client_low = self.persistence.get_meter_reading_delivered_by_client_low()
        return self._meter_reading_delivered_by_client_low
    @meter_reading_delivered_by_client_low.setter
    def meter_reading_delivered_by_client_low(self, value):
        self._meter_reading_delivered_by_client_normal = value
        self.persistence.set_meter_reading_delivered_by_client_low(value)

    @property
    def meter_reading_delivered_by_client_normal(self):
        self._meter_reading_delivered_by_client_normal = self.persistence.get_meter_reading_delivered_by_client_normal()
        return self._meter_reading_delivered_by_client_normal
    @meter_reading_delivered_by_client_normal.setter
    def meter_reading_delivered_by_client_normal(self, value):
        self._meter_reading_delivered_by_client_normal = value
        self.persistence.set_meter_reading_delivered_by_client_normal(value)

    @property
    def meter_reading_delivered_to_client_low(self):
        self._meter_reading_delivered_to_client_low = self.persistence.get_meter_reading_delivered_to_client_low()
        return self._meter_reading_delivered_to_client_low
    @meter_reading_delivered_to_client_low.setter
    def meter_reading_delivered_to_client_low(self, value):
        self._meter_reading_delivered_to_client_normal = value
        self.persistence.set_meter_reading_delivered_to_client_low(value)

    @property
    def meter_reading_delivered_to_client_normal(self):
        self._meter_reading_delivered_to_client_normal = self.persistence.get_meter_reading_delivered_to_client_normal()
        return self._meter_reading_delivered_to_client_normal
    @meter_reading_delivered_to_client_normal.setter
    def meter_reading_delivered_to_client_normal(self, value):
        self._meter_reading_delivered_to_client_normal = value
        self.persistence.set_meter_reading_delivered_to_client_normal(value)


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
        return current_price, round(total/24,2)    
    


    @property
    def mediation_service_status(self):
        return self.persistence.get_mediation_service_status()

    @mediation_service_status.setter
    def mediation_service_status(self,value):
        self.persistence.set_mediation_service_status(value)

    