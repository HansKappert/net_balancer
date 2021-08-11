from abc import ABC, abstractmethod

class energy_consumer(ABC):
    @abstractmethod
    def consumer_is_consuming(self):
        pass
    
    @abstractmethod
    def stop_charging(self):
        pass

    @abstractmethod
    def start_charging(self):
        pass