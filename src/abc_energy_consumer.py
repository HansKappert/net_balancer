from abc import ABC, abstractmethod
from persistence import persistence

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

    def set_home_location(self):
        pass
    
    @property
    def consumption(self):
        pass
    @consumption.setter
    def consumption(self,value):
        pass

    @property
    def start_above(self):
        pass
    @consumption.setter
    def consumption(self,value):
        pass

    @property
    def charge_until(self):
        pass
    @consumption.setter
    def consumption(self,value):
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
    def override_activated(self):
        pass