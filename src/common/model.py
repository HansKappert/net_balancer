import numpy as np
from common.persistence import persistence
from service.abc_energy_consumer import energy_consumer
class model:
    def __init__(self, db:persistence) -> None:
        self.persistence = db
        self._surplus = 0 # the last calculated value.
        self._balance = 0
        self._log_retention = 0
        # last readings
        self._current_consumption = 0
        self._current_production = 0
        self._past_surplusses = np.array([])

        self._consumers = []
        
    def get_consumer(self, name:str):
        for c in self._consumers:
            if c.name == name:
                return c

    @property
    def surplus(self):
        self._surplus = self.persistence.get_surplus()
        return self._surplus
    @surplus.setter
    def surplus(self,value):
        self._surplus = value
        self.persistence.set_surplus(value)
        self._past_surplusses = np.append(self._past_surplusses,value)
        if len(self._past_surplusses) > 50:
            self._past_surplusses[1:]

    def average_surplus(self, periods):
        """
        returns the average surplus of the given period
        """
        return np.average(self._past_surplusses[-periods:])
        
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
        self.surplus = self._current_production - self._current_consumption
        self.persistence.set_current_production(value)



    @property
    def log_retention(self):
        self._log_retention = self.persistence.get_log_retention()
        return self._log_retention
    @log_retention.setter
    def log_retention(self,value):
        self._log_retention = value
        self.persistence.set_log_retention(value)


    def add_consumer(self, consumer : energy_consumer):
        self._consumers.append(consumer)
    
    @property
    def consumers(self):
        return self._consumers
