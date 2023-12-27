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



    def mediate_once(self):
        """
        This function is called on a frequent base by the mediate method.
        It's task is to find a consumer that is willing and able to consume some 
        surplus (can be negative) power.
        Every consumer has it's own characteristics for this. A laundry machine
        cannot deal with some negative suplus power, expecially after when it has 
        started. But an electric vehicle that is charging might be able to deal with 
        a bit less power.
        """
        self.data_model.mediation_service_status = ""
        average_surplus = self.data_model.average_surplus(6)
        # wait until the average surplus is calculated
        if not average_surplus:
            return
        found_active_consumer = False
        has_taken_surplus = False
        for consumer in self.data_model.consumers:
            self.logger.debug(f"Consumer {consumer.name} is {'active' if consumer.balance_activated else 'inactive'}.")
            if consumer.balance_activated:
                found_active_consumer = True
                current_hour_price, average_price = self.data_model.get_current_and_average_price()
                has_taken_surplus = consumer.balance(current_hour_price, average_price, average_surplus)
            # At this point there might be a consumer that has taken some (or all) of the surplus power.
            # If any was taken, we can leave this loop, and wait for the next mediation call, 
            # at which point there will be updated surpluss data
            self.logger.debug(f"Consumer {consumer.name} has taken surplus: {has_taken_surplus}.")
            if has_taken_surplus:
                self.logger.debug(f"Resetting average surplus.")
                self.data_model.reset_average_surplus()
                break
            
            if not found_active_consumer:
                self.data_model.mediation_service_status = "Alle consumers staan uit mbt balanceren."

            

    def mediate(self, producer : service.energy_producer):
        """
        Main function of this class: it starts a thread to read dta from energy producers,
        and it mediates every 10 seconds the surplus power. 
        """
        th = threading.Thread(target=producer.start_reading, daemon=True)
        th.start()

        while True:
            self.mediate_once()
            time.sleep(self.mediation_delay)
