from abc import ABC, abstractmethod
from common import persistence

class energy_consumer(ABC):
    @abstractmethod
    def __init__(self, db:persistence):
        pass

    @abstractmethod
    def initialize(self, **kwargs):
        pass


    @abstractmethod
    def consumer_is_consuming(self):
        pass
        
    @abstractmethod
    def stop_consuming(self):
        pass

    @abstractmethod
    def start_consuming(self):
        pass

    @property 
    def name(self):
        pass

    @property
    def current_consumption_current(self):
        pass
    @property
    def current_consumption_power(self):
        pass

    @property
    def max_consumption(self):
        pass
    @max_consumption.setter
    def max_consumption(self,value):
        pass


    @property
    def charge_until(self):
        pass
    @charge_until.setter
    def charge_until(self,value):
        pass

    @property
    def isConsuming(self):
        pass
    
    @property
    def can_consume_this_surplus(self):
        pass

    @property
    def can_start_consuming(self):
        pass

    @property
    def consumption_amps_now(self):
        pass
    
    @property
    def consumption_power_now(self):
        pass

    @property
    def balance_activated(self):
        pass
    @balance_activated.setter
    def balance_activated(self,value):
        pass
