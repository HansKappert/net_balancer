from abc import ABC, abstractmethod
from common import persistence

class energy_consumer(ABC):
    @abstractmethod
    def __init__(self, db:persistence):
        pass

    @abstractmethod
    def initialize(self, **kwargs):
        pass


    # @abstractmethod
    # def consumer_is_consuming(self):
    #     pass
        
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
    def status(self):
        pass


    @property
    def isConsuming(self):
        """
        This function should report back to the caller if the 
        consumer is currently consuming any power
        """
        pass
    
    @property
    def can_consume_this_surplus(self):
        """
        This function should report back to the caller if the 
        consumer is able and willing to consume the given amount
        of surplus power
        """
        pass

    @property
    def _can_start_consuming(self):
        """
        This function should report back to the caller if the 
        consumer is able to start consuming at all. The class 
        can use the method itself, but it is also exposed externally
        for possible later use
        """
        pass

    @property
    def consumption_amps_now(self):
        """
        This function should report back to the caller how much current it is currently consuming
        """
        pass
    
    @property
    def consumption_power_now(self):
        """
        This function should report back to the caller how much power it is currently consuming
        """
        pass

    @property
    def balance_activated(self):
        """
        This property tells whether or not the consumer wants to be part of balancing
        """
        pass
    @balance_activated.setter
    def balance_activated(self,value):
        pass

    @property
    def price_percentage(self):
        """
        This function should report back to the caller above what percentage of the day's average price, the energy consumer would llike to receive maximum power
        """
        pass
    @price_percentage.setter
    def price_percentage(self,value):
        pass
