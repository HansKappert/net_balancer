from abc import ABC, abstractmethod

class energy_consumer(ABC):
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
    def consumption(self):
        pass
    @consumption.setter
    def consumption(self,value):
        pass

    @property
    def isConsuming(self):
        pass
    