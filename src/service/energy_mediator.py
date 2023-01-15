import logging
import threading
import time
import service.energy_producer
import logging
from service.abc_energy_consumer import energy_consumer
from common.model import model
from common.persistence import persistence
from common.database_logging_handler import database_logging_handler

class mediator:
    def __init__(self, data_model) -> None:
        self.data_model = data_model
        self.mediation_delay = 10
        self.logger = logging.getLogger(__name__)
        
        log_handler = logging.StreamHandler()
        log_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(log_handler)
        
        log_handler = database_logging_handler(data_model.persistence)
        log_handler.setLevel(logging.INFO)
        self.logger.addHandler(log_handler)

        pass



    def __mediate_once(self):
        """
        This function is called on a frequent base by the mediate method.
        It's task is to find a consumer that is willing and able to consume some 
        surplus (can be negative) power.
        Every consumer has it's own characteristics for this. A laundry machine
        cannot deal with some negative suplus power, expecially after when it has 
        started. But an electric vehicle that is charging might be able to deal with 
        a bit less power.
        """
        av_surplus = self.data_model.average_surplus(6)
        for consumer in self.data_model.consumers:
            if consumer.balance_activated:
                current, average = self.data_model.get_current_and_average_price()
                price_percentage = consumer.price_percentage
                if current < average * (price_percentage/100):
                    self.logger.info(f"Price this hour ({current}) is below 50% of today's average ({average}), so consume at maximum")
                    max_consumption_power = consumer.max_consumption_power
                    if consumer.can_consume_this_surplus(av_surplus):
                        consumer.start_consuming(max_consumption_power)
                else:
                    self.logger.info(f"Price this hour ({current}) is above 50% of today's average ({average}), so balance ")
                    if av_surplus: # if there is some plus or minus surplus
                        # potantial improvement is to lower the av_surplus with the amount given to the consumer, and try to give the remainder to other consumers
                        # self.logger.info("Average surplus: " + str(av_surplus))
                        if consumer.can_consume_this_surplus(av_surplus):
                            if consumer.start_consuming(av_surplus): # returns true if something has changed in energy consumption
                                self.data_model.reset_average_surplus()

            

    def mediate(self, producer : service.energy_producer):
        """
        Main function of this class: it starts a thread to read dta from energy producers,
        and it mediates every 10 seconds the surplus power. 
        """
        th = threading.Thread(target=producer.start_reading, daemon=True)
        th.start()

        while True:
            self.__mediate_once()
            time.sleep(self.mediation_delay)
