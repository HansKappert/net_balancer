import logging
from abc_energy_consumer import energy_consumer
from persistence import persistence


class fake_energy_consumer(energy_consumer):
    def __init__(self, db:persistence) :
        self.is_consuming = False
        self._consumption = 2000
        self._name = "Testconsumer"

    def initialize(self, **kwargs):
        pass

    def consumer_is_consuming(self):
        return self.is_consuming
    
    def stop_consuming(self):
        self.is_consuming = False

    def start_consuming(self):
        self.is_consuming = True
    
    @property
    def consumption(self):
        return self._consumption
    @consumption.setter
    def consumption(self,value):
        self._consumption = value

    @property
    def isConsuming(self):
        return True
    